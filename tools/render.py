#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml>=6"]
# ///
"""Compose Libre DevOps declarative agent definitions into Microsoft 365 app packages.

Each agent is authored once, in `agents/<id>/agent.yaml`, and its instructions are assembled from
reusable fragments under `fragments/`. This renderer concatenates those fragments, enforces every
platform limit that the manifest cannot enforce for itself, and writes the committed output to
`rendered/<id>/`.

The instruction budget is the reason this tool exists. Schema 1.8 caps `instructions` at 8,000
characters. The documented and only supported way to stay inside that cap is to write less, not to
push prose into a knowledge source: knowledge content is subject to cross-prompt injection
classifiers and is not honoured as maker-authored instruction. So the build fails loudly on
overflow rather than silently truncating.

Usage:
    uv run tools/render.py                       # render every agent
    uv run tools/render.py terraform-author      # render one
    uv run tools/render.py --check               # fail if rendered/ is stale (CI drift gate)
    uv run tools/render.py --package             # also write dist/<id>-<version>.zip
    uv run tools/render.py --with-embedded-knowledge

Exit codes: 0 clean, 1 a limit was breached or rendered/ is stale, 2 usage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
AGENTS = ROOT / "agents"
FRAGMENTS = ROOT / "fragments"
RENDERED = ROOT / "rendered"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"

SCHEMA_VERSION = "v1.8"
SCHEMA_URL = f"https://developer.microsoft.com/json-schemas/copilot/declarative-agent/{SCHEMA_VERSION}/schema.json"
APP_MANIFEST_VERSION = "1.18"
APP_SCHEMA_URL = f"https://developer.microsoft.com/en-us/json-schemas/teams/v{APP_MANIFEST_VERSION}/MicrosoftTeams.schema.json"

# Declarative agent schema 1.8 limits, checked against the published schema on 2026-08-23.
MAX_INSTRUCTIONS = 8000
MAX_NAME = 100
MAX_DESCRIPTION = 1000
MAX_STARTERS = 12
MAX_ACTIONS = 10
MAX_DISCLAIMER = 500
MAX_WEBSEARCH_SITES = 4
MAX_TEAMS_URLS = 5
MAX_EMBEDDED_FILES = 10
MAX_EMBEDDED_BYTES = 1_048_576
EMBEDDED_SUFFIXES = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".pdf"}

# Microsoft 365 app manifest limits.
MAX_APP_NAME_SHORT = 30
MAX_APP_NAME_FULL = 100
MAX_APP_DESC_SHORT = 80
MAX_APP_DESC_FULL = 4000

# developer.privacyUrl and developer.termsOfUseUrl are required and must resolve. They point into
# this repository rather than at libredevops.org/privacy and /terms, which do not exist.
DEVELOPER = {
    "name": "Libre DevOps",
    "websiteUrl": "https://libredevops.org",
    "privacyUrl": "https://github.com/libre-devops/copilot-agents#privacy",
    "termsOfUseUrl": "https://github.com/libre-devops/copilot-agents/blob/main/LICENSE",
}


class RenderError(Exception):
    """A platform limit was breached, or the definition is malformed."""


def fail(agent_id: str, message: str) -> None:
    raise RenderError(f"{agent_id}: {message}")


def compose_instructions(agent_id: str, names: list[str]) -> str:
    """Concatenate instruction fragments in declared order, separated by a blank line."""
    if not names:
        fail(agent_id, "no instruction fragments declared")
    parts: list[str] = []
    for name in names:
        path = FRAGMENTS / name
        if not path.is_file():
            fail(agent_id, f"instruction fragment not found: fragments/{name}")
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            fail(agent_id, f"instruction fragment is empty: fragments/{name}")
        parts.append(text)
    return "\n\n".join(parts) + "\n"


def check_dashes(agent_id: str, instructions: str) -> None:
    """House rule: no em dashes or en dashes anywhere, including in the rendered instructions."""
    for char, label in (("—", "em dash"), ("–", "en dash")):
        if char in instructions:
            line = instructions[: instructions.index(char)].count("\n") + 1
            fail(agent_id, f"{label} found in composed instructions at line {line}")


def build_capabilities(agent_id: str, spec: dict, embedded: bool) -> list[dict]:
    caps = [dict(c) for c in spec.get("capabilities", [])]
    seen: set[str] = set()
    for cap in caps:
        name = cap.get("name")
        if not name:
            fail(agent_id, "a capability has no name")
        if name in seen:
            fail(agent_id, f"capability {name} declared more than once (one of each type is allowed)")
        seen.add(name)
        if name == "WebSearch":
            sites = cap.get("sites", [])
            if len(sites) > MAX_WEBSEARCH_SITES:
                fail(agent_id, f"WebSearch has {len(sites)} sites, the limit is {MAX_WEBSEARCH_SITES}")
            for site in sites:
                url = site.get("url", "")
                if "?" in url:
                    fail(agent_id, f"WebSearch site URL must not carry a query string: {url}")
                segments = [s for s in url.split("://", 1)[-1].split("/")[1:] if s]
                if len(segments) > 2:
                    fail(agent_id, f"WebSearch site URL takes at most two path segments: {url}")
        if name == "TeamsMessages" and len(cap.get("urls", [])) > MAX_TEAMS_URLS:
            fail(agent_id, f"TeamsMessages exceeds {MAX_TEAMS_URLS} urls")

    if embedded:
        files = (spec.get("embedded_knowledge") or {}).get("files", [])
        if files:
            if "EmbeddedKnowledge" in seen:
                fail(agent_id, "EmbeddedKnowledge is generated from embedded_knowledge, do not also declare it")
            if len(files) > MAX_EMBEDDED_FILES:
                fail(agent_id, f"{len(files)} embedded files, the limit is {MAX_EMBEDDED_FILES}")
            entries = []
            for item in files:
                target = item.get("as") or Path(item["source"]).name
                if Path(target).suffix.lower() not in sorted(EMBEDDED_SUFFIXES):
                    fail(agent_id, f"embedded file type not supported: {target}")
                source = ROOT / item["source"]
                if not source.is_file():
                    fail(agent_id, f"embedded source not found: {item['source']}")
                size = source.stat().st_size
                if size > MAX_EMBEDDED_BYTES:
                    fail(agent_id, f"embedded file {target} is {size} bytes, the limit is {MAX_EMBEDDED_BYTES}")
                entries.append({"file": target})
            caps.append({"name": "EmbeddedKnowledge", "files": entries})
    return caps


def build_declarative_agent(agent_id: str, spec: dict, instructions: str, embedded: bool) -> dict:
    name = spec["name"]
    description = " ".join(spec["description"].split())

    if len(instructions) > MAX_INSTRUCTIONS:
        over = len(instructions) - MAX_INSTRUCTIONS
        fail(
            agent_id,
            f"instructions are {len(instructions)} characters, {over} over the {MAX_INSTRUCTIONS} limit. "
            "Cut a fragment. Do not move instruction prose into a knowledge source.",
        )
    if len(name) > MAX_NAME:
        fail(agent_id, f"name is {len(name)} characters, the limit is {MAX_NAME}")
    if len(description) > MAX_DESCRIPTION:
        fail(agent_id, f"description is {len(description)} characters, the limit is {MAX_DESCRIPTION}")

    manifest: dict = {
        "$schema": SCHEMA_URL,
        "version": SCHEMA_VERSION,
        "name": name,
        "description": description,
        "instructions": instructions,
    }

    caps = build_capabilities(agent_id, spec, embedded)
    if caps:
        manifest["capabilities"] = caps

    starters = spec.get("conversation_starters", [])
    if len(starters) > MAX_STARTERS:
        fail(agent_id, f"{len(starters)} conversation starters, the limit is {MAX_STARTERS}")
    if starters:
        manifest["conversation_starters"] = [
            {k: " ".join(str(v).split()) for k, v in s.items()} for s in starters
        ]

    actions = spec.get("actions", [])
    if actions:
        if len(actions) > MAX_ACTIONS:
            fail(agent_id, f"{len(actions)} actions, the limit is {MAX_ACTIONS}")
        manifest["actions"] = actions

    if spec.get("behavior_overrides"):
        manifest["behavior_overrides"] = spec["behavior_overrides"]

    disclaimer = spec.get("disclaimer")
    if disclaimer:
        text = " ".join(disclaimer["text"].split())
        if len(text) > MAX_DISCLAIMER:
            fail(agent_id, f"disclaimer is {len(text)} characters, the limit is {MAX_DISCLAIMER}")
        manifest["disclaimer"] = {"text": text}

    if spec.get("user_overrides"):
        manifest["user_overrides"] = spec["user_overrides"]

    return manifest


def build_app_manifest(agent_id: str, spec: dict) -> dict:
    pkg = spec["package"]
    short_name = pkg["short_name"]
    full_name = pkg["full_name"]
    short_desc = " ".join(pkg["short_description"].split())
    full_desc = " ".join(spec["description"].split())

    for value, limit, label in (
        (short_name, MAX_APP_NAME_SHORT, "package.short_name"),
        (full_name, MAX_APP_NAME_FULL, "package.full_name"),
        (short_desc, MAX_APP_DESC_SHORT, "package.short_description"),
        (full_desc, MAX_APP_DESC_FULL, "description"),
    ):
        if len(value) > limit:
            fail(agent_id, f"{label} is {len(value)} characters, the limit is {limit}")

    return {
        "$schema": APP_SCHEMA_URL,
        "manifestVersion": APP_MANIFEST_VERSION,
        "version": pkg["version"],
        "id": pkg["app_id"],
        "developer": DEVELOPER,
        "icons": {"color": "color.png", "outline": "outline.png"},
        "name": {"short": short_name, "full": full_name},
        "description": {"short": short_desc, "full": full_desc},
        "accentColor": pkg["accent_color"],
        "copilotAgents": {
            "declarativeAgents": [{"id": agent_id, "file": "declarativeAgent.json"}]
        },
    }


def render_one(agent_id: str, embedded: bool, dest_root: Path = RENDERED) -> dict[str, str]:
    spec = yaml.safe_load((AGENTS / agent_id / "agent.yaml").read_text(encoding="utf-8"))
    if spec.get("id") != agent_id:
        fail(agent_id, f"id in agent.yaml is {spec.get('id')!r}, expected {agent_id!r}")

    instructions = compose_instructions(agent_id, spec.get("instructions", []))
    check_dashes(agent_id, instructions)

    da = build_declarative_agent(agent_id, spec, instructions, embedded)
    app = build_app_manifest(agent_id, spec)

    # Wipe first. `--check` promises that rendered/ equals a fresh render, which is only true if
    # a file that is no longer produced also disappears (an embedded knowledge file left behind by
    # an earlier --with-embedded-knowledge run, for instance).
    out = dest_root / agent_id
    if out.is_dir():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    files: dict[str, str] = {}

    for filename, payload in (("declarativeAgent.json", da), ("manifest.json", app)):
        text = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        (out / filename).write_text(text, encoding="utf-8")
        files[filename] = hashlib.sha256(text.encode("utf-8")).hexdigest()

    for icon in ("color.png", "outline.png"):
        source = ASSETS / icon
        if source.is_file():
            shutil.copyfile(source, out / icon)
            files[icon] = hashlib.sha256(source.read_bytes()).hexdigest()

    if embedded:
        for item in (spec.get("embedded_knowledge") or {}).get("files", []):
            target = item.get("as") or Path(item["source"]).name
            data = (ROOT / item["source"]).read_bytes()
            (out / target).write_bytes(data)
            files[target] = hashlib.sha256(data).hexdigest()

    used = len(instructions)
    pct = used * 100 // MAX_INSTRUCTIONS
    print(f"  {agent_id}: instructions {used}/{MAX_INSTRUCTIONS} ({pct}%), {len(files)} files")
    return files


def package_one(agent_id: str, version: str) -> Path:
    DIST.mkdir(parents=True, exist_ok=True)
    target = DIST / f"{agent_id}-{version}.zip"
    source = RENDERED / agent_id
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source.iterdir()):
            if path.is_file():
                zf.write(path, path.name)
    print(f"  packaged {target.relative_to(ROOT)}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Libre DevOps declarative agents.")
    parser.add_argument("agents", nargs="*", help="agent ids to render (default: all)")
    parser.add_argument("--check", action="store_true", help="fail if rendered/ differs from a fresh render")
    parser.add_argument("--package", action="store_true", help="also write dist/<id>-<version>.zip")
    parser.add_argument(
        "--with-embedded-knowledge",
        action="store_true",
        help="emit the EmbeddedKnowledge capability (see docs/knowledge.md for why this is off by default)",
    )
    args = parser.parse_args()

    available = sorted(p.name for p in AGENTS.iterdir() if (p / "agent.yaml").is_file())
    selected = args.agents or available
    unknown = [a for a in selected if a not in available]
    if unknown:
        print(f"unknown agent(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"available: {', '.join(available)}", file=sys.stderr)
        return 2

    # Cross-agent check, always over every agent rather than only the selected ones: two agents
    # sharing an app_id collide on install, and rendering one at a time must not hide that.
    ids: dict[str, list[str]] = {}
    for agent_id in available:
        try:
            spec = yaml.safe_load((AGENTS / agent_id / "agent.yaml").read_text(encoding="utf-8"))
            app_id = (spec.get("package") or {}).get("app_id")
        except yaml.YAMLError as exc:
            print(f"ERROR {agent_id}: agent.yaml is not valid YAML: {exc}", file=sys.stderr)
            return 1
        if app_id:
            ids.setdefault(app_id, []).append(agent_id)
    clashes = {k: v for k, v in ids.items() if len(v) > 1}
    if clashes:
        print("\nERROR duplicate package.app_id, which collides on install:", file=sys.stderr)
        for app_id, owners in sorted(clashes.items()):
            print(f"  {app_id}: {', '.join(owners)}", file=sys.stderr)
        return 1

    # In --check mode render into a scratch tree and compare. A gate that writes to the thing it
    # is checking would pass on a second local run even though the commit is still stale.
    with tempfile.TemporaryDirectory() as tmp:
        dest_root = Path(tmp) if args.check else RENDERED
        verb = "Checking" if args.check else "Rendering"
        print(f"{verb} {len(selected)} agent(s) at schema {SCHEMA_VERSION}:")
        inventory: dict[str, dict] = {}
        try:
            for agent_id in selected:
                inventory[agent_id] = render_one(agent_id, args.with_embedded_knowledge, dest_root)
        except RenderError as exc:
            print(f"\nERROR {exc}", file=sys.stderr)
            return 1
        except KeyError as exc:
            print(f"\nERROR missing required key in agent.yaml: {exc}", file=sys.stderr)
            return 1

        if args.check:
            drifted: list[str] = []
            for agent_id in selected:
                fresh_dir, live_dir = dest_root / agent_id, RENDERED / agent_id
                fresh = {p.name: p.read_bytes() for p in fresh_dir.glob("*") if p.is_file()}
                live = {p.name: p.read_bytes() for p in live_dir.glob("*") if p.is_file()} if live_dir.is_dir() else {}
                for name in sorted(set(fresh) | set(live)):
                    if name not in live:
                        drifted.append(f"rendered/{agent_id}/{name} (missing)")
                    elif name not in fresh:
                        drifted.append(f"rendered/{agent_id}/{name} (no longer generated)")
                    elif fresh[name] != live[name]:
                        drifted.append(f"rendered/{agent_id}/{name} (differs)")
            if drifted:
                print("\nERROR rendered/ is stale. Run `just render` and commit:", file=sys.stderr)
                for key in drifted:
                    print(f"  {key}", file=sys.stderr)
                return 1
            print("rendered/ is current.")
            return 0

    inv_text = json.dumps(
        {"schema_version": SCHEMA_VERSION, "agents": inventory}, indent=2, ensure_ascii=False
    ) + "\n"
    (RENDERED / "inventory.json").write_text(inv_text, encoding="utf-8")

    if args.package:
        for agent_id in selected:
            spec = yaml.safe_load((AGENTS / agent_id / "agent.yaml").read_text(encoding="utf-8"))
            package_one(agent_id, spec["package"]["version"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
