<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Retire the standing follow-up backlog

- [x] 1.1 Name GitHub issues as the durable follow-up owner in AGENTS.md, outside the managed block
  - Covers:
    - D1 GitHub issues are this repository's durable follow-up owner
    - D3 the convention lives below the keel managed block, not inside it and not in a spec
    - keel-expectation-slice-evidence-gates / Completion Gate closes expectation evidence / Completed work has evidence closure
  - Touch:
    - AGENTS.md
  - Verify:
    - Strategy: evidence-first
    - M1: AGENTS.md gains a Project Conventions section positioned after the keel:end marker that names GitHub issues as the durable owner for deferred follow-ups, keeps keel/HANDOFF.md pointer-only, and warns against creating a standing OpenSpec change as a follow-up store; the Keel managed block is byte-identical to its previous content and npm test still reports every scenario passing, proving the four scenarios that assert on managed-block protocol text are unaffected
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d9f808bc8bc958399a297221988f2bca9875bd60eed7dca02ba535a76d6bd35f
    - M1: AGENTS.md gained a Project Conventions section immediately after the keel:end marker at former line 81, naming GitHub issues as the durable follow-up owner with evidence/rationale/consequence, keeping keel/HANDOFF.md pointer-only and keel/archive/ historical, and warning that a change directory with a proposal or specs but no task checkboxes is inferred as actionable authoring work in perpetuity. The managed block hashed sha256:0b3b0dbc2ff296b784cd846e0ef68d82772a631a99f10a926a8452c35d18387c both before and after the edit, so it is byte-identical; npm test reported "validation --all passed: baseline plus 58 scenarios", confirming the four managed-block scenarios (expectation-slice-gates, expectation-completion-gates, authoring-continuity, skill-portability-policy) are unaffected
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pass
      - Acceptance check: pass — the durable follow-up owner is now recorded in a location `keel --install` cannot rewrite, satisfying D1 and D3
      - Scope check: pass — only AGENTS.md changed, which is the single Touch path
      - Findings: none
    - Blocker: none

- [x] 1.2 Delete the follow-up-backlog change directory and its never-synced spec delta
  - Covers:
    - D2 retire the directory rather than reshape it into a storage-only store
    - D4 the change carries no spec delta and archives without a sync
    - keel-stateless-continuity / Keel resolves continuity conservatively / Storage-only standing backlog does not create ambiguity
  - Touch:
    - openspec/changes/follow-up-backlog/.openspec.yaml
    - openspec/changes/follow-up-backlog/README.md
    - openspec/changes/follow-up-backlog/proposal.md
    - openspec/changes/follow-up-backlog/tasks.md
    - openspec/changes/follow-up-backlog/specs/follow-up-ownership/spec.md
    - keel/archive/follow-ups/2026-07-27-guard-json-gitignore.md
  - Verify:
    - Strategy: evidence-first
    - M1: the openspec/changes/follow-up-backlog directory no longer exists, keel context --json no longer names follow-up-backlog in its selection, and npm test still reports every scenario passing; the one surviving deferred item is owned by GitHub issue 10 so no follow-up is lost by the deletion
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ae50ee3e6cebd7d6a2a1e1a7f07edf5d26cba1a638857353bab0dbb272f60638
    - M1: git rm -r removed all five tracked files and openspec/changes/follow-up-backlog no longer exists. keel context --json now returns status ready with selection.change retire-follow-up-backlog and selection.task 1.2 instead of the former permanent inferred pointer at follow-up-backlog with nextAction author, so the false pointer is gone. npm test reported "validation --all passed: baseline plus 58 scenarios". The one surviving deferred item is owned by https://github.com/TanglmChris/keel/issues/10, which also records the three obsolete claims it replaced, so the deletion loses no follow-up
    - Review:
      <!-- Status: one of pass, passed, complete, completed, ok, done -->
      <!-- Findings: none, or carry a durable owner — a "Discard reason:"/"Discard rationale:" prefix, a keel/archive/… path, or an existing openspec/changes/… artifact; not keel/HANDOFF.md -->
      - Status: pass
      - Acceptance check: pass — the mis-shaped standing backlog and its never-synced spec delta are gone, and context selects real work, satisfying D2 and D4
      - Scope check: pass — only the five declared Touch paths were deleted. The first task-start under-declared Touch by omitting the hidden .openspec.yaml; task-complete caught it as outside-touch, the Touch list was corrected, and the task was reauthorized at the fingerprint recorded above
      - Findings: keel/guard.json is created by keel gate task-start but is absent from this repository's .gitignore, so it surfaces as an untracked file after every gate run. Fixing it is out of scope for this task. Durable owner: keel/archive/follow-ups/2026-07-27-guard-json-gitignore.md, which carries the evidence and points at GitHub issue 11
    - Blocker: none

## Expectation Coverage

- E1: deferred follow-ups keep a durable owner that is not chat history and not keel/HANDOFF.md Covered by: 1.1
- E2: keel context stops reporting a permanent false pointer at a change nobody intends to author Covered by: 1.2
- E3: the one surviving deferred item from the retired backlog is not lost Durable owner: https://github.com/TanglmChris/keel/issues/10
- E4: the obsolete CI and npm-publish claims in the retired backlog are corrected rather than silently dropped Durable owner: https://github.com/TanglmChris/keel/issues/10
