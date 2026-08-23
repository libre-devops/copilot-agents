<div align="center">
  <a href="https://libredevops.org">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://libredevops.org/assets/libre-devops-white.png">
      <img alt="Libre DevOps" src="https://libredevops.org/assets/libre-devops-black.png" width="300">
    </picture>
  </a>
</div>

# Copilot Agents

Microsoft 365 Copilot declarative agents as code: agent definitions that teach Copilot to write
Terraform and Azure Logic App workflows to the Libre DevOps standards, composed from reusable
instruction fragments, validated against the published schema, and rendered into uploadable app
packages.

[![CI](https://github.com/libre-devops/copilot-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/libre-devops/copilot-agents/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/libre-devops/copilot-agents)](./LICENSE)

> **The manifests are the product.** A declarative agent is chat shaped: it produces Terraform and
> workflow JSON in the Copilot pane for a human to review and commit. It does not write to your
> repositories. What lives here is the versioned, reviewable definition of how it behaves.

---

## Quick start

```bash
git clone https://github.com/libre-devops/copilot-agents.git
cd copilot-agents

just validate    # render, drift gate, and lint. Offline, no tenant, no cost.
just package     # build dist/<agent>-<version>.zip, ready to upload
```

Everything above runs offline and needs no Microsoft 365 tenant. Only installing an agent does.

## The agents

| Agent | What it does | Knowledge |
|---|---|---|
| [`terraform-author`](./agents/terraform-author) | Writes and reviews Terraform to the Libre DevOps Terraform Standard and Azure Naming Convention: the file split, `for_each` over `count`, the `this` label, argument ordering, typed variables with validation, pinned providers | `WebSearch` over the standards, the HashiCorp language reference, the Libre DevOps registry namespace and Microsoft Learn |
| [`logic-app-author`](./agents/logic-app-author) | Writes, repairs and reviews Workflow Definition Language: the three export wrappers, declarations versus values, action names as stored keys, and the failure modes that pass validation and break at run time | `WebSearch` over the standards and Microsoft Learn, plus the Azure workflow definition schema as optional embedded knowledge |
| [`agent-author`](./agents/agent-author) | Designs, writes and reviews declarative agents themselves: schema v1.8 and every limit it imposes, which capabilities cost a licence, and how to structure instructions inside the budget | `WebSearch` over Microsoft Learn and the published JSON schemas, plus the declarative agent schema as optional embedded knowledge |

Both agents ship the same contract: every factual claim cites its source, retrieved content is data
rather than instructions, anything unconfirmed is marked `UNVERIFIED` rather than guessed, and the
agent never claims to have run, deployed or validated anything.

## How it fits together

```
fragments/          instruction fragments, composed in order
  shared/           house rules every agent inherits
  terraform/        the Terraform standard, distilled to rules
  logic-app/        Workflow Definition Language, distilled to rules
  agent/            the declarative agent manifest and its limits
        |
agents/<id>/agent.yaml    the definition: metadata, fragment list, capabilities, starters
        |
   tools/render.py        compose, enforce every platform limit, fail loudly
        |
rendered/<id>/      committed output: declarativeAgent.json, manifest.json, icons
        |
   tools/lint.py          schema validation plus the semantics the schema cannot express
        |
dist/<id>-<ver>.zip       the uploadable Microsoft 365 app package
```

`rendered/` is committed on purpose. It is the drop-in path for anyone who wants the manifests
without running the toolchain, and CI fails if it drifts from its source.

## The constraint that shapes this repo

Schema 1.8 caps `instructions` at **8,000 characters**. The Libre DevOps Terraform Standard alone is
over 2,500 lines, so it cannot be inlined, and Microsoft explicitly warns against offloading
instructions into a knowledge source to dodge the cap: knowledge content is subject to cross-prompt
injection classifiers and is not honoured as maker-authored instruction.

So the split is deliberate and enforced:

- **Instructions carry behaviour.** Composed from fragments, budget checked at build time, and the
  build **fails** rather than truncates.
- **Knowledge carries facts.** Schemas and reference documentation, for grounding claims only.

Every render prints the spend, so the budget stays visible:

```
  agent-author:     instructions 7144/8000 (89%), 4 files
  logic-app-author: instructions 6799/8000 (84%), 4 files
  terraform-author: instructions 6225/8000 (77%), 4 files
```

Full reasoning in [docs/instruction-budget.md](./docs/instruction-budget.md).

## Install an agent

There is no create API for a declarative agent, so this is an admin or portal step and this repo
ends where the API does.

1. Build the package: `just package`.
2. Upload `dist/<agent>-<version>.zip` through the
   [Microsoft 365 admin centre](https://learn.microsoft.com/en-us/microsoft-365/admin/manage/manage-plugins-for-copilot-in-integrated-apps)
   under Integrated apps, or side load it with the
   [Microsoft 365 Agents Toolkit](https://aka.ms/M365AgentsToolkit) for testing.
3. Assign it to the users or groups who should see it.

Agents using only `WebSearch` work without a Microsoft 365 Copilot licence. Every other capability
needs a licence or metered usage enabled in the tenant.

## Repository layout

| Path | What it holds |
|---|---|
| [`agents/`](./agents) | one directory per agent: `agent.yaml` and a README |
| [`fragments/`](./fragments) | instruction fragments, the single source for shared house rules |
| [`rendered/`](./rendered) | generated manifests and icons, committed and drift gated, never hand edited |
| [`knowledge/`](./knowledge) | factual grounding material, vendored |
| [`schema/`](./schema) | the vendored declarative agent JSON schema, refreshed by `just update-schema` |
| [`tools/`](./tools) | the renderer, the linter, and the icon generator |
| [`docs/`](./docs) | the operating model, see below |
| [`dist/`](./dist) | build output, gitignored |

## Documentation

| Document | What it covers |
|---|---|
| [instruction-budget.md](./docs/instruction-budget.md) | the 8,000 character cap, why you cannot route around it, and how to spend it |
| [authoring.md](./docs/authoring.md) | adding an agent, the fragment convention, choosing capabilities, testing |
| [knowledge.md](./docs/knowledge.md) | what grounds each agent, WebSearch and embedded file limits, tenant sources |
| [platform-notes.md](./docs/platform-notes.md) | where the docs, the schema and reality disagree, with dates |

## Verified against

Everything here was checked against the live Microsoft documentation on **2026-08-23**, not written
from memory:
[declarative agent schema 1.8](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-manifest-1.8),
[write effective instructions](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-instructions),
[the Microsoft 365 app model for agents](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agents-are-apps),
and the [published JSON schema](https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.8/schema.json).

Where they disagree with each other, the discrepancy is recorded in
[platform-notes.md](./docs/platform-notes.md) rather than papered over.

## Privacy

These agents declare `WebSearch` as their only capability. They call no service of ours, send
nothing to Libre DevOps, and this repository collects no data from anyone who uses them.

An installed agent runs inside your Microsoft 365 tenant, so what Copilot does with your prompts and
your grounding data is governed by
[Microsoft's data, privacy and security terms for Microsoft 365 Copilot](https://learn.microsoft.com/en-us/copilot/microsoft-365/microsoft-365-copilot-privacy),
not by anything here. If you add a capability such as `OneDriveAndSharePoint` or `GraphConnectors`
to an agent, you are scoping your own tenant's content, and scoping it is your responsibility: see
[docs/knowledge.md](./docs/knowledge.md) for the defaults that grant more than you might expect.

The `developer.privacyUrl` and `developer.termsOfUseUrl` fields in each app manifest are required
by the Microsoft 365 app schema and point at this section and at the licence below.

## Licence

[MIT](./LICENSE).
