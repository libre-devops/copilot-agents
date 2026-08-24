# PowerShell Author

A **Microsoft 365 Copilot declarative agent** that writes and reviews PowerShell 7 to the
Libre DevOps PowerShell Standard and the `LibreDevOpsHelpers` house style.

It answers two kinds of question: **house style**, meaning how the helper module is written and how
to add to it, and **enterprise PowerShell in general**, meaning how to write PowerShell that is safe
to run unattended, in CI, against production. Where the two disagree the house standard wins and it
says so.

## What it enforces

- **Approved verbs, singular nouns, and the `Ldo` prefix on every exported noun.** The prefix is
  not decoration: it is what stops the module colliding with a built-in cmdlet on the same host.
- **`Set-StrictMode -Version Latest`** and an explicit `$ErrorActionPreference` at the top of every
  file, because strict mode turns a typo from a silent `$null` into an error.
- **`[CmdletBinding()]`, typed and validated parameters**, and `SupportsShouldProcess` on anything
  that changes state, actually gated on `ShouldProcess`.
- **Comment-based help on every exported function**, with a `.PARAMETER` for each parameter and at
  least one `.EXAMPLE`.
- **Objects, not `Write-Host`.** Host writes cannot be captured or piped, so they are never a way
  to return data.
- **Structured logging** with the canonical `TRACE` to `FATAL` vocabulary and OpenTelemetry
  severity numbers, seeded from the environment so CI can change logging without touching code.
- **Terminating versus non-terminating errors**, which is the distinction most scripts get wrong.
- **Secrets** never in a script, a parameter default or a committed file.
- **PSScriptAnalyzer and Pester**, named as blocking gates, with the agent stating plainly that it
  has not run them.

## Knowledge

The Libre DevOps PowerShell Standard, uploaded. Scoped web search covers Microsoft Learn's
PowerShell and Azure documentation and the PowerShell Gallery.

## Rebranding

The prefix and module name are **profile tokens**, not literals: `cmdlet_prefix` and
`ps_module_name`. `just new-profile` derives both from your organisation name, so `ACME` gets
`Invoke-AcmeTerraformPlan` in `AcmeHelpers` without editing a fragment. Override them in the
profile if your module is named differently.

## Testing it

1. Ask for a new function and confirm it emits strict mode, help, typed parameters and the prefix.
2. Ask it to review PowerShell that uses `Write-Host` to return data and confirm it catches it.
3. Ask something with no house position and confirm it says so rather than inventing a rule.
