# WORKFLOW DEFINITION LANGUAGE

## Identify the wrapper first

A definition arrives in one of three shapes. A bare definition has no top level `definition` or
`properties` key, so the unwrap is unambiguous.

- Bare: `{ "$schema": ..., "triggers": {...}, "actions": {...} }`
- Portal code view: `{ "definition": {...}, "parameters": {...} }`
- ARM resource GET: `{ "properties": { "definition": {...} }, "id": ..., "name": ... }`

State which shape you were given and which you are returning.

## Parameters: declarations versus values

Both blocks are called `parameters`. Inside `definition.parameters` they are DECLARATIONS (type,
optional `defaultValue`). At the top level they are VALUES (`{ "name": { "value": ... } }`). A
declaration with neither a value nor a `defaultValue` is rejected at **deploy** time.

## Action names are keys

The designer displays `SNOW - Find ticket` but stores `SNOW_-_Find_ticket`. Spaces become
underscores, and every reference uses the stored key: `@body('SNOW_-_Find_ticket')`. Renaming an
action means moving every reference. Nothing validates this at save time; it fails at run time.

## Control flow

Actions nest: `Scope`, `Foreach` and `Until` hold `actions`; `If` holds `actions` and `else.actions`;
`Switch` holds `cases.<name>.actions` and `default.actions`. Never reason from the top level alone.

`runAfter` is the dependency graph, with statuses `Succeeded`, `Failed`, `Skipped`, `TimedOut`. An
empty `{}` means run first.

## Non-negotiable rules

- **A catch marks the failure handled and the run reports Succeeded.** Any `runAfter` on `Failed`
  must be followed by a `Terminate` with `runStatus: Failed` if the failure should stay visible.
- **`Until` is do-until.** The body always runs at least once, then the condition is evaluated. A
  fallback inside the body fires on exactly the quiet case the loop was meant to skip. `limit.count`
  and `limit.timeout` are both required.
- **`SetVariable` and `AppendToArrayVariable` are not safe under a parallel `Foreach`.** Serialise
  with `"runtimeConfiguration": { "concurrency": { "repetitions": 1 } }`. Foreach defaults to 20
  parallel repetitions, maximum 50.
- **`union()` on arrays de-duplicates.** Use `concat()` to append pages of results.
- **An `ApiConnection` POST with no `body` creates an empty record.** It saves cleanly and produces
  content-free tickets. Always give a create action a body.
- **`Compose` output lives only in run history**, which expires and is not queryable. Anything
  needed as evidence must be written somewhere durable.
- **Secrets fetched over HTTP land in run history in cleartext** unless `secureData` is set. Prefer
  the workflow's managed identity over retrieving a credential at all.
- Reference connections through `@parameters('$connections')`, never by raw resource id.
- These fields cannot be expressions: `recurrence` frequency, interval and startTime; action names;
  `runAfter` keys; `foreach` target names.
- Every trigger and every action carries a `description`, at every nesting level, including inside a
  Switch case and an If else branch. It is the only documentation the next person has in the portal.
