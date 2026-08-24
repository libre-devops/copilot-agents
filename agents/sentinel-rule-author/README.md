# Sentinel Rule Author

A **Microsoft 365 Copilot declarative agent** that writes and reviews Microsoft Sentinel analytics
rules, and understands the platform they sit in.

## Why it knows about the whole platform, not just the rule form

Most rule problems are really problems with the link either side of the rule. A rule that fires
constantly is usually a grouping or threshold problem, not a query problem. A rule nobody can
investigate is usually a missing entity mapping. A rule that misses events is usually a schedule
that does not match the source's ingestion delay.

So the agent carries the pipeline: **connectors** ingest into **tables**, **analytics rules** run
KQL and raise **alerts**, alerts become **incidents**, **entities** are what correlates them and
what an analyst pivots on, **automation rules** fire on incident or alert events and call
**playbooks**, **watchlists** hold reference data, **UEBA** adds baselines.

It also knows two platform facts that change answers:

- **Sentinel is Defender-portal only after 31 March 2027**, and many new customers are already
  onboarded there. On a Defender-onboarded workspace, Defender XDR creates and names incidents, the
  Microsoft Security rule type is auto-disabled, and reopening closed incidents is unavailable.
- **Prefer an ASIM parser over a native table**, so a rule survives a change of data source.

## The limits it enforces

Hard platform limits, quoted rather than approximated:

| | |
|---|---|
| Query | 1 to 10,000 characters. `search *` and `union *` are **rejected**, not just slow |
| Schedule | interval and lookback both 5 minutes to 14 days, **interval must be ≤ lookback** |
| Delay | scheduled rules run on a 5 minute ingestion delay; NRT every minute on 2 minutes, querying ingestion time |
| Entity mapping | 10 mappings, 3 identifiers each, at least one **required** identifier |
| Entities per alert | 500, divided equally across mappings; the field caps at 64 KB and truncates |
| Event grouping | alert per row caps at 150: the first 149 individual, the 150th summarising |
| Alert grouping | 150 alerts per incident, window default 5 hours, range 5 minutes to 7 days |
| Suppression | up to 24 hours |

**A rule with no entity mapping is treated as a defect**, not a stylistic preference. It produces an
incident nobody can pivot from.

## Knowledge

Ten uploaded packs: the Sentinel overview and rule-type pages for the platform model, the scheduled
and NRT rule pages for the settings, entity mapping and the entities reference, custom details,
automation rules, and the Kusto best practices, because a rule query runs on a schedule and its cost
is recurring.

Note that Sentinel documentation now lives in the `defender-docs` mirror rather than `azure-docs`,
which is itself a signal of where the product is going.

## Testing it

1. Ask for a rule and confirm it maps entities without being asked.
2. Give it a rule with a lookback shorter than the interval and confirm it catches the coverage gap.
3. Ask for a query containing `union *` and confirm it says the platform rejects it.
4. Ask "should this be scheduled or NRT" for a source with a long ingestion delay, and confirm it
   rules out NRT for the right reason.
