# #541 portable checkpoint and Mac continuation

This is an unfinished diagnostic checkpoint, not a release. #527 stays deferred.
#535 is closed; its separate implementation owner is #544.

## Repository state

- Branch: `codex/fix-541-foreground-handoff`.
- Product base: published Keel 5.229.3, base commit
  `20902321ea20896febca3fca320fd20a18288964`.
- No Keel product source or production registration changed in this checkpoint.
- Tasks 1.1 and 1.2 passed. Task 1.25 publishes the checkpoint. Task 1.3 is
  still pending; its execution fingerprint is preserved in tasks.md.

On Mac, first preserve any existing work, then fetch the branch normally:

```sh
git fetch origin
git switch codex/fix-541-foreground-handoff
keel context --json
```

Do not force a checkout or reset an existing local branch. Check actual CLI and
protocol versions rather than assuming the Mac matches this Linux host.
Read tasks.md, design.md, evidence/diagnosis.md and the latest issue #541
comments before selecting a next slice. The new agent can continue authoring,
implementation and review from Git; Linux runtime acceptance is still a
distinct dependency and must not be silently checked complete on Mac.

## Verified findings

- Separate App stdio and Unix daemon writers reject reverse busy frontend input.
- Native queues are consumed by actual busy and idle App execution, but native
  queue/add does not deduplicate the same client UUID. Claims/history need care.
- Native thread/settings/update persists explicit auto_review on a blank thread
  without a model warm-up. Cold resume and its first real App turn retained it.
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
The portable `evidence/window-state-checkpoint.json` is a historical snapshot,
not live service status. Read the actual Linux state and latest issue before
deciding whether the window ran, expired or failed. Do not restart an expired
window or create another executor from this checkpoint.

Revision 2 of the same unit uses native tray-menu change events plus a 300ms
fallback and an immediate second idle check before normal Quit. It preserved
the original deadline and previous events. Last measured PID was 2673080;
do not use a historical PID without revalidation. It never stops Goals or
force-kills the App. The latest snapshot still contained active jobs.

If the window runs, the helper performs explicit owned-fixture background
acceptance while the App is closed, then launches the App with a process-local
URL and queues one continuation to this maintenance chat's original ID:
`01a1e398-6e28-7003-9765-f6c714b2a5d4`.
The runner and pinned native client are retained as evidence, not portable
installers. Their absolute Linux paths and native menu identity are intentional.

## Remaining #541 delivery

1. Record the actual window outcome; preserve failed/expired evidence honestly.
2. Prove one execution instance through real App/background use, both busy
   directions, native persistence after App exit, original ids/history/claims,
   reviewer and actual worktree. Listing/start acceptance is insufficient.
3. Author the measured minimal adapter/CLI/recovery changes with concrete Touch
   and behavioral checks, then implement through task gates and test-first.
4. Complete regression, formal release/install and integration/rollback runbook.
5. Leave production Kaiwu recovery to chief/flow under kaiwu-ip #546; never
   rewrite their registration to hide drift or create replacement identities.
6. After formal delivery, proactively message existing chief thread
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
