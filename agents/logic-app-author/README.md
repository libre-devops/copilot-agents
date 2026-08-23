# LDO Logic App Author

Writes, repairs and reviews Azure Logic App workflow definitions in Workflow Definition Language,
to the [Libre DevOps Azure Logic App Standard](https://libredevops.org/docs/documents/azure-logic-app-standards/).

## Why this agent exists

WDL punishes guessing. Most mistakes are accepted at save time and fail later, at deploy or silently
at run time. The instructions encode the failures that have actually cost time on a live estate:

- A `runAfter` catch marks the failure handled, so **the run reports Succeeded**. Pair it with a
  `Terminate` or the failure is invisible.
- `Until` is do-until: the body always runs at least once, so a fallback inside it fires on exactly
  the quiet case the loop was meant to skip.
- `SetVariable` and `AppendToArrayVariable` are not safe under a parallel `Foreach`, which defaults
  to 20 repetitions.
- `union()` on arrays de-duplicates, so paging with it silently drops legitimate repeats.
- An `ApiConnection` POST with no `body` creates an empty record that saves cleanly.
- `Compose` output lives only in run history, which expires and is not queryable.
- Action names are stored keys: the designer shows `SNOW - Find ticket`, references use
  `SNOW_-_Find_ticket`, and nothing validates the link at save time.

It also identifies which of the three export wrappers it was handed (bare definition, portal code
view, ARM resource GET) and returns the same shape.

## Knowledge

Seven uploaded documents, which is what makes it authoritative rather than merely fluent:

| File | What it is |
|---|---|
| `azure-logic-app-standards.txt` | the Libre DevOps Azure Logic App Standard |
| `logic-app-workflow-definition-schema.txt` | the 2016-06-01 workflow definition JSON schema |
| `wdl-schema-reference.txt` | Microsoft's Workflow Definition Language schema reference |
| `wdl-triggers-and-actions.txt` | every trigger and action type, with its inputs |
| `wdl-expression-functions.txt` | the full WDL expression function list |
| `azapi-provider.txt` | the Terraform AzApi provider overview |
| `azapi-resource.txt` | the `azapi_resource` reference |

AzApi is there because a workflow deployed through `azapi_resource` is a different shape from the
`azurerm` one, and the agent has to know which it is writing.

Plus `WebSearch`, scoped to the Libre DevOps standards and Microsoft Learn's Azure and connector
documentation, for anything the files do not cover.

The Azure workflow definition schema is wired up as `EmbeddedKnowledge` but is **not** rendered by
default, because Microsoft's 1.8 reference states embedded files are not enabled yet. Enable it
when your tenant supports it:

```bash
just render logic-app-author --with-embedded-knowledge
```

See [docs/knowledge.md](../../docs/knowledge.md) and
[docs/platform-notes.md](../../docs/platform-notes.md).

## What it will not do

It does not deploy or validate anything. Validation of a workflow definition is a deploy-time ARM
operation, so the agent emits the definition and tells you to run `az deployment group validate` or
`terraform plan`.

## Install

See the [repository README](../../README.md#install-an-agent). The package is
`dist/logic-app-author-0.1.0.zip`, built with `just package`.
