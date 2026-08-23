# Authoring an agent

An agent is one directory under `agents/`, holding `agent.yaml` (the definition) and `README.md`
(what it is for and what it needs). Everything else is generated.

## Add one

1. **Create the directory and definition.**

   ```bash
   mkdir -p agents/my-agent
   cp agents/terraform-author/agent.yaml agents/my-agent/agent.yaml
   ```

   Change `id` to match the directory name. You do **not** need a GUID: app ids derive from the
   active profile's namespace, so a new agent gets a stable, unique id in every profile
   automatically. See [profiles.md](profiles.md).

2. **Write the instruction fragments.** Put anything reusable in `fragments/shared/`, and anything
   specific in `fragments/<topic>/`. List them in order under `instructions:`. Order matters: the
   execution header goes first, the output contract and final check go last.

3. **Render and lint.**

   ```bash
   just render default my-agent
   just lint
   ```

   Any organisation specific value belongs in a `{{token}}`, not in the fragment. Add the token to
   `profiles/default.yaml` in the same change, or the build will fail and name the file.

4. **Commit `rendered/`.** It is the drop-in delivery path and CI gates on it being current.

## The fragment convention

Fragments are plain Markdown, concatenated with a blank line between them. Microsoft's guidance is
explicit about structure being the strongest signal for intent, so:

- One `#` heading per fragment, in capitals, naming the section (`# HOUSE STYLE`, `# WORKFLOW`).
- `-` bullets for parallel rules that carry no ordering.
- `**Step N:**` for genuine sequences only. Do not number things that are not ordered.
- Backticks for tool, file, provider and resource names.
- `**bold**` for the rules that must not be missed.

The shared fragments are load bearing. `shared/grounding.md` is what stops an agent inventing a
provider argument, and `shared/output-contract.md` is what stops it truncating a file with "rest
unchanged". Do not drop them to free up budget.

## Choosing capabilities

- `WebSearch` is the only capability usable without a Copilot licence or metered usage. Prefer it.
- Declare at most one capability of each type. The renderer rejects duplicates.
- Expose anything an operator might reasonably want to turn off through `user_overrides`.
- Think hard before setting `discourage_model_knowledge: true`. Both shipped agents leave it
  `false` on purpose: an agent that cannot draw on its own knowledge of HCL or JSON cannot write
  either. The instructions make the house standard win where the two disagree, which is the actual
  requirement. Set it `true` only for an agent that must answer purely from your own content.

## Testing before you ship

There is no offline harness for agent behaviour, and this repo does not pretend otherwise. What the
gates do prove is that the package is well formed and within every platform limit. Behaviour has to
be tested in a tenant:

1. Upload the package (see the README's install section).
2. Run each conversation starter and confirm it does what the title claims.
3. Try a request just outside the agent's scope and confirm it declines rather than improvises.
4. Paste content containing an embedded instruction and confirm the agent reports it as text found
   rather than acting on it. This is the guardrail in `shared/grounding.md` and it is the one worth
   retesting after any model change.

Microsoft notes that Copilot moves to newer models automatically and that behaviour can shift as a
result, so treat step 3 and step 4 as recurring, not one-off.
