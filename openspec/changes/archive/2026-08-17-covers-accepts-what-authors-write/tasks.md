# Tasks

## 1. Accept the shapes authors write

- [x] 1.1 `criticalAuthority()` resolves a `design.md` critical-statement line written bare, bulleted (`-`, `*`, or `+`), bold-wrapped, or bulleted-bold, keeps failing a reference that matches more than one line as duplicated, and the `Unparsed` message names the accepted shapes instead of refusing decoration
  - Covers:
    - keel-expectation-slice-evidence-gates / Critical-statement lines are accepted in the shapes authors write
    - keel-expectation-slice-evidence-gates / Unresolved critical-statement Covers references distinguish missing from unparsed
    - D1
    - D4
    - F1
    - F2
    - F3
  - Read:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - openspec/changes/covers-accepts-what-authors-write/design.md
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `widened-critical-statement-shapes` scenario in `scripts/validate_plugin.py` runs `keel gate task-start` through the real CLI: `design.md` fixtures `- D2 — Keep one shared parser.`, `**D2** — Keep one shared parser.`, `- **D2** — Keep one shared parser.`, `* D2 — Keep one shared parser.`, and `+ D2 — Keep one shared parser.` each resolve the Covers reference `D2` as critical-statement authority carrying the statement text; a `design.md` carrying D2 both bare and bulleted fails as duplicated; a `D2: colon line` fixture still fails as `Unparsed` with a message naming the bulleted and bold shapes as accepted.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario unparsed-covers-critical-statement` passes with its present-but-mis-shaped fixture moved to a still-unaccepted shape, still distinguishing `Missing` (absent identifier) from `Unparsed` (present, unaccepted shape) and still resolving the bare shape.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario expectation-slice-gates` passes unchanged.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if resolving the widened shapes requires touching `specAuthority()` or changing the duplicate verdict.
    - Stop if any accepted-shape fixture resolves with statement text different from its bare-shape equivalent.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2b8f0376e4fbd6eb3c018c112c6a91aa520a840d4418babfc77d9d11ef66103d
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario widened-critical-statement-shapes` reports `widened-critical-statement-shapes scenario passed.` — all five accepted-shape fixtures resolve as critical-statement authority carrying `Keep one shared parser.`, the bare-plus-bulleted duplicate fails as `Duplicated Covers critical statement: D2.`, and the colon fixture reports `Unparsed` naming the bulleted and bold shapes.
    - M1.red: fail, for the right reason. Scenario added to `scripts/validate_plugin.py` before touching `task-contract.js`: `widened-critical-statement-shapes: the shape '- D2 — Keep one shared parser.' must resolve, got exit 3` — the unmodified `criticalAuthority()` refuses the bulleted shape as `Unparsed`.
    - M1.green: pass. Same command after `criticalAuthority()`'s line regex gained the optional bullet and balanced-bold alternatives and the `Unparsed` message named the accepted shapes: `widened-critical-statement-shapes scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario unparsed-covers-critical-statement` reports `unparsed-covers-critical-statement scenario passed.` with its present-but-mis-shaped fixture moved to the colon shape `D2: Keep one shared parser.`; `Missing` for an absent identifier, `Unparsed` for a present unaccepted shape, and bare-shape resolution all hold.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario expectation-slice-gates` reports `expectation-slice-gates scenario passed.` unchanged.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 144 scenarios.` (up from 143; the one new scenario this task added is the only change, no other scenario affected.)
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a design.md critical-statement line written bare, bulleted (`-`, `*`, or `+`), bold-wrapped, or bulleted-bold resolves as Covers authority with the statement text, a reference matching more than one line still fails as duplicated, and a still-unaccepted shape reports `Unparsed` naming the accepted shapes — proven by M1 through the real CLI against all seven fixtures, M1.red/M1.green showing the scenario fails against the unmodified parser for the stated reason and passes after the widening, and M2 showing Missing/Unparsed distinction survives with the mis-shaped fixture moved to a shape that stays unaccepted.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/task-contract.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel gate task-complete` reports the fingerprint unchanged from the one recorded at task-start.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 A Covers entry that opens with a `D<n>`/`F<n>`/`A<n>`/`Q<n>` identifier followed by a dash and trailing text resolves as that critical statement — failing loudly when the identifier is missing — while colon-form entries and hyphenated free text like `D2-compatible` stay free-text references
  - Covers:
    - keel-task-capsule / A critical-statement Covers entry may carry a trailing annotation
    - D2
    - D3
    - D5
    - F1
  - Read:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - openspec/changes/covers-accepts-what-authors-write/design.md
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `covers-annotation-entry` scenario in `scripts/validate_plugin.py` runs `keel gate task-start` through the real CLI: a Covers entry `D2 — an annotation` with a bare-shaped D2 in `design.md` resolves as critical-statement authority whose text is the `design.md` statement, not the annotation; the same entry with no D2 anywhere in `design.md` fails with `Missing Covers critical statement: D2.`; a Covers entry `E1: Public behavior passes.` and an entry opening `D2-compatible fixture text` (with D2 present in `design.md`) both remain `legacy-task-reference` and pass.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario expectation-slice-gates` passes unchanged.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the entry boundary (whitespace or em dash after the identifier) cannot keep `D2-compatible` free text without also rejecting `D2 — annotation`.
    - Stop if resolving the entry requires treating the annotation as authority text or comparing it against `design.md`.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:26f01c661a0affb20441419666f305ab9e3a141b759086b080f3b078ff5131e5
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario covers-annotation-entry` reports `covers-annotation-entry scenario passed.` — `D2 — an annotation` resolves as critical-statement authority whose text is the design.md statement and not the annotation; the same entry with no D2 in design.md fails with `Missing Covers critical statement: D2.`; `E1: Public behavior passes.` and `D2-compatible fixture text` both remain passing `legacy-task-reference` entries.
    - M1.red: fail, for the right reason. Scenario added before touching `resolveAuthority()`: `covers-annotation-entry: 'D2 — an annotation' must resolve as critical-statement authority carrying the design.md statement text, got: [{'kind': 'legacy-task-reference', 'reference': 'D2 — an annotation', …}]` — the unmodified classifier silently downgrades the entry and never checks the link.
    - M1.green: pass. Same command after `resolveAuthority()` gained the opens-the-entry match (`^([DFAQ]\d+)(?=\s|—)\s*[—-]\s*.+$`): `covers-annotation-entry scenario passed.` One scenario-side calibration between red and green: the fixture's design.md line dropped its `Basis: fixture authority.` tail so the statement-text assertion compares the exact captured text; the behavior assertions were not loosened.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario expectation-slice-gates` reports `expectation-slice-gates scenario passed.` unchanged.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 145 scenarios.` (up from 144; the one new scenario this task added is the only change, no other scenario affected.)
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a Covers entry opening with a critical-statement identifier and a dash resolves as that statement — carrying design.md's text, failing as Missing when the identifier is absent — while colon-form and hyphenated free text stay free-text references, proven by M1 through the real CLI against all four fixtures and M1.red/M1.green showing the unmodified classifier silently downgraded the entry and the new match resolves it. The lookahead boundary kept `D2-compatible` free text without rejecting `D2 — an annotation`, so neither Stop Rule fired.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/task-contract.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel gate task-complete` reports the fingerprint unchanged from the one recorded at task-start.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a design.md critical statement written bulleted, bold, or bulleted-bold resolves as Covers authority
    - E2 — a Covers entry opening with a critical-statement identifier and a dash resolves as that statement or fails loudly, never silently degrading
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
    - openspec/specs/keel-expectation-slice-evidence-gates/spec.md
    - openspec/specs/keel-task-capsule/spec.md
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
    - M2: `keel/CHANGELOG.md` carries an entry naming the widened critical-statement shapes and the Covers annotation-entry resolution, closing issue #49 Section 1
    - M3: both spec deltas are promoted into `openspec/specs/`, `node node_modules/.bin/openspec validate covers-accepts-what-authors-write --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3bbd9c8855025e20d02a993fc39086a2d97e69de5fce9c0fa913b72d3e16b05a
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.39.0 to 5.40.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.40.0 - covers accepts what authors write`, naming the widened design.md line shapes (with the 3/45/15 measurement and the shipped template teaching the bulleted shape), the Covers annotation-entry resolution with the fail-open reproduction, and the supersession of the 5.38.0 entry's shape description, closing issue #49 Section 1.
    - M3: pass. Both deltas are promoted — `openspec/specs/keel-expectation-slice-evidence-gates/spec.md` carries the reworded missing/unparsed requirement plus the new `Critical-statement lines are accepted in the shapes authors write` requirement, and `openspec/specs/keel-task-capsule/spec.md` carries `A critical-statement Covers entry may carry a trailing annotation`. `node node_modules/.bin/openspec validate covers-accepts-what-authors-write --strict` reports `Change 'covers-accepts-what-authors-write' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the promoted store.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 145 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking. M3 asserts the promotion through the two tools that consume the published store (`openspec validate --strict` and `published-specs-validate-strictly`) rather than by reading the files back. M2 is the one prose check, and what it asserts is what a diff alone would not show: this release widens what the gate accepts because the owner decided the old strictness was silently skipping the check, and it names the supersession of the 5.38.0 wording instead of leaving two entries that contradict each other without comment.
      - Scope check: `git status --short` shows exactly the Touch entries this task wrote — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, both promoted spec files, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `src/core/task-contract.js` and `scripts/validate_plugin.py`'s scenario additions from tasks 1.1 and 1.2, already declared complete and unrelated to this task's own writes, plus this change's own untracked directory, the record-write layer.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "(no leading `-`, `**`, or other decoration)" — the `Unparsed` message in `src/core/task-contract.js`
  and the `"D2 — one-line statement"` shape assertion in `scripts/validate_plugin.py`; both describe the
  pre-widening boundary as the required shape. Updated by: 1.1
- I2: "not at the start of a line followed by a dash (for example, wrapped in bullet or bold markup)" —
  the published scenario in `openspec/specs/keel-expectation-slice-evidence-gates/spec.md` names bullet
  and bold wrapping as the mis-shaped example, and those shapes now resolve. Updated by: 2.1
- I3: "now reports `Unparsed Covers critical statement: <ref>.`, naming the required shape" for a
  bullet-or-bold-wrapped identifier — `keel/CHANGELOG.md`'s 5.38.0 entry describes that boundary as
  current behavior. Discard reason: dated release history; the new release's entry records the
  supersession, and rewriting past entries would falsify the record.

## Expectation Coverage

- E1: A design.md critical statement written bulleted, bold, or bulleted-bold resolves as Covers authority. Covered by: 1.1, 2.1
- E2: A Covers entry opening with a critical-statement identifier and a dash resolves as that statement or fails loudly, never silently degrading. Covered by: 1.2, 2.1
