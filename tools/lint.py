#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema>=4.21"]
# ///
"""Lint rendered declarative agent manifests.

Three layers, because no single one is sufficient:

1. Structure: the manifest validates against the vendored declarative agent schema
   (schema/declarative-agent-v1.8.schema.json, draft-04, fetched from developer.microsoft.com).
   The schema is strict: an unrecognised property invalidates the whole document.
2. Semantics the schema does not express: at most one capability of each derived type, WebSearch
   URL shape, embedded file types and sizes, and the app manifest pointing at a declarative agent
   file that actually exists in the package.
3. House rules: no em dashes or en dashes, and instruction headroom reported so a change that
   quietly eats the remaining budget is visible in review.

4. Brand leakage: when linting a profile other than the default, any value from the default
   profile's tokens that survives into the output is reported. That is how a rebrand silently ships
   someone else's branding, for example the `ldo` product infix inside a storage account name.

Usage:
    uv run tools/lint.py                     # lint everything under rendered/
    uv run tools/lint.py --profile acme      # lint build/acme/
    uv run tools/lint.py rendered/terraform-author

Exit codes: 0 clean (warnings allowed), 1 errors, 2 usage.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft4Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "declarative-agent-v1.8.schema.json"
RENDERED = ROOT / "rendered"
BUILD = ROOT / "build"
PROFILES = ROOT / "profiles"
DEFAULT_PROFILE = "default"

MAX_INSTRUCTIONS = 8000
WARN_INSTRUCTIONS = 7200  # 90 percent of the cap
# Agent Builder's Name field allows 30 characters where the manifest allows 100. An over-long name
# packages fine but cannot be typed into the builder, so this is a warning, not an error.
MAX_BUILDER_NAME = 30
EMBEDDED_SUFFIXES = {".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx", ".txt", ".pdf"}
MAX_EMBEDDED_BYTES = 1_048_576

errors: list[str] = []
warnings: list[str] = []


def error(where: str, message: str) -> None:
    errors.append(f"{where}: {message}")


def warn(where: str, message: str) -> None:
    warnings.append(f"{where}: {message}")


def lint_declarative_agent(path: Path, validator: Draft4Validator) -> None:
    where = str(path.relative_to(ROOT))
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        error(where, f"invalid JSON: {exc}")
        return

    for issue in sorted(validator.iter_errors(manifest), key=lambda e: list(e.path)):
        pointer = "/".join(str(p) for p in issue.path) or "(root)"
        error(where, f"schema: {pointer}: {issue.message}")

    # The reference states that unrecognised properties invalidate the entire document, but the
    # published schema carries no `additionalProperties: false` at the root (checked 2026-08-23),
    # so Draft4Validator will happily accept a typo'd key that the platform then rejects. Derive
    # the allowlist from the schema itself so it tracks future versions. `$schema` is allowed
    # because Microsoft's own reference manifest includes it, even though it is not a declared
    # property.
    allowed = set(validator.schema.get("properties", {})) | {"$schema"}
    for key in sorted(set(manifest) - allowed):
        error(where, f"unrecognised root property {key!r}, which invalidates the whole document")

    # `instructions` is documented as Required but is absent from the schema's own `required`
    # array (checked 2026-08-23), so the schema alone will not catch a manifest without it.
    instructions = manifest.get("instructions")
    if not instructions:
        error(where, "instructions is missing or empty (documented as required)")
    else:
        used = len(instructions)
        if used > MAX_INSTRUCTIONS:
            error(where, f"instructions {used} characters, over the {MAX_INSTRUCTIONS} cap")
        elif used >= WARN_INSTRUCTIONS:
            warn(where, f"instructions {used}/{MAX_INSTRUCTIONS}, under 10 percent headroom left")

    for field in ("instructions", "description", "name"):
        value = manifest.get(field) or ""
        for char, label in (("—", "em dash"), ("–", "en dash")):
            if char in value:
                error(where, f"{label} in {field}, house style forbids it")

    seen: set[str] = set()
    for cap in manifest.get("capabilities", []):
        name = cap.get("name", "?")
        if name in seen:
            error(where, f"capability {name} declared more than once")
        seen.add(name)
        if name == "WebSearch":
            for site in cap.get("sites", []):
                url = site.get("url", "")
                if "?" in url:
                    error(where, f"WebSearch site carries a query string: {url}")
                segments = [s for s in url.split("://", 1)[-1].split("/")[1:] if s]
                if len(segments) > 2:
                    error(where, f"WebSearch site has {len(segments)} path segments, max 2: {url}")
        if name == "EmbeddedKnowledge":
            for entry in cap.get("files", []):
                filename = entry.get("file", "")
                target = path.parent / filename
                if Path(filename).suffix.lower() not in EMBEDDED_SUFFIXES:
                    error(where, f"embedded file type not supported: {filename}")
                if not target.is_file():
                    error(where, f"embedded file not present in the package: {filename}")
                elif target.stat().st_size > MAX_EMBEDDED_BYTES:
                    error(where, f"embedded file over 1 MB: {filename}")

    name = manifest.get("name") or ""
    if len(name) > MAX_BUILDER_NAME:
        warn(
            where,
            f"name is {len(name)} characters. The manifest allows 100, but Agent Builder's Name "
            f"field allows {MAX_BUILDER_NAME}, so this agent cannot be built there as named.",
        )

    if not manifest.get("conversation_starters"):
        warn(where, "no conversation starters, users get an empty prompt surface")


def lint_app_manifest(path: Path) -> None:
    where = str(path.relative_to(ROOT))
    try:
        app = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        error(where, f"invalid JSON: {exc}")
        return

    agents = app.get("copilotAgents", {}).get("declarativeAgents", [])
    if len(agents) != 1:
        error(where, f"{len(agents)} declarative agents declared, exactly one is supported")
    for entry in agents:
        referenced = path.parent / entry.get("file", "")
        if not referenced.is_file():
            error(where, f"declarativeAgents points at a missing file: {entry.get('file')}")

    for icon in ("color", "outline"):
        filename = app.get("icons", {}).get(icon)
        if not filename:
            error(where, f"icons.{icon} is missing, the package will fail validation")
        elif not (path.parent / filename).is_file():
            error(where, f"icons.{icon} points at a missing file: {filename}")

    for field, limit in (("short", 30), ("full", 100)):
        value = app.get("name", {}).get(field, "")
        if len(value) > limit:
            error(where, f"name.{field} is {len(value)} characters, the limit is {limit}")
    for field, limit in (("short", 80), ("full", 4000)):
        value = app.get("description", {}).get(field, "")
        if len(value) > limit:
            error(where, f"description.{field} is {len(value)} characters, the limit is {limit}")

    # Publishing to an organisation's app catalog rejects a 0.x version with VersionHasMajorLessThan1:
    # "App version shouldn't start with '0'." The Agent Builder path never sees this field, so it is a
    # warning rather than an error. Checked 2026-08-23 against the Graph teamsApp publish reference.
    version = str(app.get("version", ""))
    if version.startswith("0"):
        warn(
            where,
            f"app version {version!r} starts with 0. Publishing to an org app catalog rejects that "
            "(VersionHasMajorLessThan1). Set package.version to 1.0.0 or higher in the profile.",
        )


def default_tokens() -> dict:
    """The default profile's token values, read without a YAML dependency."""
    path = PROFILES / f"{DEFAULT_PROFILE}.yaml"
    if not path.is_file():
        return {}
    tokens, in_tokens = {}, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("tokens:"):
            in_tokens = True
            continue
        if in_tokens:
            if line[:1] not in (" ", "\t") and line.strip():
                break
            if ":" in line and line.strip() and not line.strip().startswith("#"):
                key, _, value = line.strip().partition(":")
                cleaned = value.strip().strip("\"'")
                if cleaned:
                    tokens[key.strip()] = cleaned
    return tokens


def lint_brand_leakage(path: Path, profile: str) -> None:
    """Report default-profile branding that survived into a rebranded package."""
    where = str(path.relative_to(ROOT))
    text = path.read_text(encoding="utf-8")
    for key, value in default_tokens().items():
        # Match case-insensitively: the infix appears lower case inside generated resource names.
        if value.lower() in text.lower():
            warn(
                where,
                f"profile {profile!r} still contains the default profile's {key} value {value!r}. "
                "If that is not deliberate, add the token to your profile.",
            )


def main() -> int:
    if not SCHEMA.is_file():
        print(f"schema not found: {SCHEMA}", file=sys.stderr)
        return 2
    validator = Draft4Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))

    argv = sys.argv[1:]
    profile = DEFAULT_PROFILE
    if "--profile" in argv:
        index = argv.index("--profile")
        if index + 1 >= len(argv):
            print("--profile needs a name", file=sys.stderr)
            return 2
        profile = argv[index + 1]
        del argv[index : index + 2]

    root = RENDERED if profile == DEFAULT_PROFILE else BUILD / profile
    if not root.is_dir():
        print(f"nothing to lint at {root}, run `just render {profile}` first", file=sys.stderr)
        return 2

    targets = [Path(a).resolve() for a in argv] or sorted(
        p
        for p in root.iterdir()
        if p.is_dir() and (p / "declarativeAgent.json").is_file()
    )
    if not targets:
        print("nothing to lint, run `just render` first", file=sys.stderr)
        return 2

    for target in targets:
        if not target.is_dir():
            print(f"not a directory: {target}", file=sys.stderr)
            return 2
        da = target / "declarativeAgent.json"
        app = target / "manifest.json"
        if not da.is_file():
            error(str(target), "declarativeAgent.json is missing")
            continue
        lint_declarative_agent(da, validator)
        if app.is_file():
            lint_app_manifest(app)
        else:
            error(str(target), "manifest.json is missing")
        if profile != DEFAULT_PROFILE:
            lint_brand_leakage(da, profile)

    for message in warnings:
        print(f"WARN  {message}")
    for message in errors:
        print(f"ERROR {message}", file=sys.stderr)

    checked = len(targets)
    if errors:
        print(
            f"\n{len(errors)} error(s), {len(warnings)} warning(s) across {checked} agent(s).",
            file=sys.stderr,
        )
        return 1
    print(f"\n{checked} agent(s) clean, {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
