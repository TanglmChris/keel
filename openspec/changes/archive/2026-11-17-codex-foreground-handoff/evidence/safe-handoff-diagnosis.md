# Native safe-handoff diagnosis, 2026-11-17

This completes diagnostic task 2.2, not shared-App acceptance or issue #541.
No new controlled window, App Quit/relaunch, Goal mutation, daemon restart,
tool interruption, production registration change or alternate dispatcher ran.

## Current verified state

- The original helper ended at 11:28:14.519 UTC, `stopped-without-forced-action`,
  `Idle window expired; App untouched`. Recheck: unit inactive/dead, MainPID 0.
- At 12:48:19 UTC, actual App inventory had 27 local chats: 7 active, 9 idle,
  11 notLoaded. Core chief/PM/flow and this maintenance chat were active.
  See `current-app-activity.json`; unrelated identities were omitted.
- The current original execution processes were App main 914946, App stdio
  915503, native persistent backend 1933800. Selected CODEX_HOME/SQLITE_HOME
  environment and sqlite_home/features.goals argv overrides were absent on all
  three. This does not prove identical effective configuration or Goal state.
- Foreign backend reads of our App-used private fixture returned notLoaded,
  goal:null, and backgroundTerminals/list `thread not found`. These are not
  observations of actual App tool drain. See `native-final-scope.json` and
  `goal-observation-scope.json`. No production thread was resumed to inspect it.

## Interfaces actually inspected

Installed App 26.1023.51421 uses stdio 0.165.0-alpha.1.2. Native backend is
0.167.2. Generated ClientRequest schemas declare respectively 176 and 180
methods; none has a name matching admission/quiesce/drain/shutdown/quit.
Relevant existing methods are thread/unsubscribe, thread/goal/get/set/clear,
thread/queue/*, thread/backgroundTerminals/list/clean/terminate, turn/interrupt.
This is a bounded statement about those surfaces, not proof that every internal
maintenance facility is absent. The initial local enum parser returned zero
because it expected const; the corrected enum parser and hashes are retained
in `native-final-scope.json`.

The installed main bundle SHA256 is
`ad73b094efd3d5037bceb90b285cb20d6319c4043d3b7f52ee7fade6e3015c7a`.
Read-only extracted-source locations (byte offsets in that bundle):

- before-quit handler around 4817k: current-local-conversation, automation and
  pending-worktree checks, followed by Quit/Cancel confirmation when required.
- `wde` at 361109 reads a renderer-fed in-progress Set; it is not a public
  execution-domain turn/tool-drain receipt.
- will-quit at 4819038 flushes state/settings/tracing and context disposal.
  `l9` at 4809205 waits for a callback or timeout, swallowing either callback
  outcome; `LEt` is 5000ms. This flush timeout is not proof that all tools finish.
- markAppQuitting methods at 440050 and 5123250 handle window/presentation and
  hotkey lifecycle. Their existence alone does not prove a native Goal fence.

Static source review did not establish an external atomic operation that blocks
new turns, drains actual local tools and returns a verifiable normal-Quit point.
No installed App bytes or launcher were edited. Full proprietary bundles are
not copied into Git; only derived facts and source hashes are recorded.

## Precise gap and failure exit

The missing evidence is **a safe transaction in the actual App execution domain
between completed tools and the next admitted turn**, with pending input and
original identities preserved. Two idle snapshots, a tray label, shared history,
foreign goal:null or a timed flush do not establish that transaction. A native
supported fence/receipt or a separately verified genuine quiet point is needed
before another controlled attempt. Current active work already disqualifies Quit.

No upstream impossibility is asserted. Chief's historical Goal-triggered 5ms
re-entry was real (kaiwu-ip #555, published commit cf6759ce9c5627a956a1af7bdbac8f9bb499bf0a).
Chief subsequently reported actual get_goal null without changing its Goal
(kaiwu-ip #554 comment 6947501510). Neither proves the current state of all chats;
do not stop Goals or business work to manufacture a window.

Failure exit: keep the App/backend untouched and preserve the expired attempt.
Do not restart its unit or reset its deadline. A future attempt needs an explicit
current capsule, unique attempt identity, one bounded executor, current execution
domain preflight and the existing normal-Quit/one-time-URL rollback conditions.
Existing human permission persists; no duplicate permission interview is required.

Remaining acceptance: actual App uses the same persistent execution instance;
both busy directions serialize; backend execution continues with App closed;
original ids/history/claims/reviewer/cwd are retained; production recovery is
performed by chief/flow after formal delivery. The independently green reviewer
CLI slice does not satisfy these remaining conditions.

Durable owner: https://github.com/TanglmChris/keel/issues/541 .
Coordination evidence: https://github.com/TanglmChris/kaiwu-ip/issues/555 .
Primary capability reference: https://learn.chatgpt.com/docs/app-server .
