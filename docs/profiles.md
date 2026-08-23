# Branding profiles

An agent has two separable halves: what it **does**, and who **publishes** it. Fragments and agent
definitions own the first. A profile owns the second.

That split is what lets you take this repository, point it at your own organisation, and ship the
same three agents under your own name without editing a single fragment, and without your
organisation's details ever appearing in a public commit.

## Publishing under your own brand

```bash
uv run just new-profile acme     # asks for each value, Enter accepts the default
uv run just package acme         # writes dist/acme/<agent>-<version>.zip
```

Two commands. `new-profile` prompts for the organisation name, the URLs, the colour and the version,
each with a default, so you can hold Enter and still get a profile that renders, packages and lints.
Placeholder URLs sit on `example.invalid`, which RFC 2606 reserves so it can never resolve: an
unedited value is then obvious in review rather than quietly wrong. Agent Builder does not check
those URLs, so a placeholder is fine there; replace them before publishing an app package.

Add `--defaults` (or use `just new-profile-quick`) to skip the questions entirely. The rendered manifests land in `build/acme/`, the uploadable packages in
`dist/acme/`, and both are gitignored.

## Your profile will not be committed by accident

`.gitignore` allowlists profiles rather than denylisting them:

```gitignore
profiles/*
!profiles/default.yaml
!profiles/example.yaml
!profiles/README.md
```

A profile you create is ignored unless someone deliberately adds an exception. `build/` and `dist/`
are ignored outright, so a rendered internal package cannot be committed either. If you intend to
publish a profile, adding the exception is a conscious act that shows up in review.

## What a profile contains

```yaml
id: acme

# Substituted wherever {{token}} appears, in fragments and in agent definitions alike.
tokens:
  brand_short: ACME          # uppercase prefix, e.g. "ACME Terraform Author"
  brand_name: Acme Corp      # full organisation name, used in prose
  brand_infix: acm           # lower case product code used inside generated resource names
  registry_url: registry.terraform.io/namespaces/acme
  docs_url: docs.acme.example/standards

publisher:                   # becomes developer{} in the app manifest, all four required
  name: Acme Corp            # 32 characters maximum
  website_url: https://acme.example
  privacy_url: https://acme.example/privacy
  terms_url: https://acme.example/terms

package:
  version: 1.0.0
  accent_color: "#2563EB"    # also the colour of the generated icons

app_id_namespace: <guid>     # ids derive from this, so they are unique per publisher and stable
app_ids: {}                  # optional explicit overrides, keyed by agent id
```

Every `_url` under `publisher` must be HTTPS and must resolve: they are required fields that store
validation checks. The renderer refuses a profile that gets any of this wrong.

## Tokens

Tokens are a free-form map, so add your own whenever a fragment needs a value that differs between
publishers. Two rules keep them safe:

- **The renderer fails on an unresolved placeholder.** If a fragment uses `{{thing}}` and your
  profile has no `thing`, the build stops and names the file. A typo cannot ship.
- **The linter warns on brand leakage.** When you lint a non-default profile, any value from the
  default profile's tokens that survives into your output is reported. That is how the `ldo`
  product infix inside `saldouksprd001` was caught: it is not the word "Libre DevOps", so nothing
  else would have noticed it.

Quote any YAML value that *begins* with `{{`, otherwise the brace reads as a flow mapping:

```yaml
name: "{{brand_short}} Terraform Author"    # quoted, because it starts with a brace
short_description: Writes Terraform to the {{brand_name}} standard.   # fine unquoted
```

## Overriding knowledge

A profile can swap which documents an agent is grounded in, so your standards never collide with
upstream ones:

```yaml
agent_overrides:
  terraform-author:
    knowledge_files:
      - our-terraform-standard.txt
```

Put the files in `knowledge/`, or declare their URLs in `knowledge/sources.yaml` and run
`just update-knowledge`. See [knowledge.md](knowledge.md).

## Overriding capabilities

Branding is not the only publisher-specific thing. **Knowledge source is too.** A public agent uses
scoped `WebSearch`, which reads only what Bing indexes, so an organisation grounding the same agent
in internal documentation has to swap the capability:

```yaml
agent_overrides:
  terraform-author:
    capabilities:
      - name: OneDriveAndSharePoint
        items_by_url:
          - url: https://contoso.sharepoint.com/sites/PlatformEngineering
```

This replaces that agent's capabilities entirely, and only that agent's. A profile naming an agent
that does not exist is rejected, so a rename upstream cannot leave your override silently doing
nothing. The generated build guide follows the override, telling you to add SharePoint sources
rather than website URLs.

The instruction fragments deliberately never name a specific capability, so swapping the source does
not invalidate them. See [knowledge.md](knowledge.md) for choosing the right one.

## App ids

Two publishers must never share an app id, and an id must stay stable across renders or every
install breaks. So ids derive as `uuid5(app_id_namespace, agent_id)`:

- Adding an agent needs no manual GUID. It gets a stable id in every profile automatically.
- Two profiles cannot collide, because their namespaces differ.
- The renderer checks every agent's id across the whole set, even when you render one agent, so a
  collision cannot hide.

`app_ids` overrides the derivation for a specific agent. The default profile uses it to preserve the
ids issued before profiles existed, so existing installs kept working.

## Output routing

| Profile | Manifests | Packages | Committed |
|---|---|---|---|
| `default` | `rendered/` | `dist/` | yes, and drift gated in CI |
| anything else | `build/<profile>/` | `dist/<profile>/` | no, gitignored |

`--check` is the drift gate for `rendered/`, so it applies to the default profile only and refuses
any other. Use `just check <profile>` to render and lint one of your own.

## Keeping up with upstream

Your profile is a single file that upstream never touches, so pulling new agents and fixes is a
plain `git pull` followed by `just package <profile>`. Nothing to reapply, nothing to merge.
