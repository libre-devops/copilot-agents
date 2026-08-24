# Azure Infra Consultant

A **Microsoft 365 Copilot declarative agent** that designs and reviews Azure infrastructure to the
Libre DevOps standards.

## Why it is not a generic Azure chatbot

Copilot already knows Azure. What it does not know is **your** position, and that is what this agent
carries:

- **Check for a house module before proposing raw resources.** Libre DevOps publishes over a hundred
  Terraform modules. The agent names one when it exists, and says so plainly when it cannot confirm
  one does, rather than inventing an address that will not resolve.
- **Managed identity, then OIDC, then nothing.** A stored client secret is a finding, not a design.
- **Private by default, and honest about what that breaks.** A deployment-package storage account
  still has to be writable by whatever runs the deployment, and a trusted-services bypass does not
  cover a build agent. The agent names the principals that need a path in.
- **Names built inside the module** from structured inputs so a caller cannot drift them; tags
  constructed once and merged, never per resource.

## The two rules that matter most

**Name the trade.** Every design is assessed against the five Well-Architected pillars, and the
agent must say which ones it traded away. A recommendation claiming all five are satisfied is
usually one that has not been thought about.

**Never quote a price.** Azure pricing is regional, changes without notice, and depends on
commitments the agent cannot see. It states the cost **model**: what the meter is, what drives it,
and which design choice moves it, then points at the pricing calculator. A confident wrong number is
worse than no number, because someone will budget against it.

It also separates three failures people collapse into one word: zone redundancy, region pairing and
backup answer an instance dying, a region failing, and someone deleting the data. The agent says
which of the three a design actually covers.

## Knowledge

| File | Why |
|---|---|
| `terraform-standards.txt` | how infrastructure gets built here |
| `azure-naming-convention.txt` | the naming and tagging position |
| `cicd-standards.txt` | how it ships, and where correctness is pushed left |
| `caf-landing-zone-design-areas.txt` | the vendor's structure around the house opinion |
| `caf-resource-naming.txt`, `caf-resource-abbreviations.txt` | the abbreviations the convention builds on |

**The Well-Architected Framework is deliberately not a knowledge pack.** It has no reliable public
markdown mirror; the one that exists is a 2019 archive. So the five pillars live in the instructions
as a review lens and the detail comes from scoped web search against the live pages. Shipping a
stale archive as authoritative would have been worse than not shipping it.

## Testing it

1. Ask for something a house module covers and confirm it names the module rather than the resources.
2. Ask "what will this cost" and confirm it gives the model and refuses the number.
3. Ask for a design and confirm it names a trade-off rather than claiming all five pillars.
4. Ask for a service that does not exist and confirm it says so instead of inventing one.
