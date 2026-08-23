# Platform notes

Where the declarative agent platform's documentation, its published schema and its actual behaviour
disagree, this file records the discrepancy, the decision taken, and the date it was checked. It
follows the same discipline as the rest of Libre DevOps: verify against the live source, never add a
field from memory, and say plainly where the seam is.

## `instructions` is documented as required, but is not required by the schema

Checked **2026-08-23** against
[declarative agent schema 1.8](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/declarative-agent-manifest-1.8)
and the [published schema](https://developer.microsoft.com/json-schemas/copilot/declarative-agent/v1.8/schema.json).

The reference table marks `instructions` Required. The schema's root `required` array is
`["version", "name", "description"]` only. A manifest with no instructions therefore validates
cleanly against the schema and is an agent with no behaviour.

**Decision:** `tools/lint.py` checks for a non-empty `instructions` itself rather than relying on
schema validation.

## The schema does not reject unrecognised properties

Checked **2026-08-23**.

The reference states: "Unrecognized or extraneous properties in any JSON object make the entire
document invalid." The published schema carries no `additionalProperties: false` at the root, and
only two occurrences anywhere in its 53 KB. A misspelled property name passes schema validation and
is then rejected by the platform.

**Decision:** `tools/lint.py` derives the allowed root property set from the schema's own
`properties` map and flags anything outside it, so the check tracks future schema versions instead
of hardcoding a list. `$schema` is allowlisted, because Microsoft's own reference manifest includes
it even though it is not a declared property.

## `EmbeddedKnowledge` is in the schema, but embedded files may not be enabled

Checked **2026-08-23**.

`EmbeddedKnowledge` is a fully specified capability in the 1.8 schema. The same reference page, in
the sensitivity label section, states: "This property is not enabled yet, since Embedded Files are
not enabled yet."

**Decision:** the renderer supports the capability in full but **omits it by default**. Pass
`--with-embedded-knowledge` to emit it. The shipped packages in `rendered/` are ones the platform
will accept today. See [knowledge.md](knowledge.md).

## The documented embedded file types exclude a type used in the reference's own example

Checked **2026-08-23**.

The allowed embedded document types are `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`, `.txt`
and `.pdf`. The reference's own `EmbeddedKnowledge` example lists `file2.csv`.

**Decision:** the renderer and linter enforce the documented allowlist, which is why the workflow
definition schema ships as `workflowdefinition.schema.txt` rather than `.json`.

## Agent Builder's Name field is tighter than the manifest's

Checked **2026-08-23** against
[Build agents with Agent Builder](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/agent-builder-build-agents).

The manifest allows a 100 character `name`. Agent Builder's **Name** field allows 30. An agent named
between the two packages and validates perfectly but cannot be built in Agent Builder as named.

**Decision:** `tools/lint.py` warns rather than errors, because the app package path is unaffected.
The build guide prints the count against 30 and flags an over-long name in place.

## Agent Builder has no import path, and no Actions

Checked **2026-08-23**.

Agent Builder is a form. There is no way to upload a `declarativeAgent.json` or an app package into
it, though it can export one (**Download .zip file**, manifest and icon only, no embedded files).
It also does not support Actions or API plugins: those need Copilot Studio.

**Decision:** the renderer writes `rendered/<agent>/BUILD-GUIDE.md`, a paste-ready rendering of every
Configure tab field in the order the form asks for them. This is the same honest seam as the plugin
upload step: the tooling ends where the platform's API ends, and hands a human exactly what to do
next rather than pretending. The guide is deliberately excluded from the app package zip.

## Upload is a portal or admin step

There is no create API for a declarative agent app package: an app package is submitted to a
tenant admin for organisational publishing, or to Partner Center for AppSource. This repository
therefore ends at a validated, uploadable `.zip` in `dist/`, and says so. If Microsoft ships a
publish API, wire it into a new recipe and delete this note.
