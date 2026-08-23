# The instruction budget

Declarative agent schema 1.8 caps `instructions` at **8,000 characters**. That cap is the single
constraint that shapes this repository.

## Why you cannot route around it

The obvious workaround is to put the long-form standard in a SharePoint document or another
knowledge source and tell the agent to follow it. Microsoft's own guidance says not to, and the
reasoning is not stylistic:

> Don't store or offload declarative agent instructions in SharePoint documents (or any other
> knowledge source) to work around the 8,000-character instruction limit. Knowledge source content
> is not trusted maker-authored instruction content and is subject to cross-prompt injection
> attacks (XPIA) classifiers: directive-like language can be blocked, truncated, or sanitized at
> runtime, causing unpredictable agent behavior.
>
> [Write effective instructions for declarative agents](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-instructions), checked 2026-08-23

Three consequences follow, and they are the reason for the split in this repo:

1. **Instructions carry behaviour.** Rules, workflow, output contract, refusals. Maker-authored,
   version controlled, budget enforced.
2. **Knowledge carries facts.** Schemas, reference documentation, connector lists. Grounding for
   claims, never a source of directives.
3. **Anyone with edit access to a knowledge document could otherwise change agent behaviour at
   runtime**, bypassing this repository's review entirely. Keeping directives out of knowledge
   keeps the manifest the only place behaviour is defined.

## How the budget is enforced

`tools/render.py` concatenates the fragments listed in an agent's `agent.yaml`, measures the
result, and **fails the build** if it exceeds 8,000 characters. It never truncates, because a
silently truncated instruction set is an agent whose output contract has quietly vanished.

Every render prints the spend:

```
  agent-author:     instructions 7144/8000 (89%), 4 files
  logic-app-author: instructions 6799/8000 (84%), 4 files
  terraform-author: instructions 6225/8000 (77%), 4 files
```

`tools/lint.py` warns at 7,200 characters (90 percent), so a change that eats the last of the
headroom is visible in review before the next change fails the build.

## Spending it well

The current split is roughly 2,300 characters of shared fragments plus 3,900 to 5,100 per agent.
`agent-author` is the tightest at 89 percent, because it carries reference facts rather than only
rules, and it was cut twice during authoring to get there. When you run out:

- **Cut prose before you cut rules.** Microsoft's guidance is to focus on what the agent should do
  rather than what to avoid, so a rule phrased as a positive instruction is usually shorter.
- **Move a fact to knowledge.** "Confirm the argument exists" is behaviour and belongs in
  instructions. The list of arguments is a fact and belongs in a knowledge source.
- **Split the agent.** Two focused agents each with 8,000 characters beat one agent trying to be
  both. The `worker_agents` property exists for exactly this, though note it is in preview.
- **Drop a shared fragment only on its merits, never for budget.** `agent-author` omits
  `shared/literal-execution.md` because a header saying "never infer intent" fights an agent whose
  job is turning a vague brief into a design. That is a design argument that happens to save space,
  not the other way round. Never drop `grounding.md`, which is what stops the agent inventing
  provider arguments.
