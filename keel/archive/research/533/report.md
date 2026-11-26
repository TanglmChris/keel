# Four-task Sol screening pilot

Keel #533, 2026-11-26. All 16 prespecified responses passed their behavior checks. Manual review found zero unsupported defensive paths, hidden failures or lost required safeguards in either model or instruction condition.

| Model | Instruction | Passed | Unsupported branches | Hidden failures | Lost safeguards | Input tokens | Cached input | Output tokens | Seconds |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt-6.1-sol | baseline | 4 | 0 | 0 | 0 | 23138 | 8576 | 229 | 31.18 |
| gpt-6.1-sol | traceable | 4 | 0 | 0 | 0 | 23262 | 18304 | 212 | 32.93 |
| gpt-6.2-sol | baseline | 4 | 0 | 0 | 0 | 23466 | 8960 | 132 | 31.87 |
| gpt-6.2-sol | traceable | 4 | 0 | 0 | 0 | 23590 | 9984 | 135 | 31.56 |

The internal transform only filtered and projected the supplied fields. Every external parser rejected JSON booleans and out-of-range values. Every delivery attempted the external operation once and propagated unexpected errors. All four legacy readers selected the fallback only on the supported exception. Error message wording and placement of one fallback call varied without changing these behaviors.

The controller ran Codex CLI 0.172.0 with medium effort, requested model fallback disabled, ephemeral read-only sessions and empty runtime environments. A loopback preflight observed zero model tools and no project or personal instructions. The actual native traces contain only user, reasoning and agent message items. Models are labelled by the native thread's confirmed selection. Token counts are native last-turn usage; cached tokens are included in input. Elapsed time includes local session startup. The complete native answers, exact prompts, patches, checks and individual usage are in [runs.json](runs.json).

The initial reviewer saw only opaque IDs and candidate text before scores were frozen. Behavior tests then ran in separate network-isolated containers with only system Python and synthetic input. A controller program joined the assignment key afterwards. This was one reviewer and one sample per cell. The short, explicit tasks gave both conditions a perfect baseline. The pilot cannot measure the frequency of over-defensive code on larger repositories, rank the models, or demonstrate an improvement from the extra instruction. Keep current guidance. A future report with a reproducible real task and patch can reopen the investigation.

[Frozen inputs and scoring protocol](https://github.com/TanglmChris/keel/tree/4e17cd40/openspec/changes/archive/2026-11-26-freeze-defensive-review-pilot/evidence)
