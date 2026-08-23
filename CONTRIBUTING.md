# Contributing

## Before you open a pull request

```bash
just validate
```

That is the whole offline gate and exactly what CI runs: a fresh render checked against the
committed `rendered/` tree, then schema and semantic linting. It needs no tenant, no credentials
and no spend.

If you changed a fragment or an agent definition, re-render and commit the result:

```bash
just render
git add rendered/
```

CI fails if `rendered/` does not match its source, because `rendered/` is the drop-in delivery path
for people who never run the toolchain.

## What a good change looks like

- **Sourced.** If you add or change a manifest field, a limit or a platform claim, cite the
  Microsoft page you checked and the date. If it contradicts another Microsoft page, record the
  discrepancy in `docs/platform-notes.md` rather than picking one silently.
- **Inside the budget.** `instructions` caps at 8,000 characters. The renderer prints the spend on
  every run and fails on overflow. Do not free up room by moving instructions into a knowledge
  source, and read `docs/instruction-budget.md` before you try.
- **UK English, no em dashes or en dashes.** Enforced by the renderer and the linter.
- **Behaviour tested where it can be.** The gates prove the package is well formed and within every
  limit. They cannot prove the agent behaves. If you change instructions, say in the pull request
  what you ran in a tenant and what it did. See the testing section of `docs/authoring.md`.

## Branding

Never hardcode an organisation's name, URL, colour or product code in a fragment or an agent
definition. Add a `{{token}}` and give it a value in `profiles/default.yaml`. The renderer fails the
build on an unresolved placeholder, and the linter warns when default branding leaks into a
rebranded render.

Profiles other than `default` and `example` are gitignored on purpose. Do not add exceptions for
them: see [docs/profiles.md](./docs/profiles.md).

## Adding an agent

See [docs/authoring.md](./docs/authoring.md). In short: a new directory under `agents/`, a fresh
`app_id` GUID, fragments listed in order, then `just render && just lint`.

## Attribution

All contributions are your own work. Do not add AI attribution trailers or footers to commits, pull
requests or any artefact in this repository.
