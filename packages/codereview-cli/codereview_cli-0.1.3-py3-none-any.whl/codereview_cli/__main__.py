import os, re, json, asyncio, subprocess
from pathlib import Path
from typing import List, Dict, Iterable, Generator, Callable, Optional

import click
import tiktoken
from openai import OpenAI

# ---------- Optional .gitignore support ----------
try:
    from pathspec import PathSpec
except Exception:
    PathSpec = None

# ---------- Prompt ----------
REVIEW_SYSTEM = """You are a senior software engineer performing an in-depth code review.

Return STRICT JSON ONLY (no prose, no markdown), exactly:
{
  "summary": "brief paragraph summarizing the overall code quality, architecture, and potential risks",
  "findings": [
    {
      "file": "relative/path",
      "severity": "HIGH|MEDIUM|LOW|NIT",
      "title": "short and descriptive issue title",
      "details": "clear explanation of what the issue is, why it matters, and how it impacts correctness, performance, security, or maintainability",
      "lines": [start, end]
    }
  ],
  "suggestions": [
    "specific technical or design improvement — e.g. refactoring recommendation, applying a design pattern, using a more appropriate data structure, optimizing an algorithm, improving exception handling, or simplifying logic"
  ]
}

Guidelines for analysis:
- Focus on correctness, security, performance, scalability, readability, and maintainability.
- Identify code smells, anti-patterns, unhandled edge cases, race conditions, or hard-coded configurations.
- For suggestions:
  - Propose concrete refactoring ideas (e.g., extract method, dependency inversion, modularization).
  - Recommend design patterns when relevant (e.g., Strategy, Factory, Observer, Singleton, Command).
  - Suggest modern language features or standard library utilities that improve clarity or safety.
  - Recommend testability improvements (unit tests, mocking strategies).
  - Propose better error handling or logging practices.
  - Mention opportunities for code simplification or reducing cognitive complexity.
- Limit to the **top 10 most impactful findings per chunk**.
- Each detail or suggestion should be concise (<150 words) but technically actionable.
"""


def build_user_prompt(chunk: str) -> str:
    return (
        "Files are delimited by headers like:\n"
        "### File: relative/path\n\n"
        "Review ONLY the code in this message.\n\n" + chunk
    )

# ---------- Walk (prune heavy dirs + .gitignore) ----------
DEFAULT_EXCLUDE = {".git", ".hg", ".svn", "node_modules", "dist", "build", "out", ".venv", "venv", "__pycache__"}

def _load_gitignore(root: Path):
    if PathSpec is None:
        return None
    gi = root / ".gitignore"
    if gi.exists():
        try:
            return PathSpec.from_lines("gitwildmatch", gi.read_text().splitlines())
        except Exception:
            return None
    return None

def iter_code_files(root: Path, ext: str, exclude_dirs: Iterable[str]) -> List[str]:
    files: List[str] = []
    exclude = set(exclude_dirs) | DEFAULT_EXCLUDE
    spec = _load_gitignore(root)

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for fn in filenames:
            p = Path(dirpath) / fn
            rel = p.relative_to(root).as_posix()
            if spec and spec.match_file(rel):
                continue
            if fn.endswith(ext):
                files.append(str(p))
    return files

# ---------- Chunk stream (token-aware, splits long lines) ----------
FILE_HEADER = "### File: {rel}\n"

def chunk_stream_from_files(
    files: List[str],
    encode: Callable[[str], List[int]],
    max_tokens_per_chunk: int,
    prompt_overhead: int,
) -> Generator[str, None, None]:
    budget = max_tokens_per_chunk - prompt_overhead
    if budget <= 0:
        raise click.ClickException("max-tokens-per-chunk must be > prompt-overhead")

    parts: List[str] = []
    tok_count = 0

    def flush():
        nonlocal parts, tok_count
        if parts:
            yield "".join(parts)
            parts, tok_count = [], 0

    for path in files:
        rel = Path(path).resolve().relative_to(Path(".").resolve()).as_posix()
        header = FILE_HEADER.format(rel=rel)
        ht = len(encode(header))
        if tok_count + ht + prompt_overhead > max_tokens_per_chunk:
            yield from flush()
        parts.append(header); tok_count += ht

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    lt = len(encode(line))
                    if lt > budget:
                        # Hard-split very long/minified lines by chars until they fit.
                        i, step = 0, max(256, len(line)//8 or 256)
                        while i < len(line):
                            piece = line[i:i+step]
                            while len(encode(piece)) > budget and len(piece) > 32:
                                piece = piece[:len(piece)//2]
                            pt = len(encode(piece))
                            if tok_count + pt + prompt_overhead > max_tokens_per_chunk:
                                yield from flush()
                                cont = f"(…continued {Path(rel).name} …)\n"
                                parts.append(cont); tok_count += len(encode(cont))
                            parts.append(piece); tok_count += pt
                            i += len(piece)
                        continue

                    if tok_count + lt + prompt_overhead > max_tokens_per_chunk:
                        yield from flush()
                        cont = f"(…continued {Path(rel).name} …)\n"
                        parts.append(cont); tok_count += len(encode(cont))

                    parts.append(line); tok_count += lt

            sep = "\n"
            if tok_count + len(encode(sep)) + prompt_overhead > max_tokens_per_chunk:
                yield from flush()
            parts.append(sep); tok_count += len(encode(sep))

        except Exception as e:
            warn = f"\n### Skipped: {rel} (error: {e})\n\n"
            if tok_count + len(encode(warn)) + prompt_overhead > max_tokens_per_chunk:
                yield from flush()
            parts.append(warn); tok_count += len(encode(warn))

    yield from flush()

# ---------- LLM call ----------
def call_openai(client: OpenAI, model: str, system: str, user_prompt: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=0.0,
        max_tokens=1500,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content or ""

# ---------- Aggregation + report ----------
FILE_HEADER_RE = re.compile(r"^###\s*File:\s*(.+)$", re.MULTILINE)

def try_parse_json(s: str) -> Optional[dict]:
    try:
        return json.loads(s)
    except Exception:
        m = re.search(r"\{[\s\S]*\}$", s)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return None
        return None

def aggregate(outputs: List[str], chunks: List[str]) -> Dict:
    agg = {"summary_notes": [], "suggestions": [], "findings_by_file": {}, "unparsed": []}
    for i, (out, ch) in enumerate(zip(outputs, chunks), start=1):
        data = try_parse_json(out)
        if not data:
            agg["unparsed"].append({"chunk_index": i})
            continue
        if isinstance(data.get("summary"), str):
            agg["summary_notes"].append(data["summary"])
        if isinstance(data.get("suggestions"), list):
            agg["suggestions"].extend(map(str, data["suggestions"]))

        files_in_chunk = FILE_HEADER_RE.findall(ch)
        for f in data.get("findings", []):
            fp = (f.get("file") or "").strip() or (files_in_chunk[0] if files_in_chunk else "UNKNOWN")
            entry = {
                "severity": str(f.get("severity", "LOW")).upper(),
                "title": str(f.get("title", "Issue")),
                "details": str(f.get("details", "")),
                "lines": f.get("lines"),
            }
            agg["findings_by_file"].setdefault(fp, []).append(entry)

    # De-dup per file (title, details)
    for fp, lst in list(agg["findings_by_file"].items()):
        seen = {}
        for it in lst:
            key = (it["title"].strip(), it["details"].strip())
            if key not in seen:
                seen[key] = it
        agg["findings_by_file"][fp] = list(seen.values())
    return agg

def write_markdown(agg: Dict, out_path: str) -> None:
    sev_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2, "NIT": 3}
    lines: List[str] = ["# High-level Code Review", ""]
    if agg["summary_notes"]:
        lines.append("## Overall Summary")
        for s in agg["summary_notes"]: lines.append(f"- {s}")
        lines.append("")
    if agg["suggestions"]:
        lines.append("## Global Suggestions")
        for s in agg["suggestions"]: lines.append(f"- {s}")
        lines.append("")
    lines.append("## Findings by File")
    if not agg["findings_by_file"]:
        lines.append("_No issues reported._")
    else:
        for fp in sorted(agg["findings_by_file"].keys()):
            lines.append(f"### `{fp}`")
            items = sorted(
                agg["findings_by_file"][fp],
                key=lambda it: (sev_rank.get(it["severity"], 9), it["title"].lower()),
            )
            for it in items:
                loc = f' (lines {it["lines"][0]}–{it["lines"][1]})' if it.get("lines") and len(it["lines"]) == 2 else ""
                lines.append(f'- **{it["severity"]}** — **{it["title"]}**{loc}\n  - {it["details"]}')
            lines.append("")
    if agg.get("unparsed"):
        lines.append("## Chunks with Unparsed Output")
        for u in agg["unparsed"]:
            lines.append(f'- Chunk {u["chunk_index"]}: model did not return valid JSON.')
        lines.append("")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")

# ---------- Speed-ups: concurrent review + changed-files ----------
def git_changed_files(ext: str) -> List[str]:
    try:
        out = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], text=True).splitlines()
        return [p for p in out if p.endswith(ext)]
    except Exception:
        return []

async def _review_worker(idx: int, chunk: str, client: OpenAI, model: str, outputs: Dict[int, str], debug: bool):
    prompt = build_user_prompt(chunk)
    # run blocking SDK in a thread to keep asyncio responsive
    txt = await asyncio.to_thread(call_openai, client, model, REVIEW_SYSTEM, prompt)
    outputs[idx] = txt
    if debug:
        Path(f".codereview_debug_chunk_{idx}.json").write_text(txt, encoding="utf-8")

def review_chunks_concurrently(chunk_iter, *, client: OpenAI, model: str, concurrency: int, debug: bool) -> List[str]:
    outputs: Dict[int, str] = {}
    async def runner():
        sem = asyncio.Semaphore(concurrency)
        tasks = []
        for i, ch in enumerate(chunk_iter, start=1):
            click.echo(f"Queueing chunk {i} …")
            async def run_one(ii=i, cch=ch):
                async with sem:
                    await _review_worker(ii, cch, client, model, outputs, debug)
            tasks.append(asyncio.create_task(run_one()))
        await asyncio.gather(*tasks)
        return [outputs[i] for i in range(1, len(outputs) + 1)]
    return asyncio.run(runner())

# ---------- CLI ----------
@click.command()
@click.option("--ext", default=".py", show_default=True, help="File extension to analyze")
@click.option("--model", default="gpt-4o", show_default=True, help="OpenAI model")
@click.option("--max-tokens-per-chunk", default=60000, type=int, show_default=True, help="Token cap per chunk (incl. overhead)")
@click.option("--prompt-overhead", default=1200, type=int, show_default=True, help="Estimated tokens reserved for system/instructions")
@click.option("--exclude-dirs", default="", show_default=False, help="Comma-separated extra dirs to skip")
@click.option("--report", default="code_review.md", show_default=True, help="Output Markdown path")
@click.option("--concurrency", default=4, type=int, show_default=True, help="Parallel chunk reviews")
@click.option("--only-changed", is_flag=True, help="Review only files changed vs HEAD (git)")
@click.option("--debug", is_flag=True, help="Save raw model outputs to .codereview_debug_chunk_*.json")
def main(ext, model, max_tokens_per_chunk, prompt_overhead, exclude_dirs, report, concurrency, only_changed, debug):
    """Fast, scalable LLM code review."""
    if not os.getenv("OPENAI_API_KEY"):
        raise click.ClickException("Please set OPENAI_API_KEY in your environment.")

    root = Path(".")
    extra_exclude = {d.strip() for d in exclude_dirs.split(",") if d.strip()}
    files = iter_code_files(root, ext, extra_exclude)
    if only_changed:
        changed = set(git_changed_files(ext))
        files = [f for f in files if Path(f).as_posix() in changed]
    if not files:
        click.echo(f"No files to review for extension '{ext}'.")
        return

    # tokenizer
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    encode = enc.encode

    client = OpenAI()
    # STREAM chunks directly into the concurrent reviewer (no materializing the whole list)
    chunk_iter = chunk_stream_from_files(files, encode, max_tokens_per_chunk, prompt_overhead)
    outputs = review_chunks_concurrently(chunk_iter, client=client, model=model, concurrency=concurrency, debug=debug)

    # aggregate needs the original chunk texts; re-generate once (cheap vs extra memory)
    chunks_for_aggregation = list(chunk_stream_from_files(files, encode, max_tokens_per_chunk, prompt_overhead))
    agg = aggregate(outputs, chunks_for_aggregation)
    write_markdown(agg, report)
    click.echo(f"✓ Review written to {report}")

if __name__ == "__main__":
    main()
