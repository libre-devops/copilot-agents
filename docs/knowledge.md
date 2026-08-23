# Knowledge sources

Knowledge grounds factual claims. It never carries instructions. See
[instruction-budget.md](instruction-budget.md) for why that line matters and what happens when it
is crossed.

## What each agent uses today

| Agent | Capability | Source |
|---|---|---|
| `terraform-author` | `WebSearch` | `libredevops.org/docs/documents`, the HashiCorp language reference, the Libre DevOps registry namespace, Microsoft Learn's Azure documentation |
| `logic-app-author` | `WebSearch` | `libredevops.org/docs/documents`, Microsoft Learn's Azure and connector documentation |
| `agent-author` | `WebSearch` | Microsoft Learn's Microsoft 365 and Teams documentation, `developer.microsoft.com/json-schemas`, `libredevops.org/docs/documents` |

`WebSearch` is the only capability that works without a Microsoft 365 Copilot licence or metered
usage in the tenant, which makes it the right default for an open source agent that strangers will
install.

## WebSearch constraints, which the renderer enforces

- At most **four** sites per agent.
- Each URL takes **at most two path segments**. `https://contoso.com/projects/mark-8` is valid,
  `https://contoso.com/projects/mark-8/beta-program` is not.
- No query string.

Both agents expose their `WebSearch` capability through `user_overrides`, so an operator can toggle
it off in the Copilot UI without a new package.

## EmbeddedKnowledge, and why it is off by default

`logic-app-author` declares the Azure workflow definition schema as embedded knowledge, and
`agent-author` declares the declarative agent schema, because grounding in the actual schema is
worth far more than a web search. Neither is emitted unless you ask for it:

```bash
just render logic-app-author --with-embedded-knowledge
just render agent-author --with-embedded-knowledge
```

The reason is recorded in [platform-notes.md](platform-notes.md): the capability is in the schema,
but Microsoft's 1.8 reference states embedded files are not enabled yet. Rendering it by default
would ship a package the platform may reject. Turn it on once your tenant supports it.

Limits, enforced by both the renderer and the linter:

- At most **10** files, each **1 MB** or smaller.
- Types: `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`, `.txt`, `.pdf`. Note that JSON is not
  on that list, which is why `knowledge/workflowdefinition.schema.json` is emitted into the package
  as `workflowdefinition.schema.txt`.

## Uploaded knowledge is the default, and it comes first

Every agent ships a **knowledge pack**: the standards it is meant to enforce, converted to `.txt`
and staged in `rendered/<agent>/knowledge/` ready to drag into Agent Builder's Knowledge section.
The build guide lists them as step one, before any website.

This is deliberate. Uploaded knowledge is the only grounding route that needs **no connector, no
admin, and no public indexing**, so it works in a locked-down tenant where nothing else does.

The agents are told to use it first. `shared/knowledge-precedence.md` sets the order:

1. **Uploaded knowledge files.** The house standards. Authoritative: they beat web results and they
   beat the model's own training wherever they disagree.
2. **Web search**, only for what the files do not cover, such as provider or connector reference.
3. **The model's own knowledge**, last, only to fill a remaining gap, and it must say when it does.

If a knowledge file should have covered a question and returned nothing, the agent says so instead
of moving on. That turns the silent failure described in the next section into a visible one.

### What ships, and how to refresh it

`knowledge/sources.yaml` declares each document and where it comes from. `just update-knowledge`
fetches, converts and writes them; the result is committed so a render needs no network and the
exact bytes an agent is grounded in show up in a diff.

| Agent | Knowledge |
|---|---|
| `terraform-author` | the Terraform Standard, the Azure Naming Convention |
| `logic-app-author` | the Azure Logic App Standard, the workflow definition schema |
| `agent-author` | the declarative agent manifest schema |

MDX is stripped to prose and code (fenced blocks are kept verbatim, since for a standards document
they are the most valuable part) and JSON is pretty printed, because Agent Builder accepts
`.doc .docx .ppt .pptx .xls .xlsx .txt .pdf` and not Markdown or JSON.

### Using your own standards

The quickest route is to let the wizard import them:

```bash
uv run just new-profile acme
```

It asks for a path to your Terraform and Logic App standards, accepts a single file or a whole
folder, converts anything Agent Builder will not take (Markdown, YAML, JSON) into `.txt`, skips what
it cannot use, and writes the `agent_overrides` block for you.

**Imported documents land in `knowledge/local/`, which is gitignored.** That is deliberate:
`knowledge/` itself is tracked because the upstream packs are committed there, so an internal
standard dropped in the obvious place would otherwise be committable. Anything under `local/` cannot
be.

By hand, the same thing:

```yaml
agent_overrides:
  terraform-author:
    knowledge_files:
      - local/our-terraform-standard.txt    # from knowledge/local/, gitignored
      - azure-naming-convention.txt         # an upstream pack, from knowledge/
```

A bare name resolves in `knowledge/`, and a `local/` prefix in `knowledge/local/`. You can mix them,
and an agent you do not override keeps its defaults. Files are staged flat into the rendered output,
so the build guide lists them by name.

For a source that is published and Bing-indexable, add its raw URL to `knowledge/sources.yaml` and
run `just update-knowledge` instead, which keeps it refreshable.

Agent Builder allows **20 uploaded files** per agent, and the renderer refuses more.

## Scoped web search cannot see your private documentation

This is the single most important thing to understand before pointing an agent at internal content.

> Web search enables agents to use **the search index in Bing** to respond to user prompts.
>
> Scoped web search relies on content that **Bing indexes** for the configured websites.
>
> [Knowledge sources](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/knowledge-sources), checked 2026-08-23

An intranet, an authenticated SharePoint site, or a private repository is not in Bing's index. If
you point `docs_url` at internal documentation and leave the capability as `WebSearch`, the agent
retrieves **nothing**, and then answers from model knowledge instead. It fails silently: generic
Terraform advice that looks plausible and is not your house standard.

Two related traps:

- **An admin can disable web search tenant wide.** When they do, "agents with web search enabled
  don't report an error and don't include web searches in their knowledge". The debug card still
  claims web search is on.
- **"Only use specified sources" does not fix it.** Agent Builder describes that toggle as
  prioritising your sources, and states plainly that it "doesn't support blocking general AI
  knowledge from your agent's responses". For a hard guarantee you need Copilot Studio.

The instruction fragments mitigate what they can: `shared/grounding.md` tells the agent to report
that a source returned nothing rather than quietly substituting its own knowledge, and to mark
unconfirmed claims `UNVERIFIED`. That is a behavioural mitigation, not a technical one. **The fix is
to give the agent a knowledge source that can actually reach your content.**

## Grounding an agent in private documentation

Knowledge source is a publisher decision, exactly like branding, so a profile can replace an
agent's capabilities:

```yaml
# profiles/acme.yaml
tokens:
  docs_url: contoso.sharepoint.com/sites/PlatformEngineering

agent_overrides:
  terraform-author:
    capabilities:
      - name: OneDriveAndSharePoint
        items_by_url:
          - url: https://contoso.sharepoint.com/sites/PlatformEngineering
```

The override replaces that agent's capabilities entirely and is per agent, so the others keep their
defaults. The renderer rejects an override naming an agent that does not exist, and the build guide
changes to tell you to add SharePoint rather than website URLs.

Pick the source that matches where your standards actually live:

| Your standards live in | Capability | Licence | Notes |
|---|---|---|---|
| A SharePoint site or OneDrive | `OneDriveAndSharePoint` | Copilot licence | Up to 100 SharePoint files, 50 OneDrive files. Respects each user's own permissions |
| Confluence, Jira, GitHub, ServiceNow, Azure DevOps | `GraphConnectors` | Copilot licence | An admin must configure the connector first. Several support scoping by project, space or repository |
| Loose documents you can upload | Uploaded files in Agent Builder | Copilot licence or metered usage | Up to 20 files. **Agent Builder only**: the `EmbeddedKnowledge` manifest capability is not available through the Agents Toolkit path |
| A genuinely public site | `WebSearch` | None | The only capability needing no licence |

Two consequences of permission-respecting sources worth planning for:

- The agent respects **the signed-in user's** permissions. Anyone you share it with who cannot open
  the underlying site gets no grounding from it, and no error explaining why.
- After changing a SharePoint knowledge source, **reshare the agent** so file permissions follow.

## Adding a tenant knowledge source

`OneDriveAndSharePoint` and `GraphConnectors` are tenant specific, so no useful default exists for a
public repository. To point an agent at your own content, add to the agent's `capabilities`:

```yaml
  - name: OneDriveAndSharePoint
    items_by_url:
      - url: https://contoso.sharepoint.com/sites/PlatformEngineering
```

Omitting both `items_by_url` and `items_by_sharepoint_ids` grants the agent **every** SharePoint and
OneDrive source in the organisation. Scope it deliberately.
