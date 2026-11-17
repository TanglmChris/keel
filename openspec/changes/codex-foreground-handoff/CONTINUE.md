# #541 portable checkpoint and Mac continuation

This is an implemented, tested partial-issue checkpoint, not a release. #527 stays deferred.
#535 is closed; its separate implementation owner is #544.

## Repository state

- Branch: `codex/fix-541-foreground-handoff`.
- Product base: published Keel 5.229.3, base commit
  `20902321ea20896febca3fca320fd20a18288964`.
- Product changes: src/core/codex-host.js, scripts/test_codex_host.js and both
  docs/cli-team language versions. No production registration changed.
- Tasks 1.1 and 1.2 passed. Task 1.3 finished its bounded diagnostic attempt
  with a negative result: the window expired, App untouched. This is NOT a
  successful shared-host acceptance. Tasks 1.25/1.4 publish the checkpoints.
  Tasks 2.1 and 2.15 are implemented and passed: explicit persisted reviewer,
  bilingual docs, 14 host tests, real public CLI/cold/first-App acceptance and
  full baseline plus 426 scenarios (no skips). Task 2.2 completed the current
  safe-handoff diagnosis; its negative capability result is not integration.
  Task 2.25 publishes this source/evidence checkpoint. Task 2.3 is intentionally
  a draft and must be authored before task-start; full #541 remains open.

On Mac, first preserve any existing work, then fetch the branch normally:

```sh
git fetch origin
git switch codex/fix-541-foreground-handoff
node bin/keel.js context --json
```

Do not force a checkout or reset an existing local branch. Check actual CLI and
protocol versions rather than assuming the Mac matches this Linux host.
Read tasks.md, design.md, evidence/diagnosis.md and the latest issue #541
comments before selecting a next slice. Use this branch's `node bin/keel.js`
for the new reviewer option; globally installed 5.229.3 does not contain it.
No package version bump, release, global CLI or plugin install occurred here.
The new agent can continue authoring,
implementation and review from Git; Linux runtime acceptance is still a
distinct dependency and must not be silently checked complete on Mac.

## Verified findings

- Separate App stdio and Unix daemon writers reject reverse busy frontend input.
- Native queues are consumed by actual busy and idle App execution, but native
  queue/add does not deduplicate the same client UUID. Claims/history need care.
- Native thread/settings/update persists explicit auto_review on a blank thread
  without a model warm-up. Cold resume and its first real App turn retained it.
- The public managed CLI now exposes `start --approvals-reviewer user|auto_review`.
  It preserves on-request/workspace-write, records declared reviewer before any
  native creation, retains pending identity on unknown/failure, and carries the
  explicit reviewer through cold delivery and handover. Default calls keep
  existing behavior. Native fixture used an explicit 30000ms budget; one prior
  5-second creation remains unknown and was neither deleted nor retried.
- Same-id resume with cwd/runtimeWorkspaceRoots restored actual pwd execution
  on an owned fixture. Production attachment/three-role recovery is not proved.
- Linux App 26.1023.51421 has a build-specific native websocket URL route;
  native proxy protocol probes passed. Actual App startup/acceptance has not
  passed merely because that route exists in the bundle.

## Linux-only controlled window — do not run on Mac

The owner approved an all-local-chats/tools-idle normal App exit and one-time
native websocket URL startup, with no daemon restart or global/SSH changes.
The App-only downgrade was not adopted; persistent backend execution remains
part of the original acceptance.

Linux one-shot unit: `keel541-app-window.service`. Runtime state:
`/tmp/keel541-app-window/state.json`. Original deadline:
2026-11-17 11:28:14.238 UTC (19:28:14.238 Asia/Taipei).
Final result: `evidence/window-final-state.json` records termination at
11:28:14.519 UTC with `Idle window expired; App untouched`. The helper became
inactive; it performed no Quit/relaunch/background-test/continuation-queue step.
All three production registry hashes still match the pre-window snapshot.
Earlier `window-state-checkpoint.json` is historical, not a live waiting state.
Do not restart this expired window or create another executor from the checkpoint.

Revision 2 of the same unit uses native tray-menu change events plus a 300ms
fallback and an immediate second idle check before normal Quit. It preserved
the original deadline and previous events. Last measured PID was 2673080;
do not use a historical PID without revalidation. It never stops Goals or
force-kills the App. The final run did not observe an all-idle window before its original deadline.

The expired runner would have performed explicit owned-fixture background
acceptance while the App is closed, then launched the App with a process-local
URL and queued one continuation to this maintenance chat's original ID:
`01a1e398-6e28-7003-9765-f6c714b2a5d4`.
The runner and pinned native client are retained as evidence, not portable
installers. Their absolute Linux paths and native menu identity are intentional.

## Remaining #541 delivery

1. Review completed 2.1/2.15 source/test evidence and 2.2 diagnosis. See
   evidence/reviewer-cli-real.json, reviewer-host-green.txt,
   full-regression-green.txt and safe-handoff-diagnosis.md.
2. Author task 2.3 from current native execution-domain facts. The original
   window is over. Current App work was active at the last check. A foreign
   daemon's notLoaded/goal:null and thread-not-found terminal response do not
   prove App tool drain. No externally verifiable admission/drain transaction
   was established from the installed 176/180-method request schemas or normal
   Quit source. This is a concrete evidence gap, not an upstream impossibility.
   Historical 5ms Goal re-entry is not a permanent current-state assumption.
   Do not force Goals or business work to stop. A genuinely quiet route or a
   verified native protection point is needed before any newly identified,
   bounded single-executor attempt under the existing human permission.
3. Prove one execution instance through real App/background use, both busy
   directions, native persistence after App exit, original ids/history/claims,
   reviewer and actual worktree. Listing/start acceptance is insufficient.
4. Author the measured minimal adapter/CLI/recovery changes with concrete Touch
   and behavioral checks, then implement through task gates and test-first.
5. Complete regression, formal release/install and integration/rollback runbook.
6. Leave production Kaiwu recovery to chief/flow under kaiwu-ip #546; never
   rewrite their registration to hide drift or create replacement identities.
7. After formal delivery, proactively message existing chief thread
   `01a1e7aa-5b7b-7541-bc35-7ec3f028009c` with version/published commit,
   real acceptance and recovery/rollback evidence, and verify message acceptance.
   This responsibility is explicitly authorized and recorded on issue #541.

Durable owner: https://github.com/TanglmChris/keel/issues/541 .
Notification commitment: issuecomment-6944100669. Native entry and rollback:
issuecomment-6944761563. Armed window: issuecomment-6946344305. Guard revision
2: issuecomment-6946566161. None is a formal product delivery claim.

Unrelated local chat identities and account notifications were removed from
published evidence copies. Timings, activity counts and relevant fixture/core
identities remain; original runtime evidence on Linux was not modified.

The independently corroborated terminal window result is recorded at issuecomment-6946769610.
Current safe-handoff coordination evidence is published under kaiwu-ip #555,
commit cf6759ce9c5627a956a1af7bdbac8f9bb499bf0a. No new executor is waiting.
Task 2.3 is a draft, not permission to run another global experiment. Mac
takeover can proceed on the repository work now; remeasure Mac native versions
and capabilities rather than copying Linux PIDs, sockets or menu identities.

Published red-test text copies trim trailing whitespace only; original test outputs in /tmp were not modified.
