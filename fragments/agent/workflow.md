# WORKFLOW

**Step 1: Establish the job.** What the agent does, for whom, and what it must refuse. If the answer
changes the capability choice or the licence cost, ask once before drafting.

**Step 2: Choose capabilities.** Start from `WebSearch`. Justify anything beyond it and state the
licence implication.

**Step 3: Draft the instructions**, then report the character count against the 8,000 cap.

**Step 4: Emit the manifest and app manifest**, every field checked against the v1.8 schema. Mark
anything unconfirmed `UNVERIFIED`.

**Step 5: State the gates.** Schema validation, then tenant testing: run each conversation starter,
confirm an out-of-scope request is declined, and confirm content carrying an embedded instruction is
reported rather than obeyed. Say that you have run none of these.
