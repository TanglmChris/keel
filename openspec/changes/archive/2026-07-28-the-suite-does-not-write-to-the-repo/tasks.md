## 1. The suite stops writing to the repository

- [x] 1.1 Move the source-repo install onto a fixture and refuse the class at source level
  - Covers:
    - keel-validation-runner / The suite does not write to the repository it validates / A run leaves the tree unchanged
    - keel-validation-runner / The suite does not write to the repository it validates / A mutating invocation against the repository root is refused
    - keel-validation-runner / The suite does not write to the repository it validates / Install behavior is proven on a fixture with the required shape
    - F1 the classifier reads exactly two signals, so a fixture costs three lines
    - F2 the scenario is the only mutating invocation aimed at the repository root
    - D1 a fixture rather than snapshot-and-restore
    - D2 the refusal is keyed on mutating subcommands, not on the root
    - D3 the scenario also asserts what the install did not write
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: with a `.claude/` overlay marker rolled back to the previous version — the post-bump state — a full `npm test` leaves the marker exactly as it found it, where before the run silently repaired it
    - M2: a baseline check fails, naming the scenario and the invocation, when a scenario passes the repository root to a mutating Keel command, while read-only invocations against the root still pass
    - M3 (regression): the relocated scenario still proves what it came to prove — a repository carrying the two classifier signals gets the explicit `skip AGENTS.md` message and an untouched managed block — and now also asserts the install wrote nothing else to the fixture
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:abd477f7eec9d8dec6bc74ee42d9132f58628c823c84c2f028fef1dba938c176
    - M1: pass, and the same run proves both halves of why this mattered. With `.claude/skills/openspec-apply-change/SKILL.md` rolled back to `version=5.3.3` — the post-bump state — a full `npm test` left it at `5.3.3`, and the run **failed**: `shipped version marker disagrees with the package version 5.3.4: .claude/skills/openspec-apply-change/SKILL.md says 5.3.3`. So the suite stopped writing, and the 5.3.4 marker check it had been masking now fires on the `.claude/` side for the first time.
    - M1.red: the identical rollback before this change ended the run at `version=5.3.4` with the suite green. The file was repaired by the thing that was supposed to be checking it — a check cannot fail when its own run produces its input.
    - M1.green: the marker survives the run untouched, and the check that depends on it reports honestly.
    - M2: pass. Baseline refuses any `run_keel(ROOT, …)` or `run_install(ROOT, …)` carrying a mutating subcommand, naming file, line, and the invocation. The refusal keys on the subcommand rather than on `ROOT` (D2), so the many read-only invocations — `--help`, `--version`, `--doctor`, `gate …` — stay legal and none of them tripped it.
    - M2.red: pointing the relocated call back at `ROOT` failed baseline with `a scenario must not run a mutating Keel command against the repository it validates; build a fixture instead: scripts/validate_plugin.py:5059: result = run_keel(ROOT, "--install", "--target", "claude")`.
    - M2.green: the call restored to the fixture; baseline passes with no other site tripping the rule, which confirms F2's claim that this was the only one.
    - M3: pass. The relocated scenario still proves what it came to prove. A fixture carrying the two signals `is_keel_source_repo` reads — a `package.json` named `@christang/keel` and a `plugins/keel/` directory — gets the explicit `skip AGENTS.md` message and an untouched managed block, and the consuming-project half is unchanged. It now also snapshots the fixture and fails naming any file the install rewrote without announcing it (D3), which is the assertion whose absence was the actual defect.
    - Review:
      - Status: pass
      - Acceptance check: M1 is the behavior that matters and is measured end to end on the real suite against a real dirty state, not on a fixture standing in for one; its evidence is the file's contents before and after. The three covered scenarios map directly: the unchanged marker to "A run leaves the tree unchanged", the source-level refusal to "A mutating invocation against the repository root is refused", and the rebuilt fixture plus its no-other-writes assertion to "Install behavior is proven on a fixture with the required shape". A1 holds by construction — the fixture provides exactly the two signals the classifier reads, and the skip message proves the same branch was taken.
      - Scope check: one file changed, `scripts/validate_plugin.py`, which is the sole declared Touch path. Both mutations were reverted and `npm test` passes with baseline plus 80 scenarios; `git status` shows only that file and this change's own directory.
      - Findings: `keel --check` under-reports what `keel --install` will do — with a stale marker it prints an empty dry-run plan while the install reports `refreshed=1` and rewrites a file, because the overlay refresh runs outside the action plan. That is a diagnostic honesty defect in its own right and is why this side effect was invisible to anyone reading the plan. Out of this task's Touch. Durable owner: https://github.com/TanglmChris/keel/issues/27
    - Blocker: none

## Invalidates

- I1: "a test installs one target and nothing installs the other" — the 5.3.4 entry in `keel/CHANGELOG.md` and the correction comment on issue #23. It describes the mechanism in the present tense; after this change no test installs any target into the repository. Discard reason: both are dated records of why the drift happened, and the 5.3.5 entry states that the mechanism is gone rather than rewriting the account of how it worked.
- I2: "the `.claude/` side will not go red as long as this scenario keeps refreshing it" — the reasoning recorded in issue #26 and in `openspec/changes/archive/2026-07-28-statements-that-stay-true/tasks.md` task 2.1 Findings. It stops being true here, which is the point of the change. Updated by: 1.1

## Expectation Coverage

- E1: a validation run leaves the working tree byte-identical Covered by: 1.1
- E2: the marker check is green because the markers are right, not because the suite wrote them Covered by: 1.1
- E3: the class is refused at source level rather than fixed at one call site Covered by: 1.1
- E4: the fixture could drift from the real repository's shape. Discard reason: accepted as a design risk; the classifier reads two signals and the fixture provides exactly those, so drift would be a classifier change, which fails this scenario rather than passing silently.
- E5: the overlay refresh runs outside the dry-run action plan, so `keel --check` under-reports what `keel --install` will do. Durable owner: https://github.com/TanglmChris/keel/issues/27
