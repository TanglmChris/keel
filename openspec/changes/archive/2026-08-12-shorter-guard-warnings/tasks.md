# Tasks

## 1. Shorten the two standing guard warnings

- [x] 1.1 Reword `guardResult`'s durability and enforcement-boundary warnings for brevity, keeping every required idea
  - Covers:
    - keel-touch-write-guard / Guard capability is reported from observed evidence / Standing warnings may be reworded for brevity without dropping an idea
    - keel-touch-write-guard / Guard capability is reported from observed evidence / Guard status describes the manifest, not enforcement
    - D1 — keep two warning strings, one per concern, not merged into one
    - D2 — drop "in the host" / "from the repository" explanatory clauses from the enforcement-boundary sentence
    - D3 — drop "the only" from "the only durable authority"
    - F1 — `#92`'s measurement (398/397 chars) reproduces on the live tree before this task
  - Read:
    - src/core/guard.js
    - scripts/validate_plugin.py
    - openspec/changes/shorter-guard-warnings/design.md
  - Touch:
    - src/core/guard.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `keel guard status` and `keel guard clear`, run in a fresh directory with no manifest, each produce output strictly shorter than the 398/397-char baseline `#92` measured, verified through the real CLI's combined stdout, not by reading the source string.
    - M2 (regression): `guard-status-is-not-enforcement` still passes — every needle (`enforcement`, `runtime hook`, `cannot observe`, `durable authority`) still resolves and no forbidden assertive-enforcement phrase appears.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if satisfying M1 requires dropping an idea the existing `guard-status-is-not-enforcement` scenario checks for — that would violate the MUST at `keel-touch-write-guard/spec.md:89` the owner's authorization explicitly kept in force.
    - Stop if it requires moving either warning out of the default output (e.g. to `--verbose`) — the owner's authorization was for shortening only, not relocation.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:125fae4fc5e8d4f9a0e7aa19e29d584153047b4c8c2a9d47aebf630aaeeacb03
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario guard-warnings-are-concise` reports `guard-warnings-are-concise scenario passed.` In a fresh directory with no manifest, `keel guard status` is now 334 chars (down from the 398-char baseline) and `keel guard clear` is 333 chars (down from 397), both strictly under the pre-shortening baseline.
    - M1.red: fail, for the right reason. Scenario added to `scripts/validate_plugin.py` before touching `guard.js`: `guard-warnings-are-concise: keel guard status is 398 chars, not shorter than the 398-char baseline #92 measured before the wording was shortened.` — the unmodified wording produces exactly the pre-shortening byte count.
    - M1.green: pass. Same command after `src/core/guard.js`'s two `warnings` strings were reworded: `guard-warnings-are-concise scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario guard-status-is-not-enforcement` reports `guard-status-is-not-enforcement scenario passed.` — every needle (`enforcement`, `runtime hook`, `cannot observe`, `durable authority`) still resolves against the reworded text and no forbidden assertive-enforcement phrase appears.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 141 scenarios.` (141 scenarios registered; one added by this task, `guard-warnings-are-concise`, up from the prior baseline of 140.)
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the two standing guard warnings get measurably shorter while every required idea and the existing enforcement-honesty guarantees survive — proven by M1 through the real CLI's output in a fresh, manifest-absent directory (matching how `#92` itself measured the baseline), not by reading the source string, M1.red/M1.green showing the new scenario fails against the unmodified wording for the stated reason and passes against the reworded wording, and M2 showing the pre-existing honesty scenario is unaffected.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/guard.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at task-start (`sha256:125fae4fc5...`), so no contract edit occurred while implementing. (The guard manifest was momentarily cleared by an in-repo `keel guard clear` spot-check during measurement and immediately re-armed via `keel gate task-start --record`, which reported the identical fingerprint and "Contract anchor unchanged" — no contract drift resulted.)
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a `keel guard status`/`clear`/`start` caller sees a measurably shorter default warning text that still names the manifest as disposable, not durable authority, and still states the enforcement-hook boundary honestly
    - E2 — a reader of the release notes learns that `#92` item 1 shipped and item 2 stays open, undecided
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
    - openspec/specs/keel-touch-write-guard/spec.md
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
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry naming the guard-warning shortening and that `#92` item 2 remains undecided
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate shorter-guard-warnings --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1570e337b87b0776c410ca8d4cc349b9be40a705a287b9a422648daaab6d5336
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.36.0 to 5.37.0 via `node scripts/bump_version.js 5.37.0` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.37.0 - shorter guard warnings`, naming the guard-warning shortening (closes issue #92 item 1), the 398→334 / 397→333 char measurements, and that `#92` item 2 remains undecided because the owner did not authorize it as Full-mode work in the same decision.
    - M3: pass. The delta is promoted — the new Scenario now sits in `openspec/specs/keel-touch-write-guard/spec.md` alongside its four pre-existing Scenarios reproduced verbatim, and the Requirement text is unchanged. `node bin/keel.js openspec validate shorter-guard-warnings --strict` reports `Change 'shorter-guard-warnings' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding it.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 141 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking. M3 asserts the promotion through the two tools that consume the published store (`openspec validate --strict` and `published-specs-validate-strictly`) rather than by reading the file back. M2 is the one prose check, and what it asserts is what a diff alone would not show: this release shortens two disclaimer strings without dropping an idea, and explicitly leaves `#92` item 2 undecided rather than implying it was addressed.
      - Scope check: `git status --short` shows the Touch entries this task actually wrote — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, `openspec/specs/keel-touch-write-guard/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `src/core/guard.js` and `scripts/validate_plugin.py`'s scenario addition from task 1.1, already declared complete and unrelated to this task's own writes, plus this change's own untracked directory, the record-write layer. `keel gate task-complete` (rerun after the Touch correction below) reports `Status: pass` with no `outside-touch` problems.
      - Findings: none
    - Blocker: none
    - Reauthorizations: the first `task-start --record` recorded Touch without the twelve `keel:openspec-surface-overlay` marker files `bump_version.js` actually rewrites under `.claude/`/`.codex/` (missed when copying the Touch list from the `2026-08-12-a-value-is-not-a-name` precedent's own 2.1 task). `task-complete` failed with 12 `outside-touch` problems naming each marker file. Touch corrected to include all twelve; `task-start --record` rerun, reporting a new fingerprint (`sha256:64b567fe07...` → `sha256:1570e337b8...`) and warning that execution evidence under the previous contract was stale. M1, M3, and M4 (deterministic checks unaffected in substance by widening Touch) were rerun against the corrected contract and reconfirmed passing; M2 is unaffected since it concerns `CHANGELOG.md` content, not Touch.

## Invalidates

- I1: "Measured on 5.29.0" and the `398`/`397` char counts quoted in `#92`'s issue body and this
  change's `proposal.md`/`design.md` become historical once the wording ships — a future reader
  measuring `keel guard status` will see the new, shorter counts, not these. Durable owner:
  keel/CHANGELOG.md (this change's release entry restates the before/after numbers).

## Expectation Coverage

- E1: A `keel guard status`/`clear`/`start` caller sees a measurably shorter default warning text
  that still names the manifest as disposable, not durable authority, and still states the
  enforcement-hook boundary honestly. Covered by: 1.1, 2.1
- E2: A reader of the release notes learns `#92` item 1 shipped and item 2 stays open. Covered by: 2.1
