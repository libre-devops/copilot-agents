# Agents

One directory per agent: `agent.yaml` is the definition, `README.md` explains what it is for.
Everything else is generated into [`rendered/`](../rendered).

| Agent | Purpose |
|---|---|
| [`terraform-author`](./terraform-author) | Terraform to the Libre DevOps Terraform Standard and Azure Naming Convention |
| [`logic-app-author`](./logic-app-author) | Azure Logic App workflow definitions in Workflow Definition Language |
| [`agent-author`](./agent-author) | Microsoft 365 Copilot declarative agents, the meta-agent that authors what this repo ships |

Adding one is covered in [docs/authoring.md](../docs/authoring.md). Every agent needs its own
`package.app_id` GUID: two agents sharing one will collide on install.
