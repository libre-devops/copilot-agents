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
