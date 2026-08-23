# Knowledge

Vendored factual grounding material. **Facts only, never instructions**: see
[docs/instruction-budget.md](../docs/instruction-budget.md) for why that line is enforced rather
than merely encouraged.

| File | What it is | Source |
|---|---|---|
| `workflowdefinition.schema.json` | the Azure Logic Apps workflow definition schema, 2016-06-01 | [schema.management.azure.com](https://schema.management.azure.com/providers/Microsoft.Logic/schemas/2016-06-01/workflowdefinition.json) |

## Getting this into a package

JSON is **not** an allowed embedded document type. The allowed set is `.doc`, `.docx`, `.ppt`,
`.pptx`, `.xls`, `.xlsx`, `.txt` and `.pdf`, so the renderer emits this schema into the package as
`workflowdefinition.schema.txt`, driven by the `as:` key in the agent's `embedded_knowledge` block.

Embedded knowledge is off by default. See [docs/knowledge.md](../docs/knowledge.md).
