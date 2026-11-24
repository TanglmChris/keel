## Decisions

- D1 — Store the original owned native thread ID when reserving the existing delivery claim and preserve it after native turn acknowledgement. Role handover and migration preserve existing claims and cannot overwrite that identity with the current thread.
- D2 — `keel codex status --role <role> --record <id> --json` reads the existing owned-role registry and returns role, requested record, state (delivered, unknown, or unrecorded), thread and turn. Use null for absent historical fields, including legacy claims with no original thread. The query contacts no app server and creates no native work or model turn. It gives receipt evidence and no completion or write-release verdict.
- D3 — Runtime reconciliation, shared execution attempt generation, and cross-harness fencing remain tracked by #544. This change preserves existing scheduling and delivery semantics.
