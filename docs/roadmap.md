# Roadmap

What is planned, what is blocked, and what is blocked **on the platform** rather than on effort. The
last distinction matters: several obvious ideas here are not possible today, and it is more useful to
say why than to leave them looking like a backlog nobody got to.

Nothing here is a commitment or a date.

## Near term

- **More agents.** This is a collection, and Terraform and Logic Apps are where it started. Likely
  next: KQL and Sentinel analytics rules, PowerShell to the Libre DevOps standard, Bicep, and a
  reviewer agent that only critiques and never writes.
- **Real branding assets.** The icons are a generated chevron on the profile's accent colour. They
  are honest placeholders, not a designed mark.
- **A behaviour test pack.** The gates prove a package is well formed and inside every limit. They
  cannot prove an agent behaves. A written pack of cases per agent (a correct answer, a refusal, an
  injection attempt) would at least make manual tenant testing repeatable and reviewable, in the
  spirit of the eval harness in `security-copilot-agents`.
- **Instruction budget reporting in CI.** The render already prints the spend. Surfacing it as a
  pull request comment would make a change that eats the last of the headroom visible before merge.

## Deploying agents as infrastructure as code

The obvious question, and the honest answer is **not properly, and the blocker is authentication
rather than tooling**.

### What exists

Microsoft Graph does have a publish API:

```http
POST https://graph.microsoft.com/v1.0/appCatalogs/teamsApps
Content-Type: application/zip

[the app package zip]
```

It publishes to the organisation's catalog, validates the manifest and returns detailed schema
errors, and `?requiresReview=true` routes it through admin approval. Updates go to
`POST /appCatalogs/teamsApps/{id}/appDefinitions`, and an admin approves a pending app with a
`PATCH` on the app definition's `publishingState`.

So an automated deployment path is not imaginary. Three things stop it being Terraform.

### Blocker 1: application permissions are not supported

From the [teamsApp publish reference](https://learn.microsoft.com/en-us/graph/api/teamsapp-publish),
checked 2026-08-23:

| Permission type | Least privileged | Higher privileged |
|---|---|---|
| Delegated (work or school) | `AppCatalog.Submit` | `AppCatalog.ReadWrite.All`, `Directory.ReadWrite.All` |
| Application | **Not supported** | **Not supported** |

That single row is the whole problem. No application permission means no service principal, no
federated OIDC workload identity, and therefore no unattended pipeline. Every call needs a signed in
user's token. A "deployment" that requires a human to authenticate interactively is not
infrastructure as code, whatever it is wrapped in.

Note also that `AppCatalog.Submit` only submits for review. Actually publishing needs
`AppCatalog.ReadWrite.All`, which is a broad tenant-wide grant worth thinking about before anyone
puts it on a shared identity.

### Blocker 2: the Terraform provider cannot send the request

The [`microsoft/msgraph`](https://registry.terraform.io/providers/microsoft/msgraph/latest) provider
is a thin wrapper over the Graph REST API, and `msgraph_resource` takes a `url` and a structured
`body` that is serialised as JSON:

```hcl
resource "msgraph_resource" "application" {
  url  = "applications"
  body = { displayName = "My Application" }
}
```

The publish endpoint needs a raw `application/zip` body. There is no binary body and no
Content-Type override, so the provider cannot express the call at all, regardless of authentication.
The same is true of `azuread`, which models no `teamsApp` resource.

### Blocker 3: Agent Builder agents are a different thing

An agent created in Agent Builder is backed by the Copilot Studio service, not by an app package you
own. It is shared by link or listed in the Agent Store, and the only export is a one way
**Download .zip file**. There is no create or update API to point automation at.

### What you could actually do, and why we have not

A `null_resource` with a `local-exec` calling `az rest` or `New-MgAppCatalogTeamApp` against a
delegated token would work. It would also be a shell script in a Terraform costume: no plan, no
diff, no drift detection, and state that lies the moment an admin changes something in the portal.
That is worse than an honest script, because it looks like infrastructure as code to the next person
reading it.

The same discipline applies here as in `security-copilot-agents`: the tooling ends where the
platform's API ends, and says so. What this repository does instead is make the artefact perfectly
reproducible (`just package`, drift gated, sha256 in `rendered/inventory.json`) so that the manual
step is a single upload of a known-good file, not a person hand-editing a form.

### What would change the answer

Any one of these, in rough order of likelihood:

1. **Application permission support on `POST /appCatalogs/teamsApps`.** This alone would make a CI
   publish job practical today, with a small script and no provider changes.
2. **Binary body support in `msgraph_resource`.** Combined with the above, a real
   `msgraph_resource` publishing an agent becomes possible, and this repository would grow a
   Terraform module to do it.
3. **A first-class declarative agent resource** in the msgraph or Power Platform providers.

If the first one ships, wire it into a new `just publish <profile>` recipe and delete this section.
Until then, `docs/platform-notes.md` records the seam.

## Platform dependent

Wired up and waiting on Microsoft, not on us:

- **`EmbeddedKnowledge`.** Fully supported by the renderer behind `--with-embedded-knowledge`, off by
  default because the 1.8 reference states embedded files are not enabled yet. Flip the default when
  that changes.
- **Actions and API plugins.** In the manifest schema (1 to 10 per agent) but not available in Agent
  Builder, which is the path most people use. An agent needing actions belongs in Copilot Studio
  today.
- **`worker_agents`.** In preview. Splitting a large agent into a coordinator plus workers is the
  documented answer to the 8,000 character cap, and worth revisiting once it is generally available.

## Explicitly not planned

- **A hosted or SaaS version.** This is a repository of definitions, not a service.
- **Bypassing the instruction budget.** Offloading instruction prose into a knowledge source is a
  documented antipattern with a real security consequence. See
  [instruction-budget.md](instruction-budget.md).
- **Vendoring the standards.** The agents cite `libredevops.org` rather than embedding a copy that
  would rot. A profile repoints that with one token.
