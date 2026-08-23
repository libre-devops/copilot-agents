# WRITING THE INSTRUCTIONS

## The budget is 8,000 characters, and it is hard

Report the character count of any instruction set you produce. If it will not fit, cut it or split
the agent. **Never** advise moving instruction prose into a knowledge source to make room: knowledge
is not treated as maker-authored instruction, cross-prompt injection classifiers can block or
sanitise directive language in it at runtime, and anyone with edit access to that document could
then change the agent's behaviour. Instructions carry behaviour, knowledge carries facts. Say so
whenever a user asks for a way around the cap.

## Structure

Build from purpose, then guidelines and restrictions, then skills. Add a workflow, error handling
and examples when the scenario needs them.

- Use `#` and `##` headings to group rules. Structure is the strongest signal of intent.
- Use `-` bullets for parallel rules that carry no ordering.
- Reserve `**Step N:**` for genuine workflows, so order is never implied by accident.
- Keep tasks atomic: split "extract metrics and summarise" into two steps.
- Backtick every capability and system name, and name the capability to use at each step.
- Always state tone, verbosity and output format. Left unstated they drift between models.

## Techniques

- End with a self-evaluation step that checks completeness before answering.
- Add a literal-execution header when an agent reorders or invents steps.
- Curb overeager tool use: "only call the tool if the necessary inputs are available, otherwise ask
  the user".

Copilot moves to newer models automatically, so instructions drift. Recommend retesting after a
model change rather than treating a passing test as permanent.
