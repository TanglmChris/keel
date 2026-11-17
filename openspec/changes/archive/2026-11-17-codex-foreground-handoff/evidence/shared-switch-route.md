# Reviewable shared-host switch route

Prepared 2026-11-17, task 2.3. This is an operational plan, not authorization
to execute its conditional branches. Keel maintenance remains the sole switch
executor. Chief coordinates owner decisions; flow performs downstream production
acceptance after actual formal delivery. #527 stays deferred.

## Current evidence, without assuming permanent Goal re-entry

`current-core-turns.json` records original App rollouts at 12:57:27 UTC:

- PM turn 01a1e988-1e59-7d50-babd-fa00f0508c7a completed at 12:52:56 UTC.
- Flow completed its earlier turn at 12:53:45 UTC, then began a composer turn
  01a1e995-33cd-72e0-bdb4-7350f2200ea8 at 12:57:11 UTC.
- Chief's current turn began through composer at 12:29:23 UTC; its preceding
  completed turn is not evidence that this current turn completed.
- Actual chief and flow get_goal tool outputs contained goal:null at 12:29:35
  and 12:52:40 respectively. These are dated per-role observations, not proof
  about all chats, future admissions or other automation sources.
- Returned tool RPCs do not prove detached subprocess sessions or background
  jobs finished. Each owner must retain actual process/tool terminal receipts.

No production thread was resumed by another daemon to manufacture these facts.
No business round, Goal or tool was stopped. The actual App inventory and owner
receipts must be refreshed immediately before execution; this snapshot expires.

## What normal Quit/Cancel protects

Installed Linux App 26.1023.51421, stdio 0.165.0-alpha.1.2, bundle SHA256
ad73b094efd3d5037bceb90b285cb20d6319c4043d3b7f52ee7fade6e3015c7a:

1. before-quit checks a renderer-reported active-local-chat Set, enabled
   automations and pending worktrees. If those checks require confirmation,
   a synchronous Quit/Cancel dialog is shown. Cancel calls preventDefault and
   returns before markQuitApproved/markAppQuitting in this handler.
2. Quit confirms interruption; it does not wait for a chat or tool to finish.
   Therefore never confirm it merely because a round appears to be coordination.
3. Confirmation can be bypassed on Windows, by prior/temporary approved quit
   state, or CODEX_ELECTRON_DISABLE_QUIT_CONFIRMATION=1. The current Linux main
   process has no such environment override; internal quit-state flags were not
   externally verified. macOS must inspect its own installed version.
4. The active Set is updated by local-thread-activity-changed renderer messages;
   it is not an atomic native admission/tool-drain receipt. will-quit's 5-second
   bounded context-disposal wait also is not a tool completion guarantee.

Consequently Cancel is a useful conditional failure exit if a dialog appears,
not a guaranteed race barrier. Do not invoke Quit on active chats just to test
whether that dialog appears, and do not edit flags or inject App code to force it.

## Route A — natural safe point, existing authorization

This route does not require a new native API or new owner permission **if its
actual prerequisites can be met**. It has not yet met them or executed.

1. Preserve the original maintenance id, Git head, all work, core registration
   and claim hashes, exact thread policy/cwd/history pointers and recovery note.
   The old expired unit stays inactive; record a new unique attempt id only after
   a current execution capsule defines its sole executor and bounded deadline.
2. Chief gathers one factual readiness receipt per currently relevant App role:
   normal turn completed, actual tool/subprocess handles terminated or explicitly
   proven independent of App shutdown, current automatic entry sources, and
   preserved work/recovery pointer. Detached jobs cannot be inferred done from
   a returned exec tool. No one stops IECC work or changes any Goal to provide it.
3. Coordination rounds finish normally when their current action is handed off;
   avoid generating repeated status/acknowledgement turns just to keep waiting.
   This is not a ban on user input, nor a claim of fenced admission. If a user or
   business/Goal turn arrives, cancel the attempt and let that work proceed.
4. The independent executor observes the **actual App** inventory/owner receipts,
   all local App chats/tools idle and preserved, no pending worktree setup or
   unresolved entry source. Native backend work need not stop merely because
   it exists; independently owned daemon work is assessed by actual ownership.
   Foreign notLoaded/goal:null never substitutes for actual App evidence.
5. Revalidate App/menu owner and backend pid/start identity, all prerequisites
   and current authorization. No completed receipt means no Quit. Request the
   native normal Quit once. If a busy prompt appears, choose Cancel, do not
   confirm interruption, record the failed attempt and leave the App untouched.
   The prompt is only supplementary protection, not the basis of step 4.
6. Only after original App exit and unchanged backend identity: run the approved
   private background fixture while App is absent, then launch App once with
   process-local CODEX_APP_SERVER_WS_URL using the native Unix WebSocket route.
   No daemon restart, launcher/global/SSH edit or second App instance.
7. Verify actual App connection identity and real private fixtures: frontend
   then background work, both busy directions serial, one claim per addressed
   record, same id/history/reviewer/cwd. Merely listing/opening is insufficient.
   Resume this original maintenance id with one durably reserved notification
   key; native queue/add is not idempotent, so unknown outcomes are reconciled
   against queue/history rather than automatically retried.
8. Failure: preserve every phase/outcome and original identities, no production
   migration. Roll back experimental App only by another safe normal exit, then
   the original launcher without the variable. If that safe exit is unavailable,
   record recovery-needed and stop; no force kill. Never restart the backend.
   Production chief/flow recovery follows only after real acceptance and release.

Current exit for Route A: not ready; current turns and whole-App tool/readiness
receipts are incomplete. No helper is armed and no blind 20-minute wait repeats.
Completing these prerequisites naturally is a valid next action, not an assertion
that a missing native interface makes all switching impossible.

## Route B — exact minimal proposed authorization delta

Only if Route A is blocked solely by harmless coordination model turns remaining
active after all tools/work are actually finished, chief may present this one-time
proposal to the human. It is **not approved by the original all-idle permission**:

- Allow normal Quit to terminate only explicitly handed-off **maintenance**
  `01a1e398-6e28-7003-9765-f6c714b2a5d4` and **chief**
  `01a1e7aa-5b7b-7541-bc35-7ec3f028009c` model coordination turns, while their
  executable tools/subprocesses have genuine terminal receipts and work, pending
  input and restart notes are preserved. Scope cannot silently include PM, flow,
  IECC roles, unrelated chats, any active Goal or business/tool execution.
- Keep all other actual App chats/tools naturally idle. PM/flow/IECC work must
  finish its own current work; do not cancel it for maintenance. If some other
  chat is active, this proposed delta does not make the attempt eligible.
- Explain plainly that the two named model replies may end without a final
  answer, an in-memory pending input could need explicit recovery, and history
  alone cannot prove every unsent input was saved. Preserve and acknowledge
  every known pending input before execution. If any cannot be preserved, stop.
- Ask separately whether the owner accepts this narrowly named interruption
  risk; do not treat chief's request, old permission, silence or elapsed time as
  approval. New input, active Goal, tool, business work or additional affected
  thread invalidates the proposal's scope rather than widening it.
- Only after explicit approval and a current execution capsule may maintenance
  arrange one bounded attempt. Same backend preservation, actual acceptance,
  original-id notification and safe rollback rules as Route A remain mandatory.

This delta is a possible way past a coordination-only stalemate, not a solution
to currently active IECC work or an unverified automatic admission source.

## Route C — when a new native capability is actually necessary

If automatic entry cannot naturally quiesce and stopping/changing it is excluded,
or exact tool state cannot be observed in its actual execution domain, neither
Route A nor the above narrow delta establishes safety. Required facility:

- native owner-side admission quiesce at a tick boundary, preserving Goals and
  queued user input; explicit active turn/tool/background terminal receipts;
  a bounded lease/token proving safe normal exit; abort/release/expiry recovery;
  same thread identity and deduplicated resume outcome evidence.

This describes a requested interface, **not an existing method to call**. The
inspected App/0.165 and backend/0.167.2 public request surfaces do not expose that
transaction. Product owner is OpenAI Codex App/native runtime; Keel #541 owns
documenting/version-probing it and integrating a supported operation. Do not
invent a Keel lock over a separate App writer or patch proprietary App bytes.

Feasible alternatives to review are Route A, the explicitly approved limited
Route B, or a supported native shared connection configured on a fresh Mac App
before relevant work starts (verify that Mac build/Connections UI, versions,
identity and persistence; this does not migrate Linux production by itself).
Official references: https://learn.chatgpt.com/docs/app-server and
https://learn.chatgpt.com/docs/remote-connections . No SSH or product configuration
change has been selected or executed by this plan.

Durable owner: https://github.com/TanglmChris/keel/issues/541 .
Window coordination: https://github.com/TanglmChris/kaiwu-ip/issues/555 .
