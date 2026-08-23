#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# ///
"""Create a branding profile by asking, rather than by making you edit YAML.

Every prompt shows a default in brackets. Press Enter to take it. The point is that you can hold
Enter all the way through and still get a profile that renders, packages and passes the linter, then
fix the placeholders later when you know what they should be.

Placeholders are deliberately obvious (`https://example.invalid/...`) so that an unedited value is
visible in review rather than quietly shipping. `example.invalid` is reserved by RFC 2606 and can
never resolve, which is the point.

Usage:
    uv run tools/new_profile.py acme
    uv run tools/new_profile.py acme --defaults    # take every default, ask nothing
"""
from __future__ import annotations

import argparse
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILES = ROOT / "profiles"

BRAND_ACCENT = "#15803D"


def ask(prompt: str, default: str, interactive: bool) -> str:
    if not interactive:
        return default
    try:
        answer = input(f"  {prompt}\n    [{default}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  cancelled")
        raise SystemExit(1) from None
    return answer or default


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-") or "profile"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a branding profile interactively.")
    parser.add_argument("name", help="profile name, used as the file name and the id")
    parser.add_argument("--defaults", action="store_true", help="accept every default without asking")
    args = parser.parse_args()

    name = slug(args.name)
    target = PROFILES / f"{name}.yaml"
    if target.exists():
        print(f"{target.relative_to(ROOT)} already exists", file=sys.stderr)
        return 1

    interactive = not args.defaults and sys.stdin.isatty()
    if interactive:
        print(f"\nCreating profiles/{name}.yaml. Press Enter to accept each default.\n")

    org = ask("Organisation name, as it appears to users", args.name.title(), interactive)
    short = ask("Short prefix for agent names, keep it brief", name[:4].upper(), interactive)
    infix = ask("Lower case product code used inside generated resource names", name[:3].lower(), interactive)

    domain = f"{name}.example.invalid"
    website = ask("Website URL", f"https://{domain}", interactive)
    privacy = ask("Privacy statement URL", f"{website.rstrip('/')}/privacy", interactive)
    terms = ask("Terms of use URL", f"{website.rstrip('/')}/terms", interactive)
    docs = ask(
        "Where your standards live, without the scheme (used in agent instructions)",
        f"{domain}/standards",
        interactive,
    )
    registry = ask("Terraform registry namespace", "registry.terraform.io/namespaces", interactive)
    accent = ask("Accent colour for the icons, as #RRGGBB", BRAND_ACCENT, interactive)
    version = ask("App package version, must not start with 0", "1.0.0", interactive)

    namespace = uuid.uuid5(uuid.NAMESPACE_DNS, f"{name}.copilot-agents")

    target.write_text(
        f"""# {org} branding profile, created by `just new-profile {name}`.
#
# Anything left as example.invalid is a placeholder: RFC 2606 reserves that suffix so it can never
# resolve, which makes an unedited value obvious rather than silently wrong. The app manifest
# requires these URLs to be HTTPS and to resolve, so replace them before publishing an app package.
# The Agent Builder path does not check them.
#
# This file is gitignored. See docs/profiles.md.
---
id: {name}

tokens:
  brand_short: {short}
  brand_name: {org}
  brand_infix: {infix}
  registry_url: {registry}
  docs_url: {docs}

publisher:
  name: {org}
  website_url: {website}
  privacy_url: {privacy}
  terms_url: {terms}

package:
  version: {version}
  accent_color: "{accent}"

app_id_namespace: {namespace}
app_ids: {{}}

# Ground the agents in your own documents instead of the Libre DevOps ones:
#
#   1. Put your standards in knowledge/ as .txt, .pdf or .docx, or add their raw URLs to
#      knowledge/sources.yaml and run `just update-knowledge`.
#   2. Point the agents at them here.
#
# agent_overrides:
#   terraform-author:
#     knowledge_files:
#       - our-terraform-standard.txt
#
# To ground in SharePoint instead of uploaded files, override capabilities as well:
#
#   terraform-author:
#     capabilities:
#       - name: OneDriveAndSharePoint
#         items_by_url:
#           - url: https://contoso.sharepoint.com/sites/PlatformEngineering
""",
        encoding="utf-8",
    )

    print(f"\nCreated profiles/{name}.yaml")
    print(f"  app id namespace {namespace}")
    if "example.invalid" in target.read_text(encoding="utf-8"):
        print("  note: some URLs are placeholders on example.invalid, fine for Agent Builder,")
        print("        replace them before publishing an app package")
    print(f"\nNext:  just package {name}")
    print(f"       then open build/{name}/terraform-author/BUILD-GUIDE.md\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
