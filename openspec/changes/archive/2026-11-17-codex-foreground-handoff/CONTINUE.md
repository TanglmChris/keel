# #541 implementation and 5.230.0 release-candidate checkpoint

This records candidate preparation before formal publication. #527 stays deferred;
#544 owns cross-harness policy implementation separately. Do not read a Git commit,
App listing or RPC acceptance as release/production success.

## Portable repository work

Branch: codex/fix-541-foreground-handoff. Product base was published 5.229.3,
20902321ea20896febca3fca320fd20a18288964. Candidate is 5.230.0.
The explicit reviewer, same-id cwd recovery, bilingual native shared-window
runbook and release alignment are implemented. Main docs are docs/cli-team.md,
docs/cli-team.zh-CN.md, docs/codex-validation.md and docs/host-contract.md.

Public host tests: 16 passed. Full recovery-code regression: baseline plus 426
scenarios, no skips (278 deterministic/148 stand-in). Candidate baseline/docs
passed; actual clean-tarball and updater installations both retained OpenSpec
1.14.0 and passed all 37 published specs. Exact-head full-gate CI still owns the
final repository auto-merge/publish decision. No agent merge or hand tag.

After preserving existing work, Mac may fetch/switch this branch normally and
use node bin/keel.js context --json. Do not force/reset another branch or assume
Mac versions/capabilities match Linux. Read the current issue #541 state and PR /
release results before taking the next action; archived tasks are historical.

## Runtime evidence and final state

The old global idle window ended negatively at 11:28:14.519 UTC on 2026-11-17:
Idle window expired; App untouched. Its old unit is inactive. Never restart or
reset that attempt. No global Quit fence was proven.

A different, owner-approved experiment used a private App profile/home against
the existing native backend, avoiding original App interruption. It passed real
foreground-active/backend-wait, backend follow-up, actual native Guide while a
sleep tool was in flight, normal tool completion, App-closed backend execution,
real reopened UI reply/history, original-id/cwd/policy and claim dedup.
Authoritative entry: evidence/isolated-acceptance.md. Both isolated runs normally
closed, debug ports closed, original App/backend identities and three production
registry hashes unchanged. D13 separately authorized the sole native private-
project trust entry and its exact cleanup; config hash was restored.

Evidence scripts are Linux-only historical repro helpers with absolute temporary
paths; do not launch them on Mac or treat their saved PIDs/menus as current.
Private frontend home does not isolate backend trust. Do not copy credentials,
patch App bytes, force a writer, stop Goals or restart a daemon.

## Remaining external publication and deployment sequence

1. Push reviewed candidate; open PR into main; repository-owned full-gate and
   publish workflow must run on the actual head. Verify npm version and release
   commit, not merely workflow start or tag existence.
2. Verify/update local CLI and plugins under existing owner authorization,
   preserving native trust review. Do not report source candidate as installed.
3. Proactively notify original Kaiwu chief and flow with actual published version,
   commit, acceptance, upgrade and rollback entry. Notification must be accepted.
4. Chief/flow own Kaiwu #546 production recovery/acceptance. No production role
   or registry was changed by this work. The shared connection is explicitly
   opt-in, build-specific native configuration; the original App stays as it was.
5. Close #541 only after actual publication/verification and notification. If a
   release fails, keep the issue open with exact failure evidence and preserve
   this checkout; do not fake completion or replay unknown actions.

Durable owner: https://github.com/TanglmChris/keel/issues/541 .
Deployment owner: https://github.com/TanglmChris/kaiwu-ip/issues/546 .
Formal notification responsibility: issuecomment-6944100669. User explicitly
reminded version synchronization in this chat. #527 remains untouched.

Publication copies of red-test text trim trailing whitespace only; original
runtime outputs were retained. Unrelated chat/account details are omitted from
published UI evidence. Preliminary Enter/history-only probes are labelled as
insufficient; final acceptance is based on the explicit native/real-UI assertions.
