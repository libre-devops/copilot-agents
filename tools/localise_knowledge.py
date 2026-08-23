#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6"]
# ///
"""Rebrand the shipped standards into your own, for when you wrote them in the first place.

`rebrand` deliberately leaves knowledge/*.txt alone, because rewriting someone else's published
document would falsify it. That reasoning does not apply when the document is yours and you are
adopting it internally under a different name.

This takes the upstream packs, applies your profile's branding to the prose, and writes the result
into knowledge/local/, which is gitignored. The upstream copies stay untouched, so
`just update-knowledge` still works and you can re-run this after a refresh.

What it deliberately does NOT rewrite:

- `libre-devops/<module>/<provider>` Terraform registry sources. Those modules are really published
  at that address, and renaming them would send readers to a module that does not exist.
- The `Source:` provenance line, and any `libre-devops` GitHub path, for the same reason.

Usage:
    uv run tools/localise_knowledge.py                 # use profiles/default.yaml
    uv run tools/localise_knowledge.py --profile acme
    uv run tools/localise_knowledge.py --dry-run

Exit codes: 0 done, 1 nothing to do or a problem, 2 usage.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = ROOT / "knowledge"
LOCAL = KNOWLEDGE / "local"
PROFILES = ROOT / "profiles"

# Which agent each pack belongs to, so the overrides block can be printed ready to paste.
PACK_OWNERS = {
    "terraform-standards.txt": "terraform-author",
    "azure-naming-convention.txt": "terraform-author",
    "azure-logic-app-standards.txt": "logic-app-author",
}


def load_tokens(profile: str) -> dict[str, str]:
    path = PROFILES / f"{profile}.yaml"
    if not path.is_file():
        raise SystemExit(f"profile not found: profiles/{profile}.yaml")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    tokens = data.get("tokens", {})
    website = (data.get("publisher", {}) or {}).get("website_url", "")
    host = re.sub(r"^https?://", "", website).split("/")[0]
    return {
        "brand_name": tokens.get("brand_name", ""),
        "brand_short": tokens.get("brand_short", ""),
        "brand_infix": tokens.get("brand_infix", ""),
        "docs_host": host or tokens.get("docs_url", "").split("/")[0],
    }


def build_mapping(tokens: dict[str, str]) -> dict[str, str]:
    """Prose branding only.

    `libre-devops` is absent on purpose: it is the GitHub organisation and the Terraform registry
    namespace, and both are real addresses that must keep resolving. Note that neither
    "libre-devops" nor "libredevops" contains the substring "ldo", so replacing the infix cannot
    damage them.
    """
    mapping = {
        "libredevops.org": tokens["docs_host"],
        "Libre DevOps": tokens["brand_name"],
        "LibreDevOps": tokens["brand_name"].replace(" ", ""),
        "LDO": tokens["brand_short"],
        "ldo": tokens["brand_infix"],
    }
    return {k: v for k, v in mapping.items() if v and k != v}


def rewrite(text: str, mapping: dict[str, str]) -> tuple[str, int]:
    if not mapping:
        return text, 0
    pattern = re.compile("|".join(re.escape(k) for k in sorted(mapping, key=len, reverse=True)))
    count = 0

    def swap(match: re.Match[str]) -> str:
        nonlocal count
        count += 1
        return mapping[match.group(0)]

    return pattern.sub(swap, text), count


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebrand the shipped standards into knowledge/local/.")
    parser.add_argument("--profile", default="default", help="profile to take the branding from")
    parser.add_argument("--dry-run", action="store_true", help="report and stop")
    args = parser.parse_args()

    tokens = load_tokens(args.profile)
    mapping = build_mapping(tokens)
    if not mapping:
        print(f"profiles/{args.profile}.yaml carries no branding to apply.", file=sys.stderr)
        return 1

    print(f"\nLocalising the standards using profiles/{args.profile}.yaml\n")
    for key, value in sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True):
        print(f"  {key:<18} -> {value}")
    print("\n  Left alone: libre-devops/<module>/<provider> registry sources and the Source: lines,")
    print("  because those addresses really exist and must keep resolving.\n")

    written: dict[str, list[str]] = {}
    for name, owner in PACK_OWNERS.items():
        source = KNOWLEDGE / name
        if not source.is_file():
            print(f"  {name}: not present, skipping (run `just update-knowledge`)")
            continue
        updated, count = rewrite(source.read_text(encoding="utf-8"), mapping)
        target_name = f"{args.profile}-{name}" if args.profile != "default" else f"local-{name}"
        if not args.dry_run:
            LOCAL.mkdir(parents=True, exist_ok=True)
            (LOCAL / target_name).write_text(updated, encoding="utf-8")
        print(f"  {name}: {count} replacement(s) -> knowledge/local/{target_name}")
        written.setdefault(owner, []).append(f"local/{target_name}")

    if not written:
        print("\nNothing to localise.\n")
        return 1
    if args.dry_run:
        print("\nDry run, nothing written.\n")
        return 0

    print(f"\nAdd this to the bottom of profiles/{args.profile}.yaml:\n")
    print("agent_overrides:")
    for owner, files in written.items():
        print(f"  {owner}:")
        print("    knowledge_files:")
        for name in files:
            print(f"      - {name}")
    print("\nThen: uv run just render && uv run just lint\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
