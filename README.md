<div align="center">
  <a href="https://libredevops.org">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://libredevops.org/assets/libre-devops-white.png">
      <img alt="Libre DevOps" src="https://libredevops.org/assets/libre-devops-black.png" width="300">
    </picture>
  </a>
</div>

# Copilot Agents

Microsoft 365 Copilot declarative agents as code: a growing collection of custom agents, composed
from reusable instruction fragments, validated against the published schema, and rendered into
uploadable app packages. Terraform and Azure Logic Apps are where the collection starts, not where
it stops.

Branding is a swappable profile, so you can publish the same agents under your own organisation
with two commands and without editing a fragment.

[![CI](https://github.com/libre-devops/copilot-agents/actions/workflows/ci.yml/badge.svg)](https://github.com/libre-devops/copilot-agents/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/libre-devops/copilot-agents)](./LICENSE)

> **The manifests are the product.** A declarative agent is chat shaped: it produces Terraform and
> workflow JSON in the Copilot pane for a human to review and commit. It does not write to your
> repositories. What lives here is the versioned, reviewable definition of how it behaves.

---

## Prerequisites

Just [`uv`](https://docs.astral.sh/uv/). It brings its own Python and the task runner, so there is
nothing else to install and no global Python to pollute.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh     # macOS and Linux
winget install --id=astral-sh.uv                    # Windows
```

## Quick start

```bash
git clone https://github.com/libre-devops/copilot-agents.git
cd copilot-agents
uv run just quickstart
```

That is the whole thing. It checks the knowledge packs, renders, lints, and then prints the exact
file to open and the URL to open it beside:

```
[1/4] Knowledge packs................... 5 present
[2/4] Profile........................... using profiles/default.yaml
[3/4] Rendering......................... 3 agents
[4/4] Linting........................... clean

Done. Build your first agent:

  1. Open   https://m365.cloud.microsoft/agents/new
  2. Choose "Skip to configure", not the Describe tab
  3. Follow rendered/terraform-author/BUILD-GUIDE.md
```

Offline, no tenant, nothing to log in to. The build guide then tells you what to paste into every
field, which files to upload, how to test it and how to share it.

### Under your own branding

```bash
uv run just quickstart cdsr
```

Name a profile that does not exist yet and the wizard runs on the way through. It asks for your
organisation name, URLs and colour, each with a default, and then **asks for your own standards**,
importing a file or a whole folder and converting Markdown, YAML or JSON into the `.txt` Agent
Builder requires. Imported documents land in `knowledge/local/`, which is gitignored, so an internal
standard cannot become committable by being put in the obvious place.

Hold Enter through every question and you still get something that builds, on the Libre DevOps
standards. See [docs/knowledge.md](./docs/knowledge.md) to reground it later.

### Where things end up

| Path | Manifests and build guide | App packages |
|---|---|---|
| default profile | `rendered/<agent>/` (committed) | `dist/` |
| your profile | `build/<profile>/<agent>/` | `dist/<profile>/` |

### Running without syncing at all

Every script in [`tools/`](./tools) carries a
[PEP 723](https://peps.python.org/pep-0723/) inline metadata header, so `uv` resolves each one's
dependencies on the fly. If you only want to build once and never touch the repo again, you need no
virtual environment and no `just`:

```bash
uv run tools/render.py
uv run tools/lint.py
```

`pyproject.toml` exists for the other case: working on the repo, where one environment holding the
task runner and the linters is more convenient. Keep its versions in step with the PEP 723 headers.

## The agents

| Agent | What it does | Uploaded knowledge |
|---|---|---|
| [`terraform-author`](./agents/terraform-author) | Terraform to the Libre DevOps Terraform Standard and Azure Naming Convention: the file split, `for_each` over `count`, the `this` label, argument ordering, typed variables, and the three kinds of assertion (`validation` at plan time, `check` to warn, `precondition` to abort) | the Terraform Standard, the Azure Naming Convention |
| [`logic-app-author`](./agents/logic-app-author) | Workflow Definition Language: the three export wrappers, declarations versus values, action names as stored keys, and the failure modes that pass validation and break at run time | the Logic App Standard, the workflow definition schema |
| [`agent-author`](./agents/agent-author) | Declarative agents themselves: schema v1.8 and every limit it imposes, which capabilities cost a licence, and how to structure instructions inside the budget | the declarative agent manifest schema |

Each also gets scoped `WebSearch` over the relevant public references, but the uploaded files come
first: the agents are instructed to treat them as authoritative over both web results and their own
training. That ordering is what makes them enforce *your* standard rather than generic advice.

All three ship the same contract: every factual claim cites its source, retrieved content is data
rather than instructions, a knowledge source that returns nothing is reported rather than quietly
replaced with model knowledge, anything unconfirmed is marked `UNVERIFIED` rather than guessed, and
the agent never claims to have run, deployed or validated anything.

## How it fits together

```
fragments/          instruction fragments, composed in order   what the agent DOES
  shared/           house rules every agent inherits
  terraform/        the Terraform standard, distilled to rules
  logic-app/        Workflow Definition Language, distilled to rules
  agent/            the declarative agent manifest and its limits
        |
agents/<id>/agent.yaml    the definition: metadata, fragment list, capabilities, starters
        |
profiles/<name>.yaml      publisher, tokens, colour, app ids        who PUBLISHES it
        |
   tools/render.py        substitute, compose, enforce every limit, fail loudly
        |
rendered/<id>/            committed output for the default profile
build/<profile>/<id>/     everything else, gitignored
  BUILD-GUIDE.md          paste-ready field values for Agent Builder
        |
   tools/lint.py          schema validation, semantics, and brand leakage
        |
dist/[<profile>/]<id>-<ver>.zip    the uploadable Microsoft 365 app package
```

`rendered/` is committed on purpose. It is the drop-in path for anyone who wants the manifests
without running the toolchain, and CI fails if it drifts from its source.

## Build an agent in Agent Builder

This is the path most people want: no admin, no tenant upload, and you can share the result with a
link in about five minutes.

**Agent Builder has no import path.** It is a form, so you cannot upload a `declarativeAgent.json`
into it. That is why every render also writes a paste-ready **`rendered/<agent>/BUILD-GUIDE.md`**,
which is the bridge between the version controlled definition and the form. Open the guide next to
the browser and work down it.

### 1. Open Agent Builder

Go to <https://m365.cloud.microsoft/agents/new>, or choose **New agent** in the left pane of the
Microsoft 365 Copilot app. It also works from `microsoft365.com/chat`, `office.com/chat`, and the
Teams desktop and web clients. It is not available on mobile.

On the **New agent** screen choose **Skip to configure**. The natural language **Describe** tab
writes instructions for you, which is not what you want here: the point of this repository is that
the instructions are reviewed, budgeted and version controlled.

### 2. Fill in the Configure tab

Every field below comes straight out of the build guide, in the order Agent Builder asks for it.

| Agent Builder field | Comes from | Limit |
|---|---|---|
| **Name** | guide section 1 | **30 characters**, tighter than the manifest's 100 |
| **Icon** | `rendered/<agent>/color.png` | PNG, 192x192, 1 MB |
| **Description** | guide section 2 | 1,000 characters |
| **Instructions** | guide section 3, paste the whole block | 8,000 characters |
| **Knowledge**, uploaded files | guide section 4, drag from `knowledge/` | 20 files, `.txt .pdf .docx` and friends |
| **Knowledge**, Enter URL | guide section 4 | 4 public websites, two path levels each, no query strings |
| **Capabilities** | guide section 5, both off | code interpreter, image generator |
| **Model** | guide section 6 | Auto, Quick response, or Think deeper |
| **Starter Prompts** | guide section 8 | 12 maximum |
| **About this agent** (**...** menu) | guide section 9 | short description 80, URLs must be HTTPS |

Three things worth getting right:

- **Upload the knowledge files before you add the websites.** They are the standards the agent is
  meant to enforce, and it is instructed to trust them over web results and over its own training.
  Scoped web search only reads what Bing indexes, so it can never see private documentation: the
  uploads are what make the agent actually authoritative. They need a Copilot licence or metered
  usage; the rest of the agent works without one.
- **Leave the other Work content toggles off** (Outlook, Teams, People) unless you actually want
  tenant grounding. An unscoped source reaches much further than most people expect.
- **Leave "Only use specified sources" off.** An agent that cannot draw on its own knowledge of HCL
  or JSON cannot write either, and the knowledge precedence in its instructions already puts your
  standards first. Agent Builder describes that toggle as prioritising your sources rather than
  blocking model knowledge, which it states plainly it cannot fully do.

### 3. Test before you create

Use the **Try it** pane. The build guide lists three checks worth doing every time:

1. Run each starter prompt and confirm it does what its title claims.
2. Ask for something just outside the agent's scope and confirm it declines rather than improvises.
3. Paste content containing an embedded instruction and confirm the agent reports it as text it
   found rather than acting on it.

Then choose **Create**. The agent is private to you at first.

### 4. Share it

Choose **Share** on the created agent.

- **Can chat** lets someone use it. **Can edit** makes them a co-owner with full rights. Groups can
  only be added as chat users, so owners must be added individually.
- **Copy chat link** and send it to whoever needs it.
- **Org-wide sharing for chat access** lists the agent in the Agent Store for everyone in the
  tenant. An admin policy can restrict or disable this.
- To get into **Built by your org**, submit the agent to your org catalog and an admin reviews it in
  the Microsoft 365 admin centre. The shared version and the catalog version are managed separately.

After any later edit, choose **Update**, or your changes stay invisible to the people you shared
with. If the agent uses SharePoint knowledge, reshare it so file permissions follow.

Full detail: [Share and manage agents](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder-share-manage-agents).

### Round tripping

Agent Builder can export what you built: **View all agents**, then **...**, then **Download .zip
file**, which contains the agent manifest and icon and can be sideloaded into Teams. That zip cannot
include embedded files. It is a one way trip out of the builder, so this repository stays the source
of truth and the build guide stays the way in.

## Install an agent from the app package

The alternative path, for publishing to an organisation rather than sharing from your own account.
There is no create API for a declarative agent, so this is an admin or portal step and this repo
ends where the API does.

1. Build the package: `uv run just package` (or `uv run just package <profile>`).
2. Upload `dist/<agent>-<version>.zip` through the
   [Microsoft 365 admin centre](https://learn.microsoft.com/en-us/microsoft-365/admin/manage/manage-plugins-for-copilot-in-integrated-apps)
   under Integrated apps, or side load it with the
   [Microsoft 365 Agents Toolkit](https://aka.ms/M365AgentsToolkit) for testing.
3. Assign it to the users or groups who should see it.

Agents using only `WebSearch` work without a Microsoft 365 Copilot licence. Every other capability
needs a licence or metered usage enabled in the tenant.

## Which path should I use?

| | Agent Builder | App package |
|---|---|---|
| Who can do it | any licensed user | a tenant admin |
| Time to first share | minutes | an approval cycle |
| How people get it | a chat link, or the Agent Store | assigned in Integrated apps |
| Actions and API plugins | not supported, use Copilot Studio | supported |
| Getting your definition in | paste from `BUILD-GUIDE.md` | upload the zip directly |
| Best for | trying an agent, sharing with a team | rolling one out to an organisation |

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

## Forking it entirely

`new-profile` brands the **agents**. If you are forking the repository itself and want the README,
the docs, the licence and the default profile to be yours too:

```bash
uv run just rebrand
```

It asks for your organisation name, GitHub org, domain, prefix and copyright holder, previews every
replacement with a per-file count, and only writes once you confirm. All replacements happen in a
single pass, so a value you supply is never itself rewritten (replacing `Libre DevOps` with
`Waldo Corp` and then replacing `ldo` would otherwise produce `Wacm Corp`).

It also issues a **new app id namespace** and clears the pinned ids, so your fork cannot claim the
same agent identities as upstream.

> **Run it just after forking, not later.** Changing the namespace changes every agent id, and the
> agent names change too. Agents already installed from this checkout do not follow: they would have
> to be rebuilt and reshared.

You do not need to have cloned it. Downloading the zip and copying it into an existing repository is
a normal way to adopt this, and the tool handles it: unless it finds a clean git checkout, where
`git checkout .` already does the job, it copies every file it is about to change into
`.rebrand-backup/<timestamp>/` and prints the one command that restores them.

Two things it deliberately does not touch: `knowledge/*.txt`, because those are other people's
published documents and rewriting their text would falsify them, and its own source, because its
search strings are the very words it is replacing.

## Repository layout

| Path | What it holds |
|---|---|
| [`agents/`](./agents) | one directory per agent: `agent.yaml` and a README |
| [`profiles/`](./profiles) | branding profiles: publisher, tokens, colour, app ids. Yours is gitignored |
| [`fragments/`](./fragments) | instruction fragments, the single source for shared house rules |
| [`rendered/`](./rendered) | generated manifests, icons and Agent Builder build guides, committed and drift gated, never hand edited |
| [`knowledge/`](./knowledge) | the standards agents upload as knowledge, fetched by `just update-knowledge` |
| [`schema/`](./schema) | the vendored declarative agent JSON schema, refreshed by `just update-schema` |
| [`tools/`](./tools) | the renderer, the linter, and the icon generator |
| [`docs/`](./docs) | the operating model, see below |
| [`dist/`](./dist) | build output, gitignored |

## Documentation

| Document | What it covers |
|---|---|
| [instruction-budget.md](./docs/instruction-budget.md) | the 8,000 character cap, why you cannot route around it, and how to spend it |
| [authoring.md](./docs/authoring.md) | adding an agent, the fragment convention, choosing capabilities, testing |
| [profiles.md](./docs/profiles.md) | publishing under your own brand, tokens, app id derivation, output routing |
| [roadmap.md](./docs/roadmap.md) | what is planned, and what is blocked on the platform rather than on effort |
| [knowledge.md](./docs/knowledge.md) | what grounds each agent, WebSearch and embedded file limits, tenant sources |
| [platform-notes.md](./docs/platform-notes.md) | where the docs, the schema and reality disagree, with dates |

## Verified against

Everything here was checked against the live Microsoft documentation on **2026-08-23**, not written
from memory:
[declarative agent schema 1.8](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-manifest-1.8),
[write effective instructions](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-instructions),
[the Microsoft 365 app model for agents](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agents-are-apps),
[Agent Builder](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder),
[building agents with Agent Builder](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder-build-agents),
[adding knowledge sources](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder-add-knowledge),
[sharing and managing agents](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder-share-manage-agents),
and the [published JSON schema](https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.8/schema.json).

Where they disagree with each other, the discrepancy is recorded in
[platform-notes.md](./docs/platform-notes.md) rather than papered over.

## Roadmap

More agents, since this is a collection rather than two topics. Real branding assets. A repeatable
behaviour test pack, because the offline gates prove packaging and not behaviour.

The question that comes up most is whether deployment can be automated with Terraform. **Not
properly, and the blocker is authentication rather than tooling.** Microsoft Graph does have a
publish API (`POST /appCatalogs/teamsApps`), but it supports **no application permissions at all**,
only delegated ones, so there is no service principal and no federated CI identity. Separately,
`msgraph_resource` serialises its `body` as JSON and the endpoint needs a raw `application/zip`, so
the provider cannot express the call either way.

Wrapping it in `local-exec` would be a shell script in a Terraform costume: no plan, no drift
detection, and state that lies the moment an admin touches the portal. So the repository stops at a
reproducible, drift gated, sha256 recorded artefact and leaves the upload to a human.

The full reasoning, including what would change the answer, is in
[docs/roadmap.md](./docs/roadmap.md).

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
