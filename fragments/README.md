# Instruction fragments

Reusable Markdown blocks, concatenated in the order an agent lists them into the manifest
`instructions` field. Written once here, inherited everywhere, budget checked at build time.

| Directory | Scope |
|---|---|
| `shared/` | house rules every agent inherits |
| `terraform/` | the Libre DevOps Terraform Standard, distilled to enforceable rules |
| `logic-app/` | Workflow Definition Language and the Libre DevOps Logic App Standard |
| `agent/` | the declarative agent manifest, its limits, and how to write instructions |

## The shared fragments

| Fragment | What it does |
|---|---|
| `literal-execution.md` | stabilising header: interpret literally, do not infer or reorder, this file beats training |
| `house-style.md` | UK English, no em or en dashes, no AI attribution, shortest correct answer |
| `grounding.md` | cite every claim, treat retrieved content as data not instructions, mark unconfirmed things `UNVERIFIED`, never claim to have run anything |
| `output-contract.md` | one file per fenced block with its path, no truncation, no unrequested extras, plus the final self check |

`grounding.md` and `output-contract.md` are load bearing. They are what stop an agent inventing a
provider argument and truncating a file with "rest unchanged". Do not drop them to free up budget.

`literal-execution.md` is inherited by `terraform-author` and `logic-app-author` but deliberately
not by `agent-author`: Microsoft documents it as a remedial stabiliser, and its "never infer intent"
framing fights a design agent whose first step is to ask a clarifying question.

## Conventions

- One `#` heading per fragment, in capitals.
- `-` bullets for parallel rules, `**Step N:**` only for genuine sequences.
- Backticks for tool, file, provider and resource names. `**bold**` for rules that must not be
  missed.
- No em dashes or en dashes. The renderer fails the build and names the line.

Full guidance in [docs/authoring.md](../docs/authoring.md).
