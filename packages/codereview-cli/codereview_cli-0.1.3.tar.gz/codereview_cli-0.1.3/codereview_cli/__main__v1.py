import os, re, json
from pathlib import Path
from typing import List, Dict, Iterable, Generator, Callable, Optional

import click
import tiktoken
from openai import OpenAI

# ---------- Small, focused prompt ----------
REVIEW_SYSTEM = """You are a senior engineer doing a high-level code review.
Return STRICT **JSON ONLY** (no prose, no markdown), exactly:
{
  "summary": "one paragraph",
  "findings": [
    {"file": "relative/path", "severity": "HIGH|MEDIUM|LOW|NIT",
     "title": "short", "details": "what/why/how", "lines": [start,end]}
  ],
  "suggestions": ["concise bullet"]
}
Focus on correctness, security, performance, readability, maintainability, and production risks.
"""

def build_user_prompt(chunk: str) -> str:
    return (
        "Files are delimited by headers like:\n"
        "### File: relative/path\n\n"
        "Review ONLY the code in this message.\n\n" + chunk
    )

# ---------- Walk (prune heavy dirs) ----------
DEFAULT_EXCLUDE = {".git", ".hg", ".svn", "node_modules", "dist", "build", "out", ".venv", "venv", "__pycache__"}

def iter_code_files(root: Path, ext: str, exclude_dirs: Iterable[str]) -> List[str]:
    files: List[str] = []
    exclude = set(exclude_dirs) | DEFAULT_EXCLUDE
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for fn in filenames:
            if fn.endswith(ext):
                files.append(str(Path(dirpath) / fn))
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
                                ct = len(encode(cont))
                                parts.append(cont); tok_count += ct
                            parts.append(piece); tok_count += pt
                            i += len(piece)
                        continue

                    if tok_count + lt + prompt_overhead > max_tokens_per_chunk:
                        yield from flush()
                        cont = f"(…continued {Path(rel).name} …)\n"
                        ct = len(encode(cont))
                        parts.append(cont); tok_count += ct

                    parts.append(line); tok_count += lt

            sep = "\n"
            st = len(encode(sep))
            if tok_count + st + prompt_overhead > max_tokens_per_chunk:
                yield from flush()
            parts.append(sep); tok_count += st

        except Exception as e:
            warn = f"\n### Skipped: {rel} (error: {e})\n\n"
            wt = len(encode(warn))
            if tok_count + wt + prompt_overhead > max_tokens_per_chunk:
                yield from flush()
            parts.append(warn); tok_count += wt

    yield from flush()

# ---------- LLM call ----------
def call_openai(client, model, system, user_prompt) -> str:
    resp = client.chat.completions.create(
        model=model,
        temperature=0.0,
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
            try: return json.loads(m.group(0))
            except Exception: return None
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

    # Simple de-dup per file by (title, details)
    for fp, lst in list(agg["findings_by_file"].items()):
        seen = {}
        for it in lst:
            key = (it["title"].strip(), it["details"].strip())
            if key not in seen: seen[key] = it
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

# ---------- CLI ----------
@click.command()
@click.option("--ext", default=".py", show_default=True, help="File extension to analyze")
@click.option("--model", default="gpt-4o", show_default=True, help="OpenAI model")
@click.option("--max-tokens-per-chunk", default=120000, type=int, show_default=True, help="Token cap per chunk (incl. overhead)")
@click.option("--prompt-overhead", default=1200, type=int, show_default=True, help="Estimated tokens reserved for system/instructions")
@click.option("--exclude-dirs", default="", show_default=False, help="Comma-separated extra dirs to skip")
@click.option("--report", default="code_review.md", show_default=True, help="Output Markdown path")
def main(ext, model, max_tokens_per_chunk, prompt_overhead, exclude_dirs, report):
    """Scan, chunk, review with OpenAI, and write a Markdown report."""
    if not os.getenv("OPENAI_API_KEY"):
        raise click.ClickException("Please set OPENAI_API_KEY in your environment.")

    extra_exclude = {d.strip() for d in exclude_dirs.split(",") if d.strip()}
    files = iter_code_files(Path("."), ext, extra_exclude)
    if not files:
        click.echo(f"No files with extension '{ext}' found.")
        return

    # tokenizer: prefer model-specific; fall back to cl100k
    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")
    encode = enc.encode

    chunks = list(chunk_stream_from_files(files, encode, max_tokens_per_chunk, prompt_overhead))
    if not chunks:
        click.echo("Nothing to analyze after chunking.")
        return

    client = OpenAI()
    outputs: List[str] = []
    for i, ch in enumerate(chunks, start=1):
        click.echo(f"Reviewing chunk {i}/{len(chunks)} …")
        prompt = build_user_prompt(ch)
        try:
            outputs.append(call_openai(client, model, REVIEW_SYSTEM, prompt))
        except Exception as e:
            # keep going; mark as unparsed later
            outputs.append(json.dumps({"summary":"", "findings":[], "suggestions":[], "error": str(e)}))

    agg = aggregate(outputs, chunks)
    write_markdown(agg, report)
    click.echo(f"✓ Review written to {report}")

if __name__ == "__main__":
    main()