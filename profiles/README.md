# Profiles

A branding profile is everything about an agent that is not its behaviour: who publishes it, what
it is called, what colour it is, and which app ids it claims.

| File | What it is |
|---|---|
| `default.yaml` | Libre DevOps. Renders into the committed `rendered/` tree and is what CI gates on |
| `example.yaml` | a worked example to copy. Every value is generic on purpose |

## Adding your own

```bash
just new-profile acme
```

**Anything you add here is gitignored.** `.gitignore` allowlists `default.yaml` and `example.yaml`
by name, so an internal or customer profile cannot reach a public repository unless someone
deliberately adds an exception.

Full reference in [docs/profiles.md](../docs/profiles.md).
