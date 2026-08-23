# LDO Terraform Author

Writes and reviews Terraform to the
[Libre DevOps Terraform Standard](https://libredevops.org/docs/documents/terraform-standards/) and
the [Azure Naming Convention](https://libredevops.org/docs/documents/azure-naming-convention/).

## What it enforces

- The file split as the contract: `main.tf` holds resources only, `variables.tf` holds inputs only.
- `this` as the resource label, qualified by role only when a type repeats.
- `for_each` over a map for named collections, `count` only for "create or not".
- Argument order: meta-arguments, blank line, required, optional, `dynamic`, `lifecycle` last.
- Typed variables with `description`, `validation` for hard constraints, `check` for soft ones.
- Pinned `required_version` and provider versions, `azurerm` preferred and `azapi` justified.
- Names built inside the module from structured inputs, so callers cannot override them ad hoc.

## Knowledge

`WebSearch`, scoped to four sites: the Libre DevOps standards, the HashiCorp language reference,
the Libre DevOps registry namespace, and Microsoft Learn's Azure documentation. No tenant resources
are required, so this agent works without a Copilot licence.

## What it will not do

It does not run `terraform`. It emits code and then tells you which gates to run
(`fmt`, `validate`, `tflint`, `terraform test`, `trivy`), and states plainly that it has not run
them. If it cannot confirm an argument from a cited source it marks it `UNVERIFIED` rather than
guessing.

## Install

See the [repository README](../../README.md#install-an-agent). The package is
`dist/terraform-author-0.1.0.zip`, built with `just package`.
