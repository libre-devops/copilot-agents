#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Rebrand the whole repository for a fork, not just the agents it produces.

`new-profile` brands the agents. This brands the repository: the README, the docs, the licence, the
default profile, the agent READMEs, every reference to Libre DevOps in prose. It is for the moment
just after you fork, before anyone has built anything.

Do not run it on a checkout whose agents are already installed. It changes the default profile's
app id namespace, so every agent id changes, and it changes the agent names. Installed agents do not
follow: they would have to be rebuilt and reshared.

Replacements happen in a single regex pass, so a value you supply is never itself rewritten. That
matters more than it sounds: replacing "Libre DevOps" with "Waldo Corp" and then replacing "ldo"
would otherwise turn it into "Wacm Corp".

Usage:
    uv run tools/rebrand.py                 # ask, preview, confirm
    uv run tools/rebrand.py --dry-run       # show what would change and stop
    uv run tools/rebrand.py --force         # allow a dirty working tree

Exit codes: 0 done or declined, 1 refused, 2 usage.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Generated or fetched content. rendered/ is rebuilt at the end; knowledge/*.txt are other people's
# documents and rewriting their text would falsify them.
SKIP_DIRS = {".git", ".venv", "build", "dist", "node_modules", "__pycache__", "rendered"}
# This file must exclude itself: its mapping keys are the literal strings it searches for, so
# rewriting them would destroy the tool on first use.
SKIP_FILES = {"uv.lock", "rebrand.py"}
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".toml", ".py", ".json", ".txt", ".cfg", ".ini", ""}


def tracked_files(include_sources: bool) -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if set(rel.parts) & SKIP_DIRS or rel.name in SKIP_FILES:
            continue
        if rel.parts[0] == "knowledge" and rel.suffix == ".txt":
            continue
        if rel.as_posix() == "knowledge/sources.yaml" and not include_sources:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {"justfile", "LICENSE"}:
            continue
        files.append(path)
    return sorted(files)


def ask(prompt: str, default: str) -> str:
    try:
        answer = input(f"  {prompt}\n    [{default}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  cancelled")
        raise SystemExit(0) from None
    return answer or default


def confirm(prompt: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    try:
        answer = input(f"  {prompt} {suffix}: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print("\n  cancelled")
        raise SystemExit(0) from None
    if not answer:
        return default
    return answer.startswith("y")


def build_mapping(values: dict[str, str]) -> dict[str, str]:
    """Longest keys first, so the alternation prefers the most specific match."""
    mapping = {
        "libredevops.org": values["domain"],
        "libre-devops": values["slug"],
        "Libre DevOps": values["org"],
        "LibreDevOps": values["org"].replace(" ", ""),
        "libredevops": values["slug"].replace("-", ""),
        "LDO": values["short"],
        "ldo": values["infix"],
        "Craig Thacker": values["author"],
        "craigthackerx@gmail.com": values["email"],
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
    parser = argparse.ArgumentParser(description="Rebrand this repository for a fork.")
    parser.add_argument("--dry-run", action="store_true", help="show what would change and stop")
    parser.add_argument("--force", action="store_true", help="proceed even with a dirty working tree")
    args = parser.parse_args()

    print("\nRebrand this repository")
    print("=" * 23)
    print()
    print("  This rewrites the README, the docs, the licence, the default profile and every")
    print("  reference to Libre DevOps in prose. It is meant for the moment just after you fork.")
    print()
    print("  DO NOT run it if agents from this checkout are already installed. It issues a new")
    print("  app id namespace, so every agent id changes, and it changes the agent names.")
    print("  Installed agents do not follow: they would need rebuilding and resharing.")
    print()

    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    if dirty and not args.force:
        print("  Refusing: the working tree has uncommitted changes.")
        print("  Commit or stash first, so this rewrite is reviewable and `git checkout .` undoes it.")
        print("  Override with --force if you know what you are doing.")
        return 1

    if not args.dry_run and not confirm("Understood, continue?"):
        print("\n  Nothing changed.\n")
        return 0

    print()
    org = ask("Organisation name, replacing 'Libre DevOps'", "Acme Corp")
    slug_default = re.sub(r"[^a-z0-9]+", "-", org.lower()).strip("-")
    slug = ask("GitHub organisation, replacing 'libre-devops'", slug_default)
    domain = ask("Domain, replacing 'libredevops.org'", f"{slug.replace('-', '')}.example")
    short = ask("Short prefix for agent names, replacing 'LDO'", org.split()[0][:4].upper())
    infix = ask("Lower case product code, replacing 'ldo'", short.lower()[:3])
    author = ask("Copyright holder, replacing 'Craig Thacker'", org)
    email = ask("Contact email", f"hello@{domain}")

    include_sources = confirm(
        "\n  Repoint knowledge/sources.yaml at your own domain too?\n"
        "  Saying no keeps it fetching the Libre DevOps standards, which still work.\n"
        "  Saying yes gives you URLs that probably do not exist yet, so `just update-knowledge`\n"
        "  will fail until you fix them.\n  Repoint them?",
        default=False,
    )

    mapping = build_mapping(
        {
            "org": org, "slug": slug, "domain": domain, "short": short,
            "infix": infix, "author": author, "email": email,
        }
    )

    print("\n  Replacing:")
    for key, value in sorted(mapping.items(), key=lambda kv: len(kv[0]), reverse=True):
        print(f"    {key:<24} -> {value}")

    changes: list[tuple[Path, int, str]] = []
    for path in tracked_files(include_sources):
        try:
            original = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        updated, count = rewrite(original, mapping)
        if count:
            changes.append((path, count, updated))

    if not changes:
        print("\n  Nothing to change.\n")
        return 0

    total = sum(c for _, c, _ in changes)
    print(f"\n  {total} replacement(s) across {len(changes)} file(s):")
    for path, count, _ in changes:
        print(f"    {str(path.relative_to(ROOT)):<44} {count}")

    if args.dry_run:
        print("\n  Dry run, nothing written.\n")
        return 0

    if not confirm("\n  Write these changes?"):
        print("\n  Nothing changed.\n")
        return 0

    for path, _, updated in changes:
        path.write_text(updated, encoding="utf-8")

    # A fork must not claim the upstream app ids. New namespace, no pinned ids, so every agent id
    # derives fresh and cannot collide with an agent someone installed from upstream.
    profile = ROOT / "profiles" / "default.yaml"
    text = profile.read_text(encoding="utf-8")
    namespace = uuid.uuid5(uuid.NAMESPACE_DNS, f"{domain}/copilot-agents")
    text = re.sub(r"^app_id_namespace: .*$", f"app_id_namespace: {namespace}", text, flags=re.M)
    text = re.sub(r"^app_ids:\n(?:  .*\n)*", "app_ids: {}\n", text, flags=re.M)
    profile.write_text(text, encoding="utf-8")
    print(f"\n  New app id namespace: {namespace}")
    print("  Cleared the pinned app ids, so every agent id derives fresh.")

    print("\n  Re-rendering:")
    if subprocess.call(["uv", "run", "tools/render.py"], cwd=ROOT) != 0:
        print("\n  Render failed. Review the changes, then run `uv run just validate`.")
        return 1

    print("\n  Done. Two things to check by hand:\n")
    print(f"    - The README logo block points at {domain}/assets/. Provide those images,")
    print("      or remove the <picture> block at the top of README.md.")
    if not include_sources:
        print("    - knowledge/sources.yaml still fetches the Libre DevOps standards. Replace them")
        print("      with your own, or put documents in knowledge/local/ and reference them.")
    else:
        print("    - knowledge/sources.yaml now points at your domain. Fix the URLs before running")
        print("      `just update-knowledge`, or it will fail.")
    print("\n  Then: git diff, uv run just validate, and commit.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
