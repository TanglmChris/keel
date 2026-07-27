<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Make recording the current fingerprint idempotent

- [x] 1.1 Replace any Contract anchor on --record, refuse only a missing one, and report which outcome occurred
  - Covers:
    - D1 the record write replaces the Contract anchor whatever its current value and refuses only a missing anchor
    - D2 replacing a different fingerprint is reported and warned about, not refused
    - keel-core-gates / Gate results expose capsule and fingerprint evidence / Reauthorization replaces a recorded anchor and warns
    - keel-core-gates / Gate results expose capsule and fingerprint evidence / Re-recording an unchanged contract writes nothing
    - keel-core-gates / Gate results expose capsule and fingerprint evidence / Record without a Contract anchor refuses
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/changes/record-allows-reauthorization/tasks.md
    - keel/archive/follow-ups/2026-07-27-stale-plugin-state-in-session.md
  - Verify:
    - Strategy: regression-first
    - M1: through the gate CLI, running task-start with --record a second time after the task authority changed succeeds instead of refusing, rewrites exactly the one Contract line to the new fingerprint, reports the outcome as rerecorded, and emits a warning naming the fingerprint it replaced; running it again with no authority change reports the outcome as unchanged and leaves the file byte-identical with no warning; a task carrying no Contract line still refuses with record-refused, writes nothing, and produces no guard manifest; and task-start without --record still leaves the file untouched. The core-gates validator scenario is rewritten to assert all four, and the full suite stays green
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d4c3974c248954362d5031f8f236057e74ea0497e4ebf592bd81fff1d0922712
    - M1: `contractAnchorPlan` now matches any `- Contract:` list entry in the selected task's range and returns the replaced text as `previous`, so the anchor form no longer decides whether the write is allowed. `taskStart` refuses only when no such line exists, and its message names the missing line and the literal form to add rather than conflating "already recorded" with "missing". The write path computes the target line first and skips the write entirely when it is already byte-identical, giving three reported outcomes — `recorded`, `rerecorded`, `unchanged` — carried on `result.record.status` alongside `result.record.previous`. A new `anchoredFingerprint` helper parses a fingerprint out of the replaced text, and a `rerecorded` outcome whose replaced value held a different fingerprint pushes a warning naming both values and stating that evidence produced under the previous contract is stale. The human-readable line reports the outcome; no consumer parsed its old shape
    - M1.red: with the new assertions in place against unmodified `src/core/gates.js`, `node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates` exited 1 with "core-gates scenario --record over an anchor that already carries the compiled fingerprint must report unchanged, warn about nothing, and write nothing", and dumped the gate result showing `status: fail` with the single problem `record-refused` — the exact refusal issue #13 reports
    - M1.green: the rewritten `core-gates` block asserts all four cases and exits 0: no-flag runs stay read-only, a pending anchor reports `recorded` and changes exactly one line, a re-record with no authority change reports `unchanged` with no warnings and byte-identical bytes, a re-record after an added Touch path reports `rerecorded` carrying the replaced fingerprint in `previous`, rewrites exactly the one Contract line to a genuinely different fingerprint, and warns naming the replaced one, and a task with no Contract line still refuses with `record-refused` writing nothing including the guard manifest. `npm test` reported "validation --all passed: baseline plus 64 scenarios". Verified end-to-end against this repository as well: the same command that refused five times in the 2026-07-27 session — `node bin/keel.js gate task-start . --change record-allows-reauthorization --task 1.1 --record` — now prints `Contract anchor unchanged` and `diff` against a pre-run copy of `tasks.md` reports no difference. The `rerecorded` branch was then exercised on this same task for real: adding the archive-note path to its own Touch changed the capsule, and re-running the identical command replaced `sha256:05b8cbd6…` with `sha256:d4c3974c…`, printed `Contract anchor rerecorded`, and emitted the stale-evidence warning naming both fingerprints — where the shipped 5.2.2 gate returns `record-refused` and demands a hand edit first
    - Review:
      - Status: pass
      - Acceptance check: pass — reauthorization runs without a manual edit, the contract change is reported and warned about rather than refused, a missing anchor still refuses writing nothing, and no-flag behavior is unchanged, satisfying D1, D2, and the three referenced scenarios
      - Scope check: pass — `src/core/gates.js`, `scripts/validate_plugin.py`, this task's own `tasks.md`, and the archive note, all within Touch. This task's contract was re-recorded once mid-implementation, which the new warning correctly flagged; the change was a Touch addition for the archive note, adding no verification obligation and invalidating no M1 evidence, so the recorded evidence stands. That judgment is the semantic call design.md D2 assigns to Review rather than to the gate
      - Findings: the write guard was not enforcing during this task. This session's plugin state was loaded before the relay-to-keel migration in `~/.claude/settings.json` took effect, so the relay SessionStart hook is still resident and keel's PreToolUse guard never ran; scope was proved by `keel gate task-complete --base HEAD` instead, and the guard returns on the next fresh session. Durable owner: `keel/archive/follow-ups/2026-07-27-stale-plugin-state-in-session.md`
    - Blocker: none

## Expectation Coverage

- E1: reauthorizing a task whose authority changed requires no manual edit of tasks.md Covered by: 1.1
- E2: a re-record that lands a different contract is visible at the moment it happens Covered by: 1.1
- E3: a genuinely malformed capsule with no Contract anchor still refuses and writes nothing Covered by: 1.1
- E4: task-start without --record stays byte-identical to the pre-flag gate Covered by: 1.1
