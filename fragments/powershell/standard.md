# THE STANDARD

## Every file starts the same way

`Set-StrictMode -Version Latest` and an explicit `$ErrorActionPreference`. Strict mode turns a typo
in a variable name from a silent `$null` into an error, which is the single highest-value line in
an unattended script.

## Naming

- **Approved verbs only.** `Get-Verb` is the list. `Get`, `Set`, `New`, `Remove`, `Invoke`,
  `Test`, `Assert`, `Write`. Never invent one, never use an alias in a script.
- **Every exported noun carries the `{{cmdlet_prefix}}` prefix**: `Write-{{cmdlet_prefix}}Log`,
  `Invoke-{{cmdlet_prefix}}TerraformPlan`, `Assert-{{cmdlet_prefix}}Command`. This is not decoration:
  it is what stops the module colliding with a built-in cmdlet or another module on the same host.
- Singular nouns. `Get-{{cmdlet_prefix}}Module`, not `Get-{{cmdlet_prefix}}Modules`.

## Functions

- `[CmdletBinding()]` on every function, so it gets `-Verbose`, `-Debug` and `-ErrorAction` free.
- **Typed, validated parameters.** `[string]`, `[int]`, `[switch]`, with `[ValidateSet]`,
  `[ValidateNotNullOrEmpty]` or `[ValidatePattern]` where the constraint is real. A validation
  attribute fails at bind time with a clear message; an `if` inside the body fails later and worse.
- Support `-WhatIf` and `-Confirm` through `SupportsShouldProcess` on anything that changes state,
  and actually gate the change on `$PSCmdlet.ShouldProcess(...)`.
- **Comment-based help on every exported function**: `.SYNOPSIS`, `.DESCRIPTION`, `.PARAMETER` for
  each parameter, and at least one `.EXAMPLE`. This is the module's documentation.

## Output and logging

- **Emit objects, not text.** Return typed objects the caller can filter and sort. `Write-Host`
  writes to the host and cannot be captured or piped: never use it to return data.
- Structured logging through the house logger, with the canonical levels `TRACE`, `DEBUG`, `INFO`,
  `SUCCESS`, `WARN`, `ERROR`, `FATAL`, and OpenTelemetry severity numbers. Configuration is seeded
  from the environment (`{{brand_short}}_LOG_LEVEL`, `{{brand_short}}_LOG_FORMAT`) so CI can change
  logging without touching code.
- Never log a secret, a token or a connection string. Redact before it reaches a log line.

## Errors

- Know which you are raising. `throw` and `-ErrorAction Stop` are terminating and can be caught;
  `Write-Error` alone is not and the script carries on.
- `try`/`catch`/`finally` around anything external, catching the specific exception where you can.
  `finally` for cleanup that must happen whatever failed.
- **Fail fast on a missing dependency**, before doing any work, rather than half way through.

## Secrets

Never a plaintext credential in a script, a parameter default, or a committed file. Use
SecretManagement, Key Vault or a CI secret, and prefer a managed identity or OIDC over any secret
at all.

## Gates

`PSScriptAnalyzer` against the repository's settings file, and `Pester` tests for every exported
function. Both run in CI, and both are blocking.
