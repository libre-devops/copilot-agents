# KQL Hunt Author

A **Microsoft 365 Copilot declarative agent** that writes and reviews threat hunting KQL for
**Microsoft Defender XDR advanced hunting** and **Microsoft Sentinel**.

## The problem it solves

The query language is shared between the two products. **The schemas are not.** A hunt written
against the wrong table set does not error helpfully: it returns nothing, and an empty result looks
identical to a clean environment. So the agent names the target product before it writes anything,
and asks if the request does not say.

It also separates two artefacts people conflate. A **hunt** explores and may be noisy on purpose. A
**detection** runs unattended and pages someone. The agent says which it is writing and refuses to
hand over an untuned hunt as if it were a rule.

## The correctness traps it enforces

These are the ones that pass review and then mislead an investigation:

| Trap | Why it bites |
|---|---|
| **`join` defaults to `kind=innerunique`** | It deduplicates the **left** side. Rows vanish silently. The agent states the kind on every join |
| `==` versus `=~` | Usernames, hostnames and command lines arrive in mixed case |
| `has` versus `contains` | `has "svc"` does **not** match `svchost.exe`; `contains` does |
| Timestamp column names | Defender XDR mostly uses `Timestamp`, not `TimeGenerated` |
| `arg_max(Timestamp, *)` | A bare `summarize` gives aggregates, not the record |

## Performance, in engine order

Datetime filter first, immediately after the table reference, because Kusto indexes datetime and
eliminates whole shards unread. Then term-level string predicates, most selective first. Then
`has` over `contains`, `==` over `=~`, `in` over `in~`. Never `search *`. Smaller table on the left
of a join. `project` early, `materialize()` a reused `let`, and `limit` on anything exploratory.

## Knowledge

Uploaded, because a query referencing a column that does not exist returns a clean-looking nothing:

| File | What it carries |
|---|---|
| `kql-cheatsheet.txt`, `defender-xdr-cheatsheet.txt` | the house cheatsheets |
| `kql-best-practices.txt` | the authoritative performance ordering |
| `kql-join-operator.txt` | the join flavours and the `innerunique` default |
| `xdr-hunting-schema.txt` | the Defender XDR advanced hunting tables and columns |
| `xdr-hunting-best-practices.txt`, `xdr-hunting-limits.txt` | hunting guidance and quotas |

Refresh with `just update-knowledge`.

## Testing it

1. Ask for a hunt without saying which product, and confirm it asks rather than guessing.
2. Give it a query using a bare `join` and confirm it flags `innerunique` and the lost rows.
3. Ask it for a column that does not exist and confirm it says the source returned nothing rather
   than inventing one.
4. Ask it to promote a hunt to a detection and confirm it lists tuning, entity mapping and ATT&CK
   rather than just handing the query back.
