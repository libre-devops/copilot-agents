# Knowledge

The documents agents upload into Agent Builder as knowledge. Facts only, never instructions: see
[docs/instruction-budget.md](../docs/instruction-budget.md) for why that line is enforced.

`sources.yaml` declares each document and where it comes from. `just update-knowledge` fetches,
converts and writes the `.txt` files here, which are committed so a render needs no network and the
exact bytes an agent is grounded in show up in a diff.

Agent Builder accepts `.doc .docx .ppt .pptx .xls .xlsx .txt .pdf`, and 20 files per agent. Markdown
and JSON are not accepted, which is why MDX is stripped to prose and code and JSON schemas are
pretty printed into `.txt`.

To ground agents in your own standards, add your URLs to `sources.yaml` or drop files in here, then
point an agent at them from your profile. See [docs/knowledge.md](../docs/knowledge.md).
