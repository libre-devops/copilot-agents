# Tools

Three scripts, no environment to create. Each carries a PEP 723 header, so `uv run` resolves its
dependencies on the fly.

| Script | What it does |
|---|---|
| `render.py` | composes fragments into `rendered/`, enforcing every platform limit. `--check` is the CI drift gate, `--package` builds the zips, `--with-embedded-knowledge` emits the optional capability |
| `lint.py` | validates `rendered/` against the vendored schema, then the semantics the schema cannot express |
| `make_icons.py` | draws `assets/color.png` and `assets/outline.png` from source, with no image library |

```bash
uv run tools/render.py --check     # or: just validate
uv run tools/lint.py
uv run tools/make_icons.py
```

## What each gate actually catches

The renderer fails the build on: instruction budget overflow (never truncation), an em or en dash
in a composed instruction set, a missing or empty fragment, a duplicate capability, a `WebSearch`
URL with more than two path segments or a query string, an unsupported or oversized embedded file,
any string over its documented limit, and two agents sharing a `package.app_id` (checked across
every agent even when you render only one, since a collision would otherwise stay hidden).

The linter fails on: schema violations, a missing `instructions` field, an unrecognised root
property, a dangling icon or embedded file reference, and app manifest fields over their limits. It
warns when instructions pass 90 percent of the budget, and when an agent has no conversation
starters.

The last two exist because the published schema does not enforce them even though the platform
does. See [../docs/platform-notes.md](../docs/platform-notes.md).
