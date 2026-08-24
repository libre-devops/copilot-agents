# THE CRAFT

## Correctness traps that return a plausible wrong answer

These are the ones that pass review and mislead an investigation.

- **`join` defaults to `kind=innerunique`, which deduplicates the LEFT side.** Rows disappear
  silently. State the kind on every join: `inner` for a standard inner join, `leftouter` when the
  left side must survive, `leftanti` for absence.
- **`==` is case sensitive, `=~` is not.** Usernames, hostnames, file paths and command lines
  arrive in mixed case. Choose deliberately and say which you chose.
- **`has` matches whole terms, `contains` matches substrings.** They are not interchangeable:
  `has "svc"` will not match `svchost.exe`, and `contains "svc"` will.
- **Timestamp columns differ by table.** Confirm the name from the schema rather than assuming
  `TimeGenerated`; Defender XDR tables mostly use `Timestamp`.
- **`arg_max(Timestamp, *)`** takes the latest row per key. A bare `summarize` gives aggregates,
  not the record.

## Performance, in the order the engine cares about

1. **Filter on the datetime column FIRST**, immediately after the table reference. Kusto indexes
   datetime and eliminates whole shards unread. Nothing else saves as much.
2. Then term-level `string` and `dynamic` predicates, **most selective first**.
3. Then numeric predicates, then anything that has to scan.
4. **`has` over `contains`. `==` over `=~`. `in` over `in~`.** Case-sensitive and term-indexed
   operators are cheaper.
5. **Never `search *`**, and avoid `union *`. Both read every column or every table.
6. **Filter on a table column, not a calculated one.**
7. **The smaller table goes on the LEFT of a join.** For filtering on a single column, `in` beats
   a `leftsemi` join.
8. **`project` early** to drop columns you will not use, and `materialize()` a `let` you reference
   more than once.
9. For a rare value in a dynamic column, filter with `has` before parsing:
   `where Col has "rare" | where Col.Key == "rare"`.
10. **Put `limit` or `count` on an exploratory query.** Unbounded over an unknown dataset is how
    you fill the console and the cluster.

## Hunting output

- **Project the entities**, not everything: account, device, hash, IP, process. A result nobody can
  pivot from is a dead end.
- Include the timestamp and a stable identifier on every row so a finding can be reproduced.
- Say what a **true positive would look like** in the result set, and what the expected noise is.
- Map the hypothesis to **MITRE ATT&CK** technique ids where you can, and say when you cannot.
