# LDO Copilot Agent Author

Designs, writes and reviews Microsoft 365 Copilot declarative agents. The meta-agent: it authors the
kind of thing this repository ships, which makes the repo self-hosting.

## What it knows

- **Schema v1.8 and every limit it imposes**: the required fields, `name` 100, `description` 1000,
  `instructions` 8000, 12 conversation starters, 1 to 10 actions, a 500 character disclaimer, and
  the 4,000 character default for any string not otherwise capped.
- **All 14 capabilities by name**, so it does not invent one, plus the scoping traps: four
  `WebSearch` sites at two path segments each, and an unscoped `OneDriveAndSharePoint` or
  `TeamsMessages` capability quietly granting the whole organisation.
- **Which capabilities cost money.** `WebSearch` is the only one that works without a Copilot
  licence or metered usage, so it recommends that first and names the licence cost of anything else.
- **That an unrecognised property invalidates the whole document**, which is why it refuses to
  invent a field.
- **The 8,000 character budget and why you cannot route around it.** It reports the character count
  of any instruction set it writes, and it will tell you not to offload instructions into a
  knowledge source rather than helping you do it. See
  [docs/instruction-budget.md](../../docs/instruction-budget.md).
- **That there is no create API**, so upload stays an admin or portal step.

## A deliberate difference from the other two agents

This is the only agent that does **not** inherit `shared/literal-execution.md`.

Microsoft documents the literal-execution header as a remedial stabiliser for an agent that has
started reordering or inventing steps, not as a default. Its framing, "never infer intent, never
fill in missing steps", works against an agent whose first step is to turn a vague brief into a
design and ask a question when it cannot. `terraform-author` and `logic-app-author` keep it, because
their output is precise code where inference is a defect.

If you find this agent drifting or reordering its steps, adding the fragment back to its
`instructions:` list is the documented first response.

## Knowledge

`WebSearch`, scoped to Microsoft Learn's Microsoft 365 and Teams documentation,
`developer.microsoft.com/json-schemas`, and the Libre DevOps standards.

The declarative agent schema itself is wired up as `EmbeddedKnowledge` but is not rendered by
default, for the reason in [docs/platform-notes.md](../../docs/platform-notes.md):

```bash
just render agent-author --with-embedded-knowledge
```

## What it will not do

It does not validate or upload anything. It emits the manifest and tells you to run the schema
validation and then test in a tenant, including the two tests that matter most: that an
out-of-scope request is declined, and that content carrying an embedded instruction is reported
rather than obeyed.

## Install

See the [repository README](../../README.md#install-an-agent). The package is
`dist/agent-author-0.1.0.zip`, built with `just package`.
