# Tasks

## 1. Name the confusion, and say it where a session reads first

- [x] 1.1 `sync` gets a specific sentence; `keel context` reports the same failure `--doctor` does
  - Covers:
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary / A `sync` entry names the `change-close --action` confusion specifically
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary / `keel context` reports the same failure without a separate `--doctor` call
    - D1 — detect the confusion by simple membership on `unknown.includes("sync")`, no general "did you mean" mechanism
    - D2 — move message construction into `src/core/config.js` as one function both `bin/keel.js` and `src/core/context.js` read, so the two surfaces cannot re-diverge
    - D3 — `keel context`'s warning is the same full string `--doctor` prints, not a pointer telling the reader to go run `--doctor`
    - D4 — spec delta is `MODIFIED Requirements` on the existing "A repository declares standing authorization in a closed vocabulary" Requirement, adding two Scenarios
    - F1 — `config.js` carries no reference to `sync` today; this task introduces the one literal, scoped to message text, `STANDING_AUTHORIZATION_ACTIONS` unchanged
    - F2 — `validate_standing_authorization_declaration_scenario`'s M3 fixture uses `deploy`, not `sync`, so it is unaffected by the new sentence
  - Read:
    - src/core/config.js
    - bin/keel.js
    - src/core/context.js
    - openspec/changes/a-value-is-not-a-name/design.md
  - Touch:
    - src/core/config.js
    - bin/keel.js
    - src/core/context.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: an `authorize:` block listing `sync` produces a `keel --doctor` message naming `sync` as a `change-close --action` value and pointing at `archive`, verified through the real CLI's combined stdout/stderr, not by reading the source string; a block listing an unrelated unrecognized name (`deploy`) does not gain that sentence.
    - M2: the same broken declaration's failure appears in `keel context --json`'s `warnings`, with `status` and `nextAction` unchanged by it, verified through the real CLI's JSON output.
    - M3 (regression): `standing-authorization-declaration` and `sync-surface-overlay` still pass, and `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if closing this needs adding `sync` to `STANDING_AUTHORIZATION_ACTIONS` — that widens what `authorize:` accepts, an owner decision `sync-surface-overlay` (`#54`, M4) already answered the other way for this repository's own declaration.
    - Stop if it needs a general "did you mean" / edit-distance mechanism — out of scope per the design's Non-Goals; this task names one specific, reported confusion.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:12998cd5da9708d8fb12efc5925c30519177a5c23d4dd08dc39e69eb257e3ee1
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization-sync-confusion` reports `standing-authorization-sync-confusion scenario passed.` A fresh repo declaring `authorize:\n  - sync\n` makes `keel --doctor` print `` `sync` is a value of `change-close --action`, not a name `authorize:` accepts; declare `archive` if you mean to authorize the gate that runs it. ``, while one declaring `authorize:\n  - deploy\n` still reports `deploy` as unrecognized and does not gain that sentence.
    - M1.red: fail, for the right reason. Same command run before implementation (test added to `scripts/validate_plugin.py` first): `standing-authorization-sync-confusion M1 the doctor message does not name the sync confusion: 'change-close --action'.` — the unfixed message named `sync` as unrecognized but said nothing about `change-close --action` or `archive`.
    - M1.green: pass. Same command after `src/core/config.js`'s `standingAuthorizationUnknownMessage` and `bin/keel.js`'s `printStandingAuthorizationSurface` were fixed: `standing-authorization-sync-confusion scenario passed.`
    - M2: pass. Same scenario run (M2 assertions inside it): the `sync` repo's `keel context --json` reports the same message in `warnings`, with `status: "idle"` and `nextAction.kind: "none"` unchanged; the `deploy` repo's `keel context --json` reports `deploy` in `warnings` without the `change-close --action` sentence.
    - M2.red: fail, for the right reason. Isolated by stashing only `src/core/context.js` (keeping the M1 fix in `config.js`/`bin/keel.js` applied) and rerunning: `standing-authorization-sync-confusion M2 \`keel context\` did not report the broken authorize: declaration. warnings: []` — `keel context` reported no warning at all before this task's `context.js` change.
    - M2.green: pass. Same command after popping the stash (`src/core/context.js`'s `resolveContext` restored): `standing-authorization-sync-confusion scenario passed.`
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization-declaration` reports `standing-authorization-declaration scenario passed.`; `node scripts/run_python.js scripts/validate_plugin.py --scenario sync-surface-overlay` reports `sync-surface-overlay scenario passed.`; `npm test` reports `validation --all passed: baseline plus 140 scenarios.` (140 scenarios registered; one added by this task, `standing-authorization-sync-confusion`, up from the prior baseline of 139).
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a `sync` entry in `authorize:` gets a sentence naming the `change-close --action` confusion and pointing at `archive`, in both `keel --doctor` and `keel context --json`'s warnings, while an unrelated typo (`deploy`) and `keel context`'s `status`/`nextAction` are unaffected — proven by M1/M2 through the real CLI's stdout/stderr and JSON output, not by reading the source, and M1.red/M2.red (M2.red isolated by stashing only the `context.js` half of the fix) show each half fails against its own unfixed code for the stated reason, not a coincidental one.
      - Scope check: `git status --short` shows exactly the four Touch paths (`bin/keel.js`, `scripts/validate_plugin.py`, `src/core/config.js`, `src/core/context.js`) plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at task-start (`sha256:12998cd5da...`), so no contract edit occurred while implementing.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release 5.36.0
  - Covers:
    - E1 — a reader whose `authorize:` block lists `sync` learns from `keel --doctor` that it is a `change-close --action` value, not a name to declare, and is told to declare `archive` instead
    - E2 — a session that runs `keel context` first learns the same declaration is broken without a separate `--doctor` call
    - E3 — a reader of the release notes learns that `authorize:`'s accepted vocabulary is unchanged — `sync` was not added — and why
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
    - openspec/specs/keel-standing-authorization/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.36.0
    - M2: `keel/CHANGELOG.md` carries a 5.36.0 entry naming the `sync`/`change-close --action` clarification, the `keel context` surfacing, and that `authorize:`'s accepted vocabulary is unchanged
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate a-value-is-not-a-name --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f03325c895d0467a47372c3e862d8ab24e6ef84229f8d70d348a801c44216d47
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.35.0 to 5.36.0 via `node scripts/bump_version.js 5.36.0` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.36.0 - a value is not a name`, naming the `sync`/`change-close --action` clarification in `keel --doctor`, the new `keel context` warning, and that `authorize:`'s accepted vocabulary (`commit`, `push`, `release`, `archive`) is unchanged because `sync-surface-overlay` (`#54`, M4) already answered that question.
    - M3: pass. The delta is promoted — the two new Scenarios and the modified Requirement prose now sit in `openspec/specs/keel-standing-authorization/spec.md`, alongside the three pre-existing Scenarios reproduced verbatim. `node bin/keel.js openspec validate a-value-is-not-a-name --strict` reports `Change 'a-value-is-not-a-name' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding it.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 140 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all rather than spot-checking, which is what makes "every marker names 5.36.0" a measurement instead of a claim. M3 asserts the promotion through the two tools that consume the published store (`openspec validate --strict` and `published-specs-validate-strictly`) rather than by reading the file back. M2 is the one prose check, and what it asserts is what a diff alone would not show: that this release adds a diagnostic sentence and a `keel context` warning, and explicitly does not widen `authorize:`'s vocabulary.
      - Scope check: `git status --short` shows twenty-three paths — this task's twenty-two Touch entries (the `bump_version.js` sweep plus the direct edit to `openspec/specs/keel-standing-authorization/spec.md`) — plus `src/core/config.js`, `src/core/context.js`, and `bin/keel.js` from task 1.1, already declared complete and unrelated to this task's own writes; and this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at 2.1's own task-start, so no contract edit occurred while implementing.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: A reader whose `authorize:` block lists `sync` learns from `keel --doctor` that it is a
  `change-close --action` value, not an `authorize:` name, and is told to declare `archive`
  instead if that was the intent. Covered by: 1.1
- E2: A session that runs `keel context` first (per `AGENTS.md`) learns a broken `authorize:`
  declaration is dead without a separate, explicitly-invoked `--doctor` call. Covered by: 1.1
- E3: `authorize:`'s accepted vocabulary — `commit`, `push`, `release`, `archive` — is unchanged;
  `sync` is not added, because this repository's own `sync-surface-overlay` scenario (`#54`, M4)
  already answered that question the other way. Covered by: 1.1, 2.1
