# Tools

Three scripts, no environment to create. Each carries a PEP 723 header, so `uv run` resolves its
dependencies on the fly.

| Script | What it does |
|---|---|
| `render.py` | substitutes profile tokens, composes fragments, enforces every platform limit. `--profile` selects the branding, `--check` is the CI drift gate, `--package` builds the zips, `--with-embedded-knowledge` emits the optional capability |
| `lint.py` | validates a rendered tree against the vendored schema, then the semantics the schema cannot express, then brand leakage for a non-default profile |
| `make_icons.py` | draws the colour and outline icons from source in the profile's brand colour, with no image library |

```bash
uv run tools/render.py --check     # or: just validate
uv run tools/lint.py
uv run tools/make_icons.py
```

## What each gate actually catches

The renderer fails the build on: instruction budget overflow (never truncation), an em or en dash
in a composed instruction set, a missing or empty fragment, a duplicate capability, a `WebSearch`
URL with more than two path segments or a query string, an unsupported or oversized embedded file,
any string over its documented limit, an unresolved `{{placeholder}}`, a profile with a missing
token or a non-HTTPS publisher URL, and two agents sharing an app id (checked across every agent
even when you render only one, since a collision would otherwise stay hidden).

The linter fails on: schema violations, a missing `instructions` field, an unrecognised root
property, a dangling icon or embedded file reference, and app manifest fields over their limits. It
warns when instructions pass 90 percent of the budget, and when an agent has no conversation
starters.

The last two exist because the published schema does not enforce them even though the platform
does. See [../docs/platform-notes.md](../docs/platform-notes.md).
