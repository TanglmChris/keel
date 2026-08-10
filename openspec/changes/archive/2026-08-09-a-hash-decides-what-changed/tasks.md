# Tasks

## 1. A content signature replaces the unconditional dirty-path exemption

- [x] 1.1 Attribute a dirty-at-start path only when its content changed since task start
  - Covers:
    - keel-core-gates / Dirty-worktree attribution is conservative / A path already dirty at task start whose content changed is attributed
    - keel-core-gates / Dirty-worktree attribution is conservative / A path already dirty at task start is not attributed
    - keel-touch-write-guard / The manifest records what was dirty when the task started / The recorded set carries a content signature
    - D1 — record `{path, sha256}` per dirty path instead of a bare path string, with `sha256: null` standing for "nothing to read"
    - D2 — read the current signature with the same `contentSignature` helper that builds the recorded one, exported once from `guard.js`
    - D3 — touch only the no-`--base` branch of `scopeEvidence`; the `--base` branch already has no "since task start" concept and its own scenario is unaffected
    - D4 — extend the existing `default-completion-attributes-writes` scenario with one new assertion rather than add a new scenario function
    - F1 — `scopeEvidence` has exactly one call site (`taskComplete`); `changeClose` performs no dirty-path comparison at all, so there is no second call site to touch
    - F3 — the write guard (`plugins/keel/scripts/pretooluse-guard.js`) never reads `startedDirty`; it denies by Touch membership alone
    - F4 — `plugins/keel/skills/keel-review-checklist/SKILL.md` and `src/skills/keel-review-checklist/SKILL.md` are byte-identical and both state the unconditional exemption
  - Read:
    - src/core/guard.js
    - src/core/gates.js
    - scripts/validate_plugin.py
    - plugins/keel/skills/keel-review-checklist/SKILL.md
    - openspec/changes/a-hash-decides-what-changed/design.md
  - Touch:
    - src/core/guard.js
    - src/core/gates.js
    - scripts/validate_plugin.py
    - plugins/keel/skills/keel-review-checklist/SKILL.md
    - src/skills/keel-review-checklist/SKILL.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: a path already dirty at task start that the task modifies again is attributed as outside Touch by `keel gate task-complete`'s default (no `--base`) invocation, verified through the real CLI's JSON output on a scratch git repository, not by reading the source.
    - M2 (regression): a path already dirty at task start that the task does not modify again stays exempt; the explicit-`--base` branch still attributes a path changed since that base regardless of task-start state; the no-record fallback still reports dirty paths without attributing them — every pre-existing assertion in `default-completion-attributes-writes` still passes, and `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if closing this needs adding dirty-path attribution logic to `change-close` (F1) or making the write guard read `startedDirty` (F3) — this task's whole scope is the no-`--base` branch of `scopeEvidence`, the one place the exemption is computed.
    - Stop if it needs reopening 丙 (Touch-union exemption) or 乙 (commit after every task) — both already decided against by the owner (2026-08-05, dasauto#18).
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:66665141764f9690f6a0c500e35d4217055628fd0758433443218d4defceb135
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario default-completion-attributes-writes` reports `default-completion-attributes-writes scenario passed.` after the fix, including the new assertion: a path (`src/already-dirty.js`) already dirty when the fixture task started, then modified again by the task, is now named as `outside-touch` and the gate's `status` reads `fail` — through the real CLI's JSON output, not the source.
    - M1.red: fail, for the right reason. Same command, run against the unfixed `src/core/guard.js`/`src/core/gates.js` (the new assertion was added to `scripts/validate_plugin.py` first and run before the implementation stash was popped): `default-completion-attributes-writes M2 a path already dirty at task start, then modified again by the task, was not attributed. Recording only the path (not its content) at task start exempts every later write to it, not just the one that predates the task.` — the unfixed code exempted the re-touched path unconditionally, exactly the reported defect.
    - M1.green: pass. Same command after popping the implementation stash (`src/core/guard.js` records `{path, sha256}` per dirty path; `src/core/gates.js` compares current content signature to the recorded one): `default-completion-attributes-writes scenario passed.`
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 139 scenarios.` No scenario added by this task (D4: the new assertion extends the existing `default-completion-attributes-writes` scenario rather than adding one), so the count is unchanged from before this task. `completed-sibling-attribution`, `touch-guard-drift`, and `touch-guard-surface` — the other scenarios touching dirty-path/Touch attribution — all pass unchanged. `published-specs-validate-strictly` passes against the not-yet-promoted main specs (promotion is 2.1's job). Dogfooded live: `keel guard start --force` regenerated this task's own `keel/guard.json` under the fixed code and its `startedDirty` entries now carry real `sha256` values per path.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a dirty-at-start path the task modifies again is attributed as outside Touch by `task-complete`'s default invocation, while one left untouched stays exempt — proven by M1 through the real CLI's JSON output at the public interface, not by reading the source, and M1.red/M1.green show the check fails against the unfixed comparison and passes against the fixed one for the stated reason (unconditional path-only exemption vs. conditional content-signature exemption), not a coincidental one.
      - Scope check: `git status --short` shows exactly the five Touch paths (`plugins/keel/skills/keel-review-checklist/SKILL.md`, `scripts/validate_plugin.py`, `src/core/gates.js`, `src/core/guard.js`, `src/skills/keel-review-checklist/SKILL.md`) plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at task-start (`sha256:66665141...`), so no contract edit occurred while implementing.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release 5.35.0
  - Covers:
    - E1 — a path already dirty at task start that a later task in the same change modifies again is caught by `task-complete`'s default invocation, closing the defect `#72` reproduces
    - E2 — a reader of the release notes learns the mechanism (content signature, not path name) and that 丙 and 乙 were considered and rejected by the owner before this change was authored
    - I1 — the version markers this task moves
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - scripts/validate_plugin.py
    - .claude/commands/opsx/apply.md
    - .claude/commands/opsx/archive.md
    - .claude/commands/opsx/propose.md
    - .claude/commands/opsx/sync.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
    - openspec/specs/keel-core-gates/spec.md
    - openspec/specs/keel-touch-write-guard/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.35.0
    - M2: `keel/CHANGELOG.md` carries a 5.35.0 entry naming the content-signature mechanism, that it closes `#72`, and that 丙/乙 were considered and rejected
    - M3: both spec deltas are promoted into `openspec/specs/`, `node bin/keel.js openspec validate a-hash-decides-what-changed --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:10ce7e7f7920f1f11134f8a725743f08f2d39ec7c4838e8c43a1c4183972c525
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.34.0 to 5.35.0 via `node scripts/bump_version.js 5.35.0` — the package and lockfile, both plugin manifests, the `keel:start` blocks in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.35.0 - a hash decides what changed`. It names the content-signature mechanism (sha256 or absent marker per dirty path, recorded at task-start, compared at completion), that it closes `#72`, the measured shape (81% of archived changes have ≥2 tasks, 70% of tasks are not their change's first), and that 乙 (commit per task) and 丙 (Touch-union exemption, the owner's first decision, measured to fire 458 times with a proven false positive among them) were both considered and rejected before 甲 was chosen (2026-08-05, dasauto#18).
    - M3: pass. Both delta requirements are promoted — `openspec/specs/keel-core-gates/spec.md`'s "Dirty-worktree attribution is conservative" (conditional exemption prose, the split "not attributed"/"whose content changed is attributed" scenarios, and the narrowed "Keel stores no baseline" scenario) and `openspec/specs/keel-touch-write-guard/spec.md`'s "The manifest records what was dirty when the task started" (content-signature prose and its new scenario). `node bin/keel.js openspec validate a-hash-decides-what-changed --strict` reports `Change 'a-hash-decides-what-changed' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding both.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 139 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking. M3 asserts the promotion through the two tools that consume the published store (`openspec validate --strict` and `published-specs-validate-strictly`) rather than by reading the file back. M2 is the one prose check, and what it asserts is what a diff alone would not show: that this release documents the rejected alternatives (乙, 丙) and the measurement that rejected 丙, so a future reader does not reopen either without first learning why they were declined.
      - Scope check: `git status --short` shows twenty-six paths — this task's twenty-two Touch entries plus `src/core/guard.js`, `src/core/gates.js`, `plugins/keel/skills/keel-review-checklist/SKILL.md`, and `src/skills/keel-review-checklist/SKILL.md` from task 1.1 (already checked and completed) — and this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at 2.1's task-start, so no contract edit occurred. The four task-1.1 files are not in 2.1's Touch at all; each carries only 1.1's already-completed write, confirmed by `git diff --stat` on each matching the changes recorded in 1.1's own Evidence, with no further edits since. Of 2.1's twenty-two Touch paths, twenty were already dirty when 2.1 started (`bump_version.js`'s own sweep) and two were edited directly by this task (`keel/CHANGELOG.md`'s prose, and the two spec.md promotions under `openspec/specs/`) — deterministic attribution cannot speak to the twenty individually without a base, and this Review is their scope evidence: each is exactly the version bump this task's own M1 verified, nothing else.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "version=5.34.0" — the `keel:start` managed markers in `AGENTS.md`, `CLAUDE.md`, and
  `assets/bootstrap/AGENTS.md`; the four `.claude/commands/opsx/*.md` files; the four
  `.claude/skills/openspec-*/SKILL.md` files; the four `.codex/skills/openspec-*/SKILL.md` files;
  `"version": "5.34.0"` in `package.json`, `package-lock.json`, and both plugin manifests
  (`plugins/keel/.claude-plugin/plugin.json`, `plugins/keel/.codex-plugin/plugin.json`); and
  `PACKAGE_VERSION`/`PROTOCOL_VERSION` in `scripts/validate_plugin.py`. Updated by: 2.1
- I2: "A path already dirty when the task started is not attributed even if the task modified it again" — `keel/CHANGELOG.md:232-234`, a 2026-08-02 entry narrating the 5.16.0 release that first
  shipped the unconditional exemption. Discard reason: this is a dated, historical CHANGELOG entry
  describing the mechanism as it stood at the 5.16.0 release it documents; it is not evergreen
  documentation of the current mechanism, and rewriting a past release's narration to match this
  change's conditional exemption would misrepresent what that release shipped.
- I3: "a path already dirty when the task started is never attributed even if the task changed it again" — `plugins/keel/skills/keel-review-checklist/SKILL.md` and
  `src/skills/keel-review-checklist/SKILL.md` (byte-identical, F4). Updated by: 1.1
- I4: "A path that was already dirty when the task started is not attributed to that task even if the task modified it again" — `openspec/specs/keel-core-gates/spec.md`, the "Dirty-worktree
  attribution is conservative" requirement's prose. Updated by: 2.1 (spec promotion)
- I5: "AND THEN the outcome is the same whether or not the task modified that path again" — `openspec/specs/keel-core-gates/spec.md`, the "A path already dirty at task start is not attributed"
  scenario under the same requirement. Updated by: 2.1 (spec promotion)
- I6: "Keel does not persist a diff snapshot, hash set, or execution baseline for later completion" — `openspec/specs/keel-core-gates/spec.md`, the "Keel stores no baseline" scenario under the same
  requirement. This change adds the first hash set `task-start` persists (a per-path content
  signature), scoped to the dirty-at-start attribution the same requirement documents. Updated by:
  2.1 (spec promotion)
- I7: "The guard manifest MUST record the repository's dirty-path set" with no mention of content — `openspec/specs/keel-touch-write-guard/spec.md`, the "The manifest records what was dirty when the
  task started" requirement's prose, which describes a bare path record. Updated by: 2.1 (spec
  promotion)

## Expectation Coverage

- E1: A path already dirty at task start that a later task in the same change modifies again is
  attributed as outside Touch by `keel gate task-complete`'s default invocation, instead of being
  silently exempt for the rest of the task's life — the defect `#72` reproduces and measured as the
  common case (70% of tasks are not their change's first). Covered by: 1.1
- E2: A reader of the release notes learns that the exemption is now conditioned on content, not
  merely on the path having been dirty at task start, and that 丙 (Touch-union exemption) and 乙
  (commit after every task) were both considered and rejected by the owner before this change was
  authored, so neither is reopened by a future run reading the issue fresh. Covered by: 2.1
