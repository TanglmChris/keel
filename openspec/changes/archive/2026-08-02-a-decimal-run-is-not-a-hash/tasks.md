## 1. Recognize a hexadecimal identifier by its letters

- [x] 1.1 Require a hexadecimal letter before a digit run is treated as hash-shaped
  - Covers:
    - keel-stateless-continuity / A recorded commit identifier is recognized by what makes it one / A decimal number in evidence prose is not an identifier
    - keel-stateless-continuity / A recorded commit identifier is recognized by what makes it one / A recorded hexadecimal identifier is still refused
    - keel-stateless-continuity / A recorded commit identifier is recognized by what makes it one / Recorded commit wording fails on its own
    - D1 — a hash-shaped token must carry at least one of `a`–`f`
    - D2 — the residual miss is measured and accepted
    - D3 — the three repairs that change what the rule refuses stay out
    - F1 — the criterion and where it is applied
    - F2 — the three measured false positives
    - F3 — the existing coverage that must stay green
    - A1 — the numbers in evidence prose are base-10
  - Touch:
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario decimal-runs-are-not-hash-shaped` passes. The scenario installs Keel into a temporary repository and drives `keel --check` over an active tasks.md, asserting the three shapes measured in F2 are accepted with `keel state: ok`; that a hexadecimal token of the same length beside the same context word is still refused with `keel state: failed` naming the line; and that recorded merge and completion wording carrying no such token is still refused, so the narrowing did not narrow the rule.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario cli` still passes, which is where the existing coverage of this check lives (F3).
    - M3 (regression): `npm test` passes.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0a45f92690364e21e704831deefd7de93a0f2d17ef3c01aa5079e27e1be564f1
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario decimal-runs-are-not-hash-shaped` reports `decimal-runs-are-not-hash-shaped scenario passed.` The scenario installs Keel into a temporary repository and drives the check a user runs, `keel --check`, over a real active tasks.md: each of the three shapes on its own line, then all three in one file, then the same file with a hexadecimal token of the same length beside the same context word, then work state written in words alone.
    - M1.red: fail, as required, against the branch base `df17a3d` (5.18.0). The scenario reports `an ordinary number in evidence prose was refused as a recorded identifier` beside the check's own output, `state-error openspec/changes/numbers-in-evidence/tasks.md:10: remove contextual commit hash from tasks.md; git log is the source of truth` — the reported message verbatim, reproduced through the check rather than quoted from the issue.
    - M1.green: pass. With the letter condition in place all three shapes are accepted, and the two negative assertions still hold: the hexadecimal token is refused, the refusal names its line and fails the exit status, and the wording rule refuses work state that carries no token at all. The negatives matter more than the positives here — a narrowing whose tests only prove that more things pass has not shown it kept the rule.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario cli` reports `cli scenario passed.` That is where the existing coverage lives (F3), and its fixture asserts the refusal on a token carrying two hexadecimal letters, so it is exactly the case the narrowing must not touch.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 128 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: every check runs `keel --check` over a repository holding a real tasks.md, not the compiled expression in isolation, and the red half reproduces #58's message through that path. The negative cases are asserted in the same run as the positives, because the risk in a narrowing is entirely on the side of what stops being caught.
      - Scope check: `git status --short` lists exactly `scripts/install_to_repo.py` and `scripts/validate_plugin.py`, the two Touch entries, plus this change's own untracked directory. The completion gate's attribution, recorded in this task's manifest at task start, reported no out-of-Touch path.
      - Findings: three. First, the checklist's failure-message check caught one condition guarding two distinct failures in the new scenario: `state_of()` returns `unreported` when `keel --check` printed no state at all, and every assertion compared it against the expected state, so a check that never reached a verdict would have been reported as a refusal of a line that is fine. Each assertion now tests for the absent verdict separately and says so. The three checks were re-run after the split, including the red half against the branch base, so the evidence above describes the scenario as it now stands. Resolved here: M1. Second, the residual miss this change accepts is real and is now written down rather than assumed: an abbreviated identifier that happens to carry no letter is missed, which is 3.7% of seven-character abbreviations. It is bounded by measurement — across every tasks.md in this repository's OpenSpec history, active and archived, 5,210 lines, no verdict changes — and by the wording patterns, which are untouched and catch the sentence such an identifier is usually written in. Resolved here: M1, whose negative half asserts the rule still refuses what it exists to refuse. Third, and found while authoring this very change: the wording rule refuses a tasks.md that *cites* it. A `Covers` entry must quote its requirement name verbatim, so naming the requirement after the thing it governs made `keel --check` refuse three lines of this file. The requirement was renamed to get past it — which is the same cost #58 reports, paid this time in the spec's vocabulary. The exemption that already exists covers lines *stating* the rule, not lines *citing* it. Repairing it changes which lines the rule refuses, which is the owner's decision by D3 and not this change's to make. Durable owner: https://github.com/TanglmChris/keel/issues/65
  - Blocker: none

## 2. Close

- [x] 2.1 Release 5.19.0
  - Covers:
    - E5 — a reader of the release notes learns which lines stopped being refused, which did not, and what was deliberately left alone
    - I1, I2 — the wordings this change leaves standing or makes stale
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
    - openspec/specs/keel-stateless-continuity/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.19.0
    - M2: `keel/CHANGELOG.md` carries a 5.19.0 entry naming the reported false positive, stating the property the criterion now requires, quantifying the residual miss, and recording the three repairs left to the owner and why
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate a-decimal-run-is-not-a-hash --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:37682e2bccdfaa923e70a6e32a4fd8bd14162d4ac15837d4e71efe4ab9fabe8e
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` 20 markers moved from 5.18.0 to 5.19.0 across the package and lockfile, both plugin manifests, the three `keel:start` blocks, the twelve overlay markers, the AGENTS.md title and preflight line, and the validator constants. Three occurrences of the old version deliberately stay: the two in this change's proposal and design, and the one in the new scenario's comment, which stamp a measurement with the version it was measured at.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.19.0 - a decimal run is not a hash`, naming the reported failure and what the refusal actually cost, stating the property the criterion now requires, quantifying the residual miss at 3.7% of seven-character abbreviations with both bounds on it, and recording the three repairs left to the owner as #65 with the fourth found while writing the change. It also states that this and the 5.18.0 entry together mean one rule, so neither is read as licence to move a pattern in its own direction.
    - M3: pass. The delta is promoted into `openspec/specs/keel-stateless-continuity/spec.md`, `node bin/keel.js openspec validate a-decimal-run-is-not-a-hash --strict` reports the change valid, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding this requirement.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 128 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: each release claim is checked by running what it describes rather than by inspection — the marker count by `version-alignment`, the promotion by the strict validator and by the store check 5.17.0 added, and the whole surface by the full suite.
      - Scope check: `git status --short` lists 23 modified files plus this change's own untracked directory. Every one is a Touch entry of this change: 22 belong to 2.1, and `scripts/install_to_repo.py` belongs to 1.1, which is complete but uncommitted, so its edit is still in the worktree. Nothing outside the union of the two Touch lists changed. Every version marker was written with an editor tool rather than a shell loop, so the write guard saw each one — the gap that produced the out-of-Touch write recorded against 5.15.0 and tracked as issue #53.
      - Findings: none
  - Blocker: none

## Invalidates

- I1: "#58 is the same cause with the opposite repair" — the last bullet of the 5.18.0 entry in `keel/CHANGELOG.md`, which names this issue as an open example of a criterion that over-matches. After this change the example is repaired rather than pending. Discard reason: a changelog entry is a record of what one release knew and is not rewritten by a later one. The 5.19.0 entry states the repair and refers back to it, which is where a reader following the thread is sent.
- I2: "version=5.18.0" — grep it and you find the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, plus the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`; the same version is written as `"version": "5.18.0"` in `package.json`, `package-lock.json`, and both plugin manifests, in the AGENTS.md title and its preflight line, and in the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants of `scripts/validate_plugin.py`. Updated by: 2.1

## Expectation Coverage

- E1: Evidence prose holding an ordinary decimal number is not refused as a recorded hash. Covered by: 1.1
- E2: A hexadecimal identifier of hash length beside a context word is still refused, with the same message. Covered by: 1.1
- E3: Recorded merge, completion, and working-state wording still fails on its own, independently of any digit run. Covered by: 1.1
- E4: The miss the narrowing creates is measured and written down rather than assumed negligible. Covered by: 1.1
- E5: A reader of the release notes learns what stopped being refused, what did not, and which repairs were left to the owner. Covered by: 2.1
