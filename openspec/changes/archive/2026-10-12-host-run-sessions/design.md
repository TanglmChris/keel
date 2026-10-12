## Context

Issue #300 and the owner's decision of 2026-10-12 recorded on it. Not chosen: relying only on where the task is created.

## Facts

- F1 — Both runs of rtl_ppa_prj's `rtl-ppa-pm-patrol` had the coordinator's worktree as cwd; the task's `lastRunAt` 11:57:12.258Z matches `iecc-pm`'s `session_started` 11:57:12.651Z, source `startup` (2026-10-12, read-only).
- F2 — In that run's transcript the SessionStart hooks ran at 11:57:12.7 and the prompt, beginning `<scheduled-task name="rtl-ppa-pm-patrol"`, was enqueued at 11:57:15.7; its metadata (`entrypoint: claude-desktop`) matches an ordinary session (Claude desktop 2.1.295). The marker is an observed host format, not a documented contract.
- F3 — Claude Code's hook payloads carry `session_id`; UserPromptSubmit carries `prompt`.
- F4 — The wake waiter polls the role's presence and fires on the first qualifying start (5.114.0).

## Decisions

- D1 — On SessionStart for a bound role, the hook writes `<chat root>/sessions/<session_id>.json` with the role and the presence it is about to replace, before touching presence. Without a `session_id` it writes nothing and behaves as before.
- D2 — On the first UserPromptSubmit of a session with that file, the hook decides: a prompt whose trimmed start is `<scheduled-task` marks the session `host_run` and restores the saved presence; any other prompt marks it ordinary. Later prompts never change the decision.
- D3 — For a `host_run` session every hook event returns exit 0 with no output and writes nothing: no presence, no notice, no wake; SessionEnd leaves presence as it is. SessionEnd removes the session's file in every case.
- D4 — The waiter, on seeing a qualifying start, notes its `session_started` and fires only if presence still shows that same value after `KEEL_SHIFT_WAKE_SETTLE_MS` (default 15000); a reverted start resets it to waiting.
- D5 — `keel patrol task` adds: `Create it from a session whose folder is bound to no role: a host task starts its runs in the folder it was created from, and Keel recognizes such a run only once its prompt arrives.`
