# Native onboarding measurement

2026-11-18: independent temporary native app-server processes with a shared temporary CODEX_HOME, no credentials copied, no production socket or global config used. CLI 0.164.0 and installed daemon binary 0.167.2 both measured.

- thread/read does not expose effective approval/sandbox/reviewer. Same-id thread/resume with only threadId rejoins the original execution context and returns original readOnly/on-request/user. No policy override, model turn or history import is necessary.
- While source owns the writer, target thread/read can see the same persistent id with a foreign notLoaded state; target resume refuses “already has an active writer”. Thus foreign notLoaded alone is not a safety signal.
- Source native queue and background terminal lists empty and goal null. Source thread/unsubscribe returns unsubscribed; target same-id resume then succeeds retaining original cwd, policy and zero-turn history.
- Tests used source created persistent native thread and metadata name, then only read/rejoin/list/unsubscribe. Both test processes were normally terminated with SIGTERM after their fixture was idle. No App, production role/service/Goal or global config changed.
- These measurements prove native lifecycle with a blank persistent thread, not model completion, busy rejoin, frontend routing or production deployment. Implementation acceptance must add nonempty-history and actual-model delivery evidence. Root/native fixture paths and IDs in JSON are temporary diagnostics, not portable commands or production identities.

Official native reference: https://learn.chatgpt.com/docs/app-server (read 2026-11-18). Installed generated schemas establish the version-specific fields; actual lifecycle JSON establishes behavior.
