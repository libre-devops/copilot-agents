#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Everything from a fresh clone to a build guide you can paste from.

Chains the steps that were previously four commands and a docs lookup: check the knowledge packs
exist, create a branding profile if one was asked for and is missing, render, lint, then print the
exact paths and the URL to open. Each step delegates to the tool that owns it, so there is one
implementation of each thing and this only sequences them.

Usage:
    uv run tools/quickstart.py              # the Libre DevOps agents, into rendered/
    uv run tools/quickstart.py acme         # your own branding, into build/acme/
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE = ROOT / "knowledge"
PROFILES = ROOT / "profiles"
DEFAULT_PROFILE = "default"
BUILDER_URL = "https://m365.cloud.microsoft/agents/new"

# The agent to start with. One working agent teaches the flow, and the rest are the same paste job.
FIRST_AGENT = "terraform-author"


def run(args: list[str], *, interactive: bool = False) -> int:
    """Run a sibling tool through uv so it resolves its own PEP 723 dependencies."""
    command = ["uv", "run", *args]
    if interactive:
        return subprocess.call(command, cwd=ROOT)
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
    return result.returncode


def step(number: int, total: int, label: str) -> None:
    print(f"[{number}/{total}] {label.ljust(34, '.')}", end=" ", flush=True)


def done(message: str) -> None:
    print(message, flush=True)


def main() -> int:
    profile = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PROFILE).strip() or DEFAULT_PROFILE
    total = 4

    print("\nCopilot agents quickstart")
    print("=" * 25)
    print()

    step(1, total, "Knowledge packs")
    packs = sorted(KNOWLEDGE.glob("*.txt"))
    if not packs:
        done("missing, fetching")
        if run(["tools/fetch_knowledge.py"]) != 0:
            print("\nCould not fetch the knowledge packs. Check your network, or run")
            print("`uv run just update-knowledge` for the full output.")
            return 1
    else:
        done(f"{len(packs)} present")

    step(2, total, "Profile")
    target = PROFILES / f"{profile}.yaml"
    if target.is_file():
        done(f"using profiles/{profile}.yaml")
    elif profile == DEFAULT_PROFILE:
        done("missing profiles/default.yaml")
        return 1
    else:
        # Flush before the subprocess writes to the same stdout, or "creating" lands after its
        # output rather than before it.
        print("creating", flush=True)
        print(flush=True)
        if run(["tools/new_profile.py", profile, "--brief"], interactive=True) != 0:
            return 1
        print()

    step(3, total, "Rendering")
    if run(["tools/render.py", "--profile", profile]) != 0:
        print("failed. Run `uv run just render", profile, "` for the full output.")
        return 1
    out = Path("rendered") if profile == DEFAULT_PROFILE else Path("build") / profile
    agents = sorted(p.name for p in (ROOT / out).iterdir() if p.is_dir() and p.name != "assets")
    done(f"{len(agents)} agents")

    step(4, total, "Linting")
    if run(["tools/lint.py", "--profile", profile]) != 0:
        print(f"failed. Run `uv run just lint {profile}` for the full output.")
        return 1
    done("clean")

    first = out / FIRST_AGENT / "BUILD-GUIDE.md"
    knowledge = ROOT / out / FIRST_AGENT / "knowledge"
    print("\nDone. Build your first agent:\n")
    print(f"  1. Open   {BUILDER_URL}")
    print("  2. Choose \"Skip to configure\", not the Describe tab")
    print(f"  3. Follow {first}")
    if knowledge.is_dir():
        count = len(list(knowledge.iterdir()))
        print(f"\n  Section 4 asks you to upload {count} file(s) from {out / FIRST_AGENT / 'knowledge'}.")
        print("  Do that before adding the web sources: they are what make the agent")
        print("  enforce your standard rather than generic advice.")

    remaining = [a for a in agents if a != FIRST_AGENT]
    if remaining:
        print("\n  Then the same for:")
        for agent in remaining:
            print(f"    {out / agent / 'BUILD-GUIDE.md'}")

    print("\n  Sharing is section 11 of the guide: Create, then Share, then Copy chat link.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
