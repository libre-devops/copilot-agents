# THE RULE, AND ITS LIMITS

Every one of these is a hard platform limit. Quote them rather than approximating.

## Query

- **1 to 10,000 characters.** Use a user-defined function to get under it rather than cutting logic.
  `search *` and `union *` are **rejected**, not merely slow.
- Guard `bag_unpack` projections with `column_ifexists("field","")` or the query fails when the
  column is absent.

## Scheduling

- **Run every** and **look up data from the last** both range **5 minutes to 14 days**.
- **Interval must be shorter than or equal to lookback.** Shorter means overlap and duplicate
  results; longer is rejected because it leaves coverage gaps. Say which you chose and why.
- Scheduled rules run on a **five minute ingestion delay**. NRT rules run every minute on a **two
  minute** delay and query on **ingestion time**, not `TimeGenerated`.

## Entity mapping, the part that decides whether an incident is investigable

- Up to **10 entity mappings** per rule, **3 identifiers** each, **at least one required identifier**
  per mapping. Prefer strong identifiers, and more than one where you can.
- Up to **500 entities per alert**, divided equally across mappings: 2 mappings means 250 each. The
  entities field caps at **64 KB** and truncates beyond it.
- **A rule with no entity mapping produces an incident nobody can pivot from.** Treat a missing
  mapping as a defect, not a preference.

## Alerts and incidents

- **Alert threshold** applies per run, not cumulatively.
- **Event grouping** is either one alert summarising everything (the default) or one alert per row.
  Per row caps at **150 alerts**: the first 149 are individual and the 150th summarises the lot.
- **Alert grouping** puts up to **150 alerts** in one incident, over a window defaulting to **5
  hours**, settable from 5 minutes to 7 days. **All mapped entities matching** is the recommended
  criterion; grouping everything from the rule into one incident hides distinct attacks.
- **Suppression** stops the query up to **24 hours** after an alert.

## Always set

**Severity** with a reason, and **MITRE ATT&CK tactics and techniques**, which propagate to the
incident. An unmapped rule is invisible in coverage reporting.
