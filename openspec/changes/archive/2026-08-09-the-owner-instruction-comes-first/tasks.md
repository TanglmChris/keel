# Tasks

## 1. `finding-owner` leads with its instruction

- [x] 1.1 Move the actionable instruction to the front of the `finding-owner` message
  - Covers:
    - keel-core-gates / A finding resolved in its own task is recorded as resolved / The actionable instruction leads the diagnostic
    - D1 — move the sentence by literal position only: same words, same clause boundaries, joined to the opening sentence with an em dash
    - D2 — verify by extending the existing core-gates scenario with three single-cause order assertions instead of one compound condition
    - D3 — spec delta is MODIFIED Requirements on the existing finding-owner requirement, adding one sentence to its prose and one new Scenario
    - F1 — grep confirmed the sentence appears in exactly three non-archive files: gates.js (the message), spec.md (the scenario), CHANGELOG.md:67 (a dated 5.28.0 entry)
    - F2 — none of the three new order checks combine a membership test with a non-membership test inside an `or`, so OR_GUARDED_ASSERTION_SITES (75) is unaffected
  - Read:
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/changes/the-owner-instruction-comes-first/design.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `finding-owner`'s message states its actionable instruction ("name a path after `Durable owner:`") before the sentence naming the `Resolved here:` form, verified by parsing the real `task-complete --json` output through the CLI, not by reading the source string.
    - M2 (regression): the `core-gates` scenario's pre-existing content assertions (all three disposition forms present, `keel/HANDOFF.md` refused as an owner) still pass, and `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if closing this needs any word of `DURABLE_OWNER_FORMS`, a disposition marker, or any other diagnostic message to change — this task is a pure reorder of one message.
    - Stop if it needs touching `#49` section 1 (bare `D<n>` Covers references reported `Missing`) — that is a separate, unresolved material decision already escalated twice to the owner.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2cf886d4ffe119cba2a511451b614ba47dfc7526fa65f59e0e10fdb56e140569
    - M1: pass. Live-CLI repro (`/tmp/keel-m1`, a standalone `openspec/changes/demo` with an unowned `Findings` entry): `node bin/keel.js gate task-complete --change demo --task 1.1 --json`, `finding-owner` message parsed from JSON reads `` Review Findings must be `none` or carry a disposition — name a path after `Durable owner:` so it reads as the owner rather than a file the finding mentions. A finding fixed in this task is `Resolved here:` naming an `M<n>` check this task declares... `` — the instruction is the second clause of the first sentence, before `Resolved here:` first appears.
    - M1.red: fail, for the right reason. `node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates` against the unfixed `src/core/gates.js`, after the three order assertions were added to `scripts/validate_plugin.py`: `` core-gates scenario: the finding-owner message states its actionable instruction after the `Resolved here:` form instead of before it. ``
    - M1.green: pass. Same command after `src/core/gates.js`'s message was reordered: `core-gates scenario passed.`
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 139 scenarios.` (139 scenarios registered; no scenario added by this task, since D2 extends the existing `core-gates` scenario rather than adding one — the count moved only because `reauthorizations-shape`, shipped in 5.33.0, is now in the baseline). `assertion-shape-count scenario passed: 75 sites, a bound on a shape and not a count of defects.` — unchanged from the recorded `OR_GUARDED_ASSERTION_SITES = 75`, confirming F2. One pre-existing pinned-literal fixture in the same `core-gates` scenario (`review-entry-extent`'s M4, asserting the unwrapped `finding-owner` message's exact text) quoted the old trailing period (`` "Review Findings must be `none` or carry a disposition." ``); updated in the same Touch-authorized file to quote the new leading clause instead, since it pins the message's literal text by design (comment at `scripts/validate_plugin.py:9759-9762`) and that text is exactly what this task changes.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that `finding-owner`'s message states its actionable instruction before the disposition enumeration, proven by M1 through the same `task-complete --json` output a real caller receives, not by reading the source string — and M1.red/M1.green show the check fails against the unfixed message and passes against the fixed one for the stated reason, not a coincidental one.
      - Scope check: `git status --short` shows exactly `src/core/gates.js` and `scripts/validate_plugin.py` — this task's whole Touch — plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at task-start (`sha256:2cf886d4ff...`), so no contract edit occurred while implementing.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release 5.34.0
  - Covers:
    - E1 — an author who receives `finding-owner` reads the actionable instruction before the three-way disposition menu
    - E2 — a reader of the release notes learns only sentence order changed and that `#49` section 1 remains open
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
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.34.0
    - M2: `keel/CHANGELOG.md` carries a 5.34.0 entry naming the `finding-owner` reorder, that it resolves `#49` section 2 only, and that section 1 stays open
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate the-owner-instruction-comes-first --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:5dacce49e9dee526bdcba38159d41f8d5f948e95f8dcf5bd61fab2ca9ff246e4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.33.0 to 5.34.0 via `node scripts/bump_version.js 5.34.0` — the package and lockfile, both plugin manifests, the `keel:start` blocks in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.34.0 - the instruction leads the menu`. It names the `finding-owner` reorder, that two prior unattended runs (2026-08-02, 2026-08-04) deferred it deliberately rather than being blocked by a material decision, that only the sentence's position moved with every word and every accepted/refused verdict unchanged, and that `#49` section 1 (bare `D<n>` reported `Missing`) is untouched and remains open.
    - M3: pass. The delta is promoted — the new sentence and the "The actionable instruction leads the diagnostic" Scenario now sit in `openspec/specs/keel-core-gates/spec.md`, inserted into the existing "A finding resolved in its own task is recorded as resolved" Requirement alongside its three unchanged Scenarios (a MODIFIED requirement, not a replacement). `node bin/keel.js openspec validate the-owner-instruction-comes-first --strict` reports `Change 'the-owner-instruction-comes-first' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding it.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 139 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking, which is what makes "every marker names 5.34.0" a measurement instead of a claim. M3 asserts the promotion through the two tools that consume the published store (`openspec validate --strict` and `published-specs-validate-strictly`) rather than by reading the file back. M2 is the one prose check, and what it asserts is what a diff alone would not show: that this reorder is the isolated diff two prior runs deliberately deferred, and that it leaves `#49` section 1 open rather than silently resolving the whole issue.
      - Scope check: `git status --short` shows twenty-three paths — this task's twenty-two Touch entries plus `src/core/gates.js` from task 1.1 — and this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at 2.1's task-start, so no contract edit occurred. `src/core/gates.js` shows modified in `git status` but is not in 2.1's Touch at all; it carries only 1.1's already-completed write, confirmed by `git diff --stat src/core/gates.js` matching the reorder recorded in 1.1's own Evidence. Every one of 2.1's twenty-two Touch paths was already dirty when 2.1 started (all twenty-one from `bump_version.js`'s own sweep plus `openspec/specs/keel-core-gates/spec.md`, which this task edited directly), so deterministic attribution cannot speak to them individually and this Review is their scope evidence: each is exactly the version bump or the spec-delta promotion this task's own Verify performed, nothing else.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "version=5.33.0" — the `keel:start` managed markers in `AGENTS.md`, `CLAUDE.md`, and
  `assets/bootstrap/AGENTS.md`; the four `.claude/commands/opsx/*.md` files; the four
  `.claude/skills/openspec-*/SKILL.md` files; the four `.codex/skills/openspec-*/SKILL.md` files;
  `"version": "5.33.0"` in `package.json`, `package-lock.json`, and both plugin manifests
  (`plugins/keel/.claude-plugin/plugin.json`, `plugins/keel/.codex-plugin/plugin.json`); and
  `PACKAGE_VERSION`/`PROTOCOL_VERSION` in `scripts/validate_plugin.py`. Updated by: 2.1
- I2: "It closes with \"Name a path after `Durable owner:` so it reads as the owner rather than
  a file the finding mentions\"" — `keel/CHANGELOG.md:67`, a 2026-08-04 entry narrating the
  cross-line-Findings fix. Discard reason: this is a dated, historical CHANGELOG entry describing
  the `finding-owner` message as it stood at the 5.28.0 release it documents ("closes with" was
  true then); it is not evergreen documentation of the message's current shape, and rewriting a
  past release's narration to match a later reorder would misrepresent what that release shipped.

## Expectation Coverage

- E1: An author whose Review `Findings` triggers `finding-owner` reads the one actionable
  instruction — name a path after `Durable owner:` — before the three-way disposition menu,
  instead of after it. Covered by: 1.1
- E2: A reader of the release notes learns that only the message's sentence order changed, that
  `DURABLE_OWNER_FORMS` and every accepted/refused verdict are unchanged, and that `#49` section 1
  (bare `D<n>` Covers references reported `Missing`) remains a separate, unresolved decision.
  Covered by: 2.1
