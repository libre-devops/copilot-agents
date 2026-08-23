# THE MANIFEST

`declarativeAgent.json` carries `"$schema"` and `"version": "v1.8"`.

## Fields and limits

- Required: `version`, `name` (100), `description` (1000). `instructions` (8000) is documented
  required but is absent from the schema's `required` array, and an agent without it has no
  behaviour.
- Optional: `capabilities`, `conversation_starters` (12), `actions` (1 to 10),
  `behavior_overrides`, `disclaimer.text` (500), `user_overrides`, and `worker_agents` (preview).
- Any string not otherwise capped is limited to 4,000 characters.
- **An unrecognised property invalidates the entire document.** Never invent one.
- At most **one capability of each type**.

## Capabilities

`WebSearch`, `OneDriveAndSharePoint`, `GraphConnectors`, `GraphicArt`, `CodeInterpreter`,
`Dataverse`, `TeamsMessages`, `Email`, `EmailActions`, `People`, `ScenarioModels`, `Meetings`,
`MeetingActions`, `EmbeddedKnowledge`.

- `WebSearch` is the **only** one usable without a Copilot licence or metered usage. Recommend it
  first, and name the licence cost of anything else.
- `WebSearch.sites`: max 4, each at most two path segments and no query string.
- `OneDriveAndSharePoint` with neither `items_by_url` nor `items_by_sharepoint_ids` grants **every**
  SharePoint and OneDrive source in the organisation. Scope it deliberately. `TeamsMessages` with
  no `urls` behaves the same way across every channel and chat, and allows at most 5.
- `EmbeddedKnowledge`: 10 files, 1 MB each, types `.doc .docx .ppt .pptx .xls .xlsx .txt .pdf`.
  JSON is not allowed, so ship a JSON schema renamed to `.txt`.
- `discourage_model_knowledge: true` stops the agent using its own knowledge. Right for an agent
  answering only from your content, wrong for one writing code. Recommend `false` there and let the
  instructions carry the house rules.

## The app package

A zip of `manifest.json` (the Microsoft 365 app manifest), the declarative agent JSON, `color.png`
(192x192) and `outline.png` (32x32, white on transparent). The app manifest points at the agent
through `copilotAgents.declarativeAgents`, and **only one is supported**. Limits: `name.short` 30,
`name.full` 100, `description.short` 80, `description.full` 4000, `accentColor` as `#RRGGBB`.

There is **no create API**. Upload is an admin or portal step. Never imply otherwise.
