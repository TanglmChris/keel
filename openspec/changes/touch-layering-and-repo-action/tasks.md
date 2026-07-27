<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. The guard stops denying what the completion gate forgives

- [x] 1.1 Let a guarded task write its own change directory, and stop hashing that directory for drift
  - Covers:
    - D1 the guard gains one record-write layer derived from the manifest change field, with no manifest schema change
    - D2 authority-drift hashing skips the same prefix in the hook and in guard status, because the fingerprint already distinguishes a record write from a contract change
    - keel-touch-write-guard / Guarded write tools outside Touch are denied deterministically / The guarded change's own records are writable undeclared
    - keel-touch-write-guard / Guard failure modes fail closed / Recording progress is not authority drift
    - keel-touch-write-guard / Guard failure modes fail closed / Completed task denies
  - Touch:
    - plugins/keel/scripts/pretooluse-guard.js
    - src/core/guard.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: driving the hook with real PreToolUse events, a write to the guarded change's own tasks.md is allowed although Touch never named it, that write still being present does not make a following in-Touch product write fail with authority drift, a write to another change's directory and to the archive tree are still denied, and an authority file outside the change directory that changed since guard start still denies. Once the guarded task's checkbox is ticked, a product write inside Touch is denied while a write to its own change directory still succeeds, so the task can finish its Evidence. keel guard status reports the same: no authority drift after a checkbox and Evidence write, and fingerprint drift when the same file's Touch line is edited. A new validator scenario locks every case
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:aa3af1668e8daed6505d61e4066d33f9410a0812e37dd4980fb1045b59404b45
    - M1: both the hook and `guardStatus` derive `recordPrefix` as `openspec/changes/<manifest.change>/` from the field the manifest already carries, so no manifest shape changed and an older hook against a newer CLI keeps today's behavior instead of failing closed. The hook now resolves the candidate path before the drift loop and returns early for anything under that prefix; the drift loop skips recorded authority entries under it; and `guardStatus` skips the same entries while keeping its fingerprint comparison untouched. Because byte hashing was also what incidentally stopped a checked task from writing, that denial is now stated directly: a new `taskIsChecked` reads the guarded task's own checkbox line with a targeted regex — not a second parser — and denies product writes while leaving the record layer open, so the task can still write the Evidence its completion gate demands. An unreadable or unmatched `tasks.md` is not read as checked, because every gate that compiles catches that and denying on a parse miss would trade a real capability for a guess
    - M1.red: the new `touch-guard-record-layer` scenario exited 1 at its first case — "expected silent allow for …/openspec/changes/demo/tasks.md" — dumping the deny whose reason was `openspec/changes/demo/tasks.md is outside Touch for demo#1.1. Touch allows: src/feature.js`, which is issue #8's reproduction verbatim
    - M1.green: the scenario exits 0 across nine cases driven through real PreToolUse events: the change's own `tasks.md` is writable undeclared; a product write still succeeds after that record write, where before it failed with authority drift; another change's directory and `keel/archive/**` are still denied; an authority file *outside* the change directory that moved since guard start still denies with `authority drift`; `guard status` reports `active` with no problems after a record write; editing the task's own Touch line still reports `fingerprint-drift`; and once the checkbox is ticked a product write inside Touch is denied while the record write still succeeds. `npm test` reported "validation --all passed: baseline plus 69 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — the guard and the completion gate now apply the same record-write boundary, a task can finish its own bookkeeping under an active guard, and each of the four enforcement paths that must survive is asserted by a case of its own, satisfying D1, D2 and the three referenced scenarios
      - Scope check: pass — `plugins/keel/scripts/pretooluse-guard.js`, `src/core/guard.js`, `scripts/validate_plugin.py`, all within Touch, verified against `--base HEAD`. The change's own spec delta and this `tasks.md` were also written; those are the record layer this task introduces, and `keel-core-gates` already excludes them from outside-Touch attribution
      - Findings: this narrows write-time drift detection, deliberately and not silently. Byte hashing did two jobs — reporting record writes as drift, which is the defect, and letting the hook notice a *real* contract edit inside `tasks.md` at the next write. A hook that cannot compile a capsule cannot separate them, so the second is lost: contract drift inside the change directory is now caught by `keel guard status` and `keel gate task-complete`, which compile and compare, rather than at the next write. Two existing assertions in `touch-guard-drift` were locking in the old behavior and were inverted — one of them asserted that appending a newline to `tasks.md` must fail closed, which is exactly the reported defect stated as a requirement. Durable owner: openspec/changes/touch-layering-and-repo-action/design.md decision D2, which states the trade and the rejected alternative
    - Blocker: none

## 2. A repository action is a legal task

- [ ] 2.1 Add Mode repo-action for an authorized repository action with no worktree writes
  - Covers:
    - D3 repo-action is a fourth mode requiring Touch none, prohibiting product writes, and alone omitting the commit prohibition
    - D4 whether the repository action was authorized stays a Review judgment, while the gate enforces the write posture
    - keel-task-capsule / Task modes and conditional fields are executable / Repo-action performs a repository action without worktree writes
    - keel-task-capsule / Task modes and conditional fields are executable / Repo-action still refuses a product Touch
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: through the gate CLI, a task declaring Mode repo-action with Touch none passes task-start and compiles to a capsule whose mode is repo-action, whose prohibitions include the product-write prohibition, and whose prohibitions are the only ones that omit the commit prohibition; the same mode with a concrete Touch path fails with a diagnostic naming the Touch none it requires; an unsupported mode value is still rejected by a message listing all four supported modes; and diagnose-only, implementation, and plan-first keep their existing acceptance and their existing prohibitions unchanged. A new validator scenario locks every case
  - Evidence:
    - Contract: pending
    - M1: pending
    - M1.red: pending
    - M1.green: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Expectation Coverage

- E1: a guarded task can write its own Evidence, Review, and checkbox without reauthorizing Covered by: 1.1
- E2: the guard and the completion gate agree on which paths are records rather than product Covered by: 1.1
- E3: no enforcement is lost — product writes outside Touch, authority edits outside the change directory, contract drift, and post-completion product writes all still deny Covered by: 1.1
- E4: a task whose effect is a repository action has a legal contract instead of a Touch entry chosen to satisfy the validator Covered by: 2.1
- E5: no existing task changes its compiled fingerprint Covered by: 1.1, 2.1
