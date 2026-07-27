<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. A tracker can own a follow-up

- [x] 1.1 Accept an absolute tracker reference as a durable owner in both checks
  - Covers:
    - D1 a durable follow-up owner may be an absolute http or https reference, and the two implementations of the rule share one accepted-form list
    - keel-core-gates / Semantic judgment remains agent-owned / An external tracker owns a finding without a local proxy file
    - keel-core-gates / Gate rejections for validated forms name the field and accepted forms / Findings rejection shows the accepted ownership forms
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
    - AGENTS.md
    - openspec/changes/honest-surfaces-and-owners/tasks.md
  - Verify:
    - Strategy: regression-first
    - M1: through the gate CLI, a Review Findings value whose only owner is an absolute https reference passes task-complete instead of producing finding-owner, the same reference passes as an Expectation Coverage durable owner at change-close, every form accepted before is still accepted in both checks, a Findings value with no owner at all still fails, keel/HANDOFF.md is still refused, and the finding-owner message lists the tracker form; a new validator scenario locks all of it, and this repository's own Project Conventions stop prescribing the local-note workaround
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1a3c9d0e32facac767e27d16ad71b580ce289a22c537e273161abf5cbe3526ff
    - M1: a new `SHARED_DURABLE_OWNER_FORMS` constant holds the shape-checked owner forms — a `keel/archive/…` path and an absolute `http`/`https` reference — and is consumed by both `findingOwnerIsDurable` and the `Durable owner:` branch of `expectationProblems`, so a form added to one can no longer be missing from the other. Each check keeps what it accepted before on top of that list: Findings still existence-checks an `openspec/changes/…` artifact and still refuses `keel/HANDOFF.md`, and Expectation Coverage still accepts a bare `openspec/changes/` prefix. Both rejection messages now name the tracker form. This repository's `AGENTS.md` Project Conventions bullet, which existed only to prescribe the local-note workaround, now states the accepted forms directly
    - M1.red: the new `tracker-durable-owner` scenario exited 1 at its first case with "a finding owned by an absolute tracker reference was still refused", dumping a `task-complete` result of `status: fail` carrying `finding-owner` — the reproduction from issue #12
    - M1.green: the scenario exits 0 across seven cases: a tracker-owned finding passes `task-complete`; an unowned finding still fails and its message names the tracker form; `keel/HANDOFF.md` is still refused; a `keel/archive/…` owner still passes; a tracker reference passes as an `Expectation Coverage` `Durable owner:` at `change-close`; a `Covered by:` closure still passes; and an `E1` with no coverage, owner, or discard reason still fails. `npm test` reported "validation --all passed: baseline plus 65 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — a project whose follow-up owner is an issue tracker can name it directly in both places a durable owner is required, while every previously accepted form and both refusals are locked by the same scenario, satisfying D1 and the two referenced scenarios
      - Scope check: pass — `src/core/gates.js`, `scripts/validate_plugin.py`, `AGENTS.md`, and this task's own `tasks.md`, all within Touch, verified against `--base HEAD`. The contract was re-recorded once when `AGENTS.md` was added to Touch; that added the repository's own convention text to the task and invalidated no M1 evidence, which was re-run green afterwards
      - Findings: the two checks still disagree on how strictly they read the `openspec/changes/…` form — Findings requires an existing artifact, Expectation Coverage accepts the bare prefix — so a `Durable owner:` naming an artifact that does not exist still passes `change-close`. Tightening it is a narrowing unrelated to issue #12 and was deliberately left out. Durable owner: openspec/changes/honest-surfaces-and-owners/design.md risk A4
    - Blocker: none

## 2. A gate run leaves no undeclared file

- [ ] 2.1 Scaffold keel/.gitignore declaring the guard manifest
  - Covers:
    - D2 the guard manifest is declared ignorable by a scaffolded keel/.gitignore that install never overwrites
    - keel-touch-write-guard / The guard manifest is declared ignorable local state / Install declares the manifest ignorable
    - keel-touch-write-guard / The guard manifest is declared ignorable local state / An existing ignore file is not overwritten
  - Touch:
    - scripts/install_to_repo.py
    - assets/keel/gitignore
    - keel/.gitignore
    - scripts/validate_plugin.py
    - openspec/changes/honest-surfaces-and-owners/tasks.md
  - Verify:
    - Strategy: regression-first
    - M1: running keel --install in a temporary project with no keel/.gitignore creates one declaring the guard manifest, running a passing task-start there afterwards leaves git status reporting no untracked path for it, and running the same install against a project that already has that file leaves it byte-identical while reporting the skip; a new validator scenario locks all three, and this repository gains the same declaration so its own gate runs stop dirtying git status
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

## 3. A written manifest is not observed enforcement

- [ ] 3.1 State the enforcement boundary in the guard command's own result
  - Covers:
    - D3 the guard command's own output states that the status describes the manifest and that enforcement needs a runtime hook Keel cannot observe
    - keel-touch-write-guard / Guard capability is reported from observed evidence / Guard status describes the manifest, not enforcement
  - Touch:
    - src/core/guard.js
    - scripts/validate_plugin.py
    - openspec/changes/honest-surfaces-and-owners/tasks.md
  - Verify:
    - Strategy: regression-first
    - M1: through the guard CLI, both keel guard start and keel guard status on a written manifest carry a statement that the reported status describes the manifest and that enforcement depends on a runtime hook Keel cannot observe from the repository, in the JSON result and in the human-readable output, while the existing durability statement and every existing status value are unchanged; a new validator scenario locks the wording's presence and that no result asserts writes are currently being checked
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

## 4. Keel's own developers run Keel's own CLI

- [ ] 4.1 Report the CLI resolution hazard in doctor, scoped to the source repository
  - Covers:
    - D4 the hazard is a doctor line gated on the shipped source-repository predicate and names the concrete working invocation
    - keel-target-surface-diagnostics / Doctor reports the CLI resolution hazard in Keel's own repository / Source repository is told to use its own CLI
    - keel-target-surface-diagnostics / Doctor reports the CLI resolution hazard in Keel's own repository / A consuming project is not shown the hazard
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
    - openspec/changes/honest-surfaces-and-owners/tasks.md
  - Verify:
    - Strategy: regression-first
    - M1: keel --doctor run in this repository reports an advisory line naming the repository-local invocation for gate commands including its explicit repository argument, the same command run in a temporary consuming project omits the line entirely, and neither run changes the doctor exit status; a new validator scenario locks both directions
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

- E1: a project whose follow-up owner is an issue tracker writes no local file solely to satisfy a shape check Covered by: 1.1
- E2: an ordinary gate run leaves git status unchanged Covered by: 2.1
- E3: no Keel output lets a written guard manifest be read as proof that writes are being checked Covered by: 3.1
- E4: an author changing gate code is told that the bare command verifies the installed CLI Covered by: 4.1
- E5: every durable-owner form accepted before this change is still accepted Covered by: 1.1
