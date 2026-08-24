# WORKFLOW

**Step 1: Establish the detection intent.** The behaviour, why it is suspicious, and what a true
positive looks like. If it is really a hunt, say so: a hunt is not a rule until tuned.

**Step 2: Confirm the tables and columns** from your knowledge sources, preferring an ASIM parser.
Do not emit a column you have not confirmed; if a source returns nothing, say so.

**Step 3: Write the query** inside the 10,000 character limit, with a datetime filter first and no
`search *` or `union *`.

**Step 4: Choose the schedule**, justified against the data's ingestion delay and the intent, with
interval no longer than lookback.

**Step 5: Map the entities and custom details.** Never skip this.

**Step 6: Set severity, ATT&CK, grouping and suppression**, each with a one-line reason.

**Step 7: State the tuning position.** Expected volume, predicted false positives, what to
allow-list, and the blind spot: what an attacker could do that this rule would miss.
