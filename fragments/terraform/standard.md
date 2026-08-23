# THE STANDARD

## File split is the contract

A reusable module is `main.tf` (resources only), `variables.tf` (all inputs), `outputs.tf` (all
outputs), `terraform.tf` (`required_version` and `required_providers` only), `README.md`, and
`examples/complete/`. Add `locals.tf`, `data.tf`, `moved.tf` and `tests/*.tftest.hcl` when needed.
Never declare a variable in `main.tf` or a resource in `variables.tf`.

A workspace root adds `providers.tf`, `backend.tf`, gitignored `override.tf`, and `env/*.tfvars`.
**Provider blocks live in the workspace root only, never in a reusable module.**

## Resources

- Label a single resource of a type `this`. Qualify by role only when the same type appears more
  than once. Never echo the type in the label (`azurerm_resource_group.this`, not `.resource_group`).
- Use `for_each` over a map for any named collection. Use `count` only for "create or not".
- Argument order inside a block: meta-arguments (`for_each`, `count`, `provider`), blank line,
  required arguments, optional arguments, `dynamic` blocks, then `lifecycle` last.
- Do not null-check a value declared with `optional(type, default)`. It cannot be null.
- Use `dynamic` blocks to omit optional nested blocks entirely rather than emitting empty ones.

## Variables and outputs

- Every input needs a `description` and an explicit `type`. Required inputs carry no `default`.
- Encode hard platform constraints as `validation` blocks. Use `check` blocks for softer,
  post-apply assertions that should warn rather than block.
- Model multi-resource inputs as `list(object)` or `map(object)` with `optional()` defaults.
- Preserve the `for_each` key structure in map outputs. Mark credentials `sensitive = true`.

## Providers

- Pin `required_version` and every provider version in `terraform.tf`.
- Prefer `azurerm`. Reach for `azapi` only where `azurerm` does not model the resource, and write
  a comment saying why. Use `azuread` for Entra objects and `msgraph` only as the escape hatch.
- Authenticate with OIDC. Never commit credentials or a `.tfvars` file containing secrets.

## Naming

Construct names as `${prefix}-${infix}-${outfix}-${suffix}[-${optional}][-${numbering}]`, all lower
case: CAF type abbreviation, 2 to 4 letter product code, region code (`uks`, `euw`), environment
(`dev`, `tst`, `prd`), optional qualifier, zero-padded ordinal. Resource types that forbid hyphens
(storage accounts, VMs) drop the dashes: `saldouksprd001`. Build the name inside the module from
structured inputs so callers cannot override it ad hoc.
