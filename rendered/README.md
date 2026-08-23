# Rendered manifests

**Generated. Never hand edit.** Run `just render` and commit the result.

Each directory is a complete Microsoft 365 app package payload:

| File | What it is |
|---|---|
| `declarativeAgent.json` | the declarative agent manifest, schema v1.8 |
| `manifest.json` | the Microsoft 365 app manifest, pointing at the agent through `copilotAgents` |
| `color.png` | 192x192 colour icon |
| `outline.png` | 32x32 outline icon, required to pass validation |
| `BUILD-GUIDE.md` | paste-ready values for every Agent Builder Configure field, in form order. Not included in the package zip |

`inventory.json` records the sha256 of every rendered file, as the promotion and rollback record.

This directory is committed on purpose. It is the drop-in path for anyone who wants the manifests
without running the toolchain, and CI fails if it drifts from `agents/` and `fragments/`. Run
`just package` to zip these into `dist/` for upload.
