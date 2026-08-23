#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6"]
# ///
"""Build the knowledge packs that agents upload into Agent Builder.

Agent Builder grounds an agent in uploaded files, and accepts .doc .docx .ppt .pptx .xls .xlsx
.txt and .pdf. It does not accept Markdown, MDX or JSON. So the source documents are fetched and
converted to plain text here, and the result is committed: a render needs no network, and the exact
bytes an agent is grounded in are reviewable in a diff.

This matters more than it sounds. Scoped web search reads only what Bing indexes, so it cannot see
private documentation and cannot be relied on for anything behind a login. Uploaded knowledge is the
one grounding route that needs no connector, no admin, and no public indexing.

Usage:
    uv run tools/fetch_knowledge.py            # refresh every source
    uv run tools/fetch_knowledge.py --check    # fail if the committed copies are stale

Exit codes: 0 clean, 1 stale or a fetch failed, 2 usage.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = ROOT / "knowledge"
SOURCES = KNOWLEDGE / "sources.yaml"

# Agent Builder allows 20 uploaded files, and each embedded .txt may be up to 512 MB. The practical
# limit is comprehension, not storage: Microsoft's own guidance is to keep uploaded documents
# concise, so a source ballooning past this is worth looking at rather than shipping blindly.
WARN_BYTES = 400_000


def strip_mdx(text: str) -> str:
    """Reduce MDX to the prose and code a language model can use.

    Frontmatter, import statements and JSX component tags carry no meaning once the page is not
    being rendered, and they cost tokens. Fenced code blocks are kept verbatim: for a standards
    document they are the most valuable part.
    """
    text = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    text = re.sub(r"^import\s+.*?from\s+['\"].*?['\"]\s*$", "", text, flags=re.M)
    text = re.sub(r"^export\s+const\s+.*$", "", text, flags=re.M)

    # Protect fenced code before stripping tags, so JSX-looking generics inside code survive.
    blocks: list[str] = []

    def stash(match: re.Match[str]) -> str:
        blocks.append(match.group(0))
        return f"\x00BLOCK{len(blocks) - 1}\x00"

    text = re.sub(r"```.*?```", stash, text, flags=re.S)
    text = re.sub(r"<([A-Z][\w.]*)\b[^>]*/>", "", text)
    text = re.sub(r"</?([A-Z][\w.]*)\b[^>]*>", "", text)
    text = re.sub(r"\{/\*.*?\*/\}", "", text, flags=re.S)
    for i, block in enumerate(blocks):
        text = text.replace(f"\x00BLOCK{i}\x00", block)

    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def render_json(text: str, title: str) -> str:
    """Pretty print a JSON schema so it reads as text rather than one enormous line."""
    try:
        return f"# {title}\n\n" + json.dumps(json.loads(text), indent=2) + "\n"
    except json.JSONDecodeError:
        return f"# {title}\n\n{text}\n"


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "copilot-agents-knowledge"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return response.read().decode("utf-8")


def build(source: dict) -> str:
    raw = fetch(source["url"])
    title = source["title"]
    is_json = source.get("format") == "json"
    body = render_json(raw, title) if is_json else f"# {title}\n\n" + strip_mdx(raw)
    return (
        f"Source: {source['url']}\n"
        f"Fetched by tools/fetch_knowledge.py. Do not edit by hand.\n\n"
        f"{body}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the agent knowledge packs.")
    parser.add_argument("--check", action="store_true", help="fail if the committed copies are stale")
    args = parser.parse_args()

    sources = (yaml.safe_load(SOURCES.read_text(encoding="utf-8")) or {}).get("sources", [])
    if not sources:
        print(f"no sources declared in {SOURCES}", file=sys.stderr)
        return 2

    stale: list[str] = []
    for source in sources:
        target = KNOWLEDGE / source["name"]
        try:
            content = build(source)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            print(f"ERROR fetching {source['url']}: {exc}", file=sys.stderr)
            return 1

        size = len(content.encode("utf-8"))
        if args.check:
            current = target.read_text(encoding="utf-8") if target.is_file() else ""
            if current != content:
                stale.append(source["name"])
            continue

        target.write_text(content, encoding="utf-8")
        flag = "  (large, consider trimming)" if size > WARN_BYTES else ""
        print(f"  {source['name']}: {size:,} bytes{flag}")

    if args.check:
        if stale:
            print("\nERROR knowledge packs are stale. Run `just update-knowledge`:", file=sys.stderr)
            for name in stale:
                print(f"  knowledge/{name}", file=sys.stderr)
            return 1
        print("knowledge packs are current.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
