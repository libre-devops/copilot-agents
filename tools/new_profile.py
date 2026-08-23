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
KNOWLEDGE_LOCAL = ROOT / "knowledge" / "local"

# Agent Builder accepts these directly. Anything else text-like is converted to .txt, because
# Markdown, YAML and JSON are not accepted however sensible that would be.
UPLOADABLE = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".pdf"}
CONVERTIBLE = {".md", ".mdx", ".yaml", ".yml", ".json", ".hcl", ".tf", ".rst", ".adoc", ""}

# Which agents it is worth offering to reground. agent-author is grounded in the declarative agent
# schema, which is Microsoft's and not yours, so it is not offered.
REGROUNDABLE = {
    "terraform-author": "Terraform standards",
    "logic-app-author": "Logic App standards",
}

BRAND_ACCENT = "#15803D"

# Hosts that almost always sit behind a login. Scoped web search reads only the Bing index, so a
# site like this returns nothing and the agent quietly falls back to its own knowledge instead.
PRIVATE_HINTS = (
    "atlassian.net", "sharepoint.com", "visualstudio.com", "dev.azure.com",
    "confluence", "intranet", ".internal", ".corp", ".local", "localhost",
)


def normalise_url(raw: str) -> tuple[str, list[str]]:
    """Coerce a publisher URL into the HTTPS form the app manifest requires.

    The opposite of normalise_site, and the asymmetry is worth stating: publisher URLs are written
    into the manifest verbatim and must be absolute HTTPS, while docs_url is written into the agent
    definition as https://{{docs_url}} and so must not carry a scheme. Rather than expect anyone to
    remember which is which, both prompts accept either form and fix it here.
    """
    notes: list[str] = []
    value = raw.strip().rstrip("/")
    if value.startswith("http://"):
        value = "https://" + value[len("http://"):]
        notes.append("upgraded http:// to https://, which the app manifest requires")
    elif not value.startswith("https://"):
        value = "https://" + value
        notes.append("added https://, which the app manifest requires")
    return value, notes


def normalise_site(raw: str) -> tuple[str, list[str]]:
    """Coerce whatever the user pasted into something usable as a scoped web search site.

    The agent definitions write this token as `https://{{docs_url}}`, so the value must not carry a
    scheme of its own. Scoped web search also allows at most two path segments and no query string,
    and a URL breaking either rule fails the render rather than the prompt, which is far too late to
    be useful.
    """
    notes: list[str] = []
    value = raw.strip()

    stripped = re.sub(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", "", value)
    if stripped != value:
        notes.append("removed the scheme, because the agent definition adds https:// itself")
        value = stripped

    trimmed = value.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    if trimmed != value:
        notes.append("removed the query string, which scoped web search rejects")
        value = trimmed

    host, _, path = value.partition("/")
    segments = [seg for seg in path.split("/") if seg]
    if len(segments) > 2:
        value = "/".join([host, *segments[:2]])
        notes.append(
            f"trimmed {len(segments)} path segments to two, which is the scoped web search limit"
        )

    if any(hint in host.lower() for hint in PRIVATE_HINTS):
        notes.append(
            f"{host} looks like it needs a login. Scoped web search reads only the Bing index, so "
            "it will return nothing from there. Ground the agents in uploaded knowledge files "
            "instead: see docs/knowledge.md"
        )

    return value, notes


def ask(prompt: str, default: str, interactive: bool) -> str:
    if not interactive:
        return default
    try:
        answer = input(f"  {prompt}\n    [{default}]: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n  cancelled")
        raise SystemExit(1) from None
    return answer or default


def import_knowledge(raw: str, profile: str, label: str) -> tuple[list[str], list[str]]:
    """Copy the user's documents into knowledge/local/, converting where Agent Builder needs it.

    Accepts a single file or a directory. Names are prefixed with the profile so an imported
    document can never collide with an upstream pack, and everything lands in knowledge/local/,
    which is gitignored: internal standards must not become committable by being put in the
    obvious place.
    """
    notes: list[str] = []
    source = Path(raw.strip()).expanduser()
    if not source.exists():
        return [], [f"{source} does not exist, keeping the default {label}"]

    candidates = sorted(p for p in source.iterdir() if p.is_file()) if source.is_dir() else [source]
    imported: list[str] = []
    KNOWLEDGE_LOCAL.mkdir(parents=True, exist_ok=True)

    for item in candidates:
        suffix = item.suffix.lower()
        target_name = f"{profile}-{slug(item.stem)}"
        if suffix in UPLOADABLE:
            target = KNOWLEDGE_LOCAL / f"{target_name}{suffix}"
            target.write_bytes(item.read_bytes())
        elif suffix in CONVERTIBLE:
            try:
                text = item.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                notes.append(f"skipped {item.name}: not readable as text")
                continue
            target = KNOWLEDGE_LOCAL / f"{target_name}.txt"
            target.write_text(f"# {item.name}\n\n{text}", encoding="utf-8")
            notes.append(f"converted {item.name} to {target.name}, Agent Builder does not accept {suffix}")
        else:
            notes.append(f"skipped {item.name}: Agent Builder does not accept {suffix}")
            continue
        imported.append(f"local/{target.name}")

    if not imported:
        notes.append(f"nothing usable found, keeping the default {label}")
    return imported, notes


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9-]", "-", name.lower()).strip("-") or "profile"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a branding profile interactively.")
    parser.add_argument("name", help="profile name, used as the file name and the id")
    parser.add_argument("--defaults", action="store_true", help="accept every default without asking")
    parser.add_argument(
        "--brief",
        action="store_true",
        help="suppress the closing next-steps block, for a caller that prints its own",
    )
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

    def ask_url(prompt: str, default: str) -> str:
        value, notes = normalise_url(ask(prompt, default, interactive))
        for note in notes:
            print(f"    note: {note}")
        return value

    website = ask_url("Website URL", f"https://{domain}")
    privacy = ask_url("Privacy statement URL", f"{website}/privacy")
    terms = ask_url("Terms of use URL", f"{website}/terms")
    docs_raw = ask(
        "Where your standards live (paste a URL, it gets normalised)",
        f"{domain}/standards",
        interactive,
    )
    docs, docs_notes = normalise_site(docs_raw)
    for note in docs_notes:
        print(f"    note: {note}")
    registry_raw = ask("Terraform registry namespace", "registry.terraform.io/namespaces", interactive)
    registry, registry_notes = normalise_site(registry_raw)
    for note in registry_notes:
        print(f"    note: {note}")
    accent = ask("Accent colour for the icons, as #RRGGBB", BRAND_ACCENT, interactive)
    version = ask("App package version, must not start with 0", "1.0.0", interactive)

    # Knowledge. The agents ship the Libre DevOps standards; this is where you swap in your own.
    overrides: dict[str, list[str]] = {}
    if interactive:
        print("\n  Knowledge. The agents ship the Libre DevOps standards as uploaded files.")
        print("  Give a path to a file or a folder to use your own, or press Enter to keep them.")
        print("  Anything you import goes in knowledge/local/, which is gitignored.\n")
    for agent_id, label in REGROUNDABLE.items():
        answer = ask(f"Your {label} (file or folder, Enter to keep the default)", "", interactive)
        if not answer.strip():
            continue
        imported, notes = import_knowledge(answer, name, label)
        for note in notes:
            print(f"    note: {note}")
        if imported:
            overrides[agent_id] = imported
            print(f"    imported {len(imported)} file(s) for {agent_id}")

    namespace = uuid.uuid5(uuid.NAMESPACE_DNS, f"{name}.copilot-agents")

    if overrides:
        block = (
            "\n# Your own knowledge, imported into knowledge/local/ which is gitignored.\n"
            "agent_overrides:\n"
        )
        for agent_id, files_ in overrides.items():
            block += f"  {agent_id}:\n    knowledge_files:\n"
            block += "".join(f"      - {f}\n" for f in files_)
    else:
        block = """
# Ground the agents in your own documents instead of the Libre DevOps ones:
#
#   1. Put your standards in knowledge/local/ (gitignored) as .txt, .pdf or .docx
#   2. Point the agents at them here, prefixing the name with local/
#
# agent_overrides:
#   terraform-author:
#     knowledge_files:
#       - local/our-terraform-standard.txt
#
# To ground in SharePoint instead of uploaded files, override capabilities as well:
#
#   terraform-author:
#     capabilities:
#       - name: OneDriveAndSharePoint
#         items_by_url:
#           - url: https://contoso.sharepoint.com/sites/PlatformEngineering
"""

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
{block}""",
        encoding="utf-8",
    )

    print(f"\nCreated profiles/{name}.yaml")
    print(f"  app id namespace {namespace}")
    if any("needs a login" in n for n in docs_notes) and not overrides:
        print("\n  Your standards are not reachable by web search, and you kept the Libre DevOps")
        print("  knowledge packs, so these agents will enforce those rather than yours. To fix it:")
        print("    1. put your documents in knowledge/local/ (gitignored) as .txt, .pdf or .docx")
        print(f"    2. list them under agent_overrides in profiles/{name}.yaml, prefixed local/")
        print("  See docs/knowledge.md. The commented block at the bottom of the profile shows how.")
    elif overrides:
        grounded = ", ".join(sorted(overrides))
        print(f"\n  Grounded in your own documents: {grounded}.")
        print("  Anything not listed there keeps the Libre DevOps standards.")

    if "example.invalid" in target.read_text(encoding="utf-8"):
        print("  note: some URLs are placeholders on example.invalid, fine for Agent Builder,")
        print("        replace them before publishing an app package")
    if not args.brief:
        print(f"\nNext:  just package {name}")
        print(f"       then open build/{name}/terraform-author/BUILD-GUIDE.md\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
