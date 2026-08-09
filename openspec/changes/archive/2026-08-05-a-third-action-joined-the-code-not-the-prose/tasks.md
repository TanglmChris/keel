# Tasks

## 1. Align spec prose to the derived action set

- [x] 1.1 Seven lines across two spec deltas name `sync` alongside `apply` and `archive`
  - Covers:
    - keel-openspec-surface-overlay / Keel refreshes existing overlays idempotently / Install refreshes an existing overlay
    - keel-openspec-surface-overlay / Keel refreshes existing overlays idempotently / Install skips missing OpenSpec files
    - keel-openspec-surface-overlay / Thin CLI owns OpenSpec initialization and overlays only / Codex init uses plugin plus official OpenSpec
    - keel-target-surface-diagnostics / Missing Keel overlays are visible / Missing overlay marker is reported
    - D1 — classify each flagged line against the code it describes rather than treating every grep hit as drift
    - D2 — the seven changed lines all use exactly `apply/archive/sync`, matching `overlayActionLabel()`
    - D3 — `keel-openspec-surface-overlay/spec.md:7` stays unchanged; its own requirement is deliberately apply+archive-scoped
    - D4 — `keel-openspec-surface-overlay/spec.md:121` extends its existing `authoring/apply/archive` phrasing rather than inventing a new one
    - D5 — the Purpose line is filed as `TanglmChris/keel#86` rather than hand-edited outside archive/sync
    - F3 — `refreshOpenSpecSurfaceOverlay`/`openspecOverlaySurfacesForTarget` already apply idempotent refresh uniformly across managed actions
    - F4 — doctor's status line already reads `Keel ${overlayActionLabel()} overlay`, i.e. names sync today
  - Read:
    - openspec/specs/keel-openspec-surface-overlay/spec.md
    - openspec/specs/keel-target-surface-diagnostics/spec.md
    - bin/keel.js
    - openspec/changes/a-third-action-joined-the-code-not-the-prose/design.md
    - openspec/changes/a-third-action-joined-the-code-not-the-prose/proposal.md
  - Touch:
    - openspec/changes/a-third-action-joined-the-code-not-the-prose/specs/keel-openspec-surface-overlay/spec.md
    - openspec/changes/a-third-action-joined-the-code-not-the-prose/specs/keel-target-surface-diagnostics/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node bin/keel.js openspec validate a-third-action-joined-the-code-not-the-prose --strict` passes, confirming both delta specs parse and resolve against their published capabilities.
    - M2: the delta specs contain `apply/archive/sync` exactly seven times combined (four in `keel-openspec-surface-overlay`, three in `keel-target-surface-diagnostics`) and zero remaining bare `apply/archive` occurrences, matching the seven lines D1/D2 selected.
    - M3 (regression): `npm test` passes with no failing scenario — this change touches no code, so the full suite is unaffected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if closing this needs a code change to `overlayActionLabel()`, `openspecOverlaySurfacesForTarget`, or `refreshOpenSpecSurfaceOverlay` — this task is prose-only.
    - Stop if resolving the Purpose-line drift (`#86`) turns out to be required for this task's own Acceptance rather than a genuinely separate follow-up.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:fffa4147a50e9b7c677744b3d2ad86b50f829e65a7233e2e64e7ec7b3cfecad8
    - M1: pass. `node bin/keel.js openspec validate a-third-action-joined-the-code-not-the-prose --strict` reports `Change 'a-third-action-joined-the-code-not-the-prose' is valid`.
    - M2: pass. `grep -c "apply/archive/sync" openspec/changes/a-third-action-joined-the-code-not-the-prose/specs/keel-openspec-surface-overlay/spec.md` reports 4; the same grep against `specs/keel-target-surface-diagnostics/spec.md` reports 3; total 7. `grep -rn "apply/archive" openspec/changes/a-third-action-joined-the-code-not-the-prose/specs/ | grep -v "apply/archive/sync"` returns nothing — no bare occurrence remains in either delta.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 138 scenarios.`, including `published-specs-validate-strictly scenario passed: 21 published specs validate strictly against openspec 1.6.0.` — unaffected, since the published store is untouched until 2.1.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the delta specs name `sync` alongside `apply`/`archive` everywhere the described behavior already covers it, without touching the one requirement (line 7) that is deliberately apply+archive-scoped. M1 proves the delta is structurally valid against its published capabilities; M2 proves the count matches exactly the seven lines D1/D2 selected (not more, not fewer) by counting the derived label string directly rather than trusting the diff by eye.
      - Scope check: `git status --short` shows exactly this change's own untracked directory (the record-write layer) plus `keel/guard.json`, which the guard itself manages. `keel guard status` reports the fingerprint unchanged from the one recorded at task-start, so no contract edit occurred. No file outside `openspec/changes/a-third-action-joined-the-code-not-the-prose/` was touched; the two delta spec files match this task's Touch exactly.
      - Findings: none
    - Blocker: none

## 2. Close

- [x] 2.1 Sync, archive, and release 5.31.0
  - Covers:
    - E1 — a reader of the published specs learns Keel's overlay covers apply, archive, and sync from the prose itself, not only from CLI output
    - E2 — a reader of the release notes learns which lines drifted, why one line was deliberately left alone, and why one line is tracked separately as `#86`
    - I1 — the `apply/archive` wording this task promotes past
    - I2 — the `authoring/apply/archive` wording this task promotes past
    - I3 — the `apply/archive` wording in the diagnostics requirement this task promotes past
  - Read:
    - keel/CHANGELOG.md
    - openspec/changes/a-third-action-joined-the-code-not-the-prose/specs/keel-openspec-surface-overlay/spec.md
    - openspec/changes/a-third-action-joined-the-code-not-the-prose/specs/keel-target-surface-diagnostics/spec.md
  - Touch:
    - openspec/specs/keel-openspec-surface-overlay/spec.md
    - openspec/specs/keel-target-surface-diagnostics/spec.md
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
  - Verify:
    - Strategy: evidence-first
    - M1: after the two delta requirements are agent-applied into `openspec/specs/`, `grep -rn "apply/archive" openspec/specs/ | grep -v "apply/archive/sync" | wc -l` reports 2 (the two documented residuals: line 7, and the Purpose line tracked as `#86`).
    - M2: `node bin/keel.js openspec validate a-third-action-joined-the-code-not-the-prose --strict` passes (pre-archive).
    - M3: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.31.0.
    - M4: `keel/CHANGELOG.md` carries a 5.31.0 entry naming the nine-line measurement, the seven lines fixed, the one kept intentionally (D3), and the one filed as `#86` (D5).
    - M5: `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes against the promoted store.
    - M6 (regression): `npm test` passes with no failing scenario and no exception.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
    - Stop if sync produces a published-spec diff beyond the seven lines D1/D2 selected.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:57d6a01f93ed97eb53e6e5b5c68655563ebdda60d4f9d0802dedb3bc4ecb7c6e
    - M1: pass. After agent-applying the two `MODIFIED Requirements` deltas into `openspec/specs/keel-openspec-surface-overlay/spec.md` and `openspec/specs/keel-target-surface-diagnostics/spec.md`, `grep -rn "apply/archive" openspec/specs/ | grep -v "apply/archive/sync" | wc -l` reports 2 — line 3 (Purpose, `#86`) and line 7 (D3) in `keel-openspec-surface-overlay/spec.md`.
    - M2: pass. `node bin/keel.js openspec validate a-third-action-joined-the-code-not-the-prose --strict` reports `Change 'a-third-action-joined-the-code-not-the-prose' is valid`.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` after `node scripts/bump_version.js 5.31.0` moved every marker: package/lockfile, both plugin manifests, the `keel:start` blocks in `AGENTS.md`/`CLAUDE.md`/`assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers, and `PACKAGE_VERSION`/`PROTOCOL_VERSION` in `scripts/validate_plugin.py`.
    - M4: pass. `keel/CHANGELOG.md` carries `## 5.31.0 - a third action joined the code, not the prose`, naming the nine-line measurement, the seven fixed lines and why, the one line kept intentionally (D3) and why, and the one line filed as `#86` (D5) and why the delta mechanism cannot reach it.
    - M5: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` reports `published-specs-validate-strictly scenario passed: 21 published specs validate strictly against openspec 1.6.0.`
    - M6: pass. `npm test` reports `validation --all passed: baseline plus 138 scenarios.` — no failing scenario, no exception, none added (this change is prose-only).
    - Review:
      - Status: pass
      - Acceptance check: M1 is the scenario that reads the promoted store directly rather than trusting the edit by eye, and its count (2 residual) matches D1-D5's classification exactly — not more, not fewer. M2 and M5 assert the promotion through the two tools that consume it (`openspec validate --strict` and `published-specs-validate-strictly`), not by reading the file back. M4 is the one prose check, and what it asserts is what a reader cannot reconstruct from the diff alone: that a third of the original nine lines were deliberately not touched, and why.
      - Scope check: `git status --short` shows exactly this task's Touch — the two published spec files, every version marker `bump_version.js` reported, and `keel/CHANGELOG.md` — plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at this task's task-start, so no contract edit occurred since the M7 removal was re-recorded. No file outside Touch or the change's own directory appears in `git status`.
      - Findings: none
    - Blocker: none
    - Blocker: none

## Invalidates

- I1: "an apply/archive OpenSpec file" / "apply/archive files" — the "Keel refreshes existing
  overlays idempotently" requirement in `openspec/specs/keel-openspec-surface-overlay/spec.md`
  (lines 34, 41, 42). Updated by: 2.1
- I2: "authoring/apply/archive overlays" — the "Thin CLI owns OpenSpec initialization and
  overlays only" requirement in `openspec/specs/keel-openspec-surface-overlay/spec.md` (line 121).
  Updated by: 2.1
- I3: "distinguish missing apply/archive overlay markers" / "apply/archive OpenSpec file" /
  "apply/archive overlay as missing" — the "Missing Keel overlays are visible" requirement in
  `openspec/specs/keel-target-surface-diagnostics/spec.md` (lines 115, 119, 121). Updated by: 2.1

## Expectation Coverage

- E1: A reader of `openspec/specs/keel-openspec-surface-overlay/spec.md` and
  `openspec/specs/keel-target-surface-diagnostics/spec.md` learns from the prose alone that Keel's
  overlay covers apply, archive, and sync — not only from `keel --doctor` or `--install` output.
  Covered by: 1.1, 2.1
- E2: A reader of the release notes learns which nine lines were measured, which seven changed,
  why one requirement was deliberately left naming only apply and archive, and why the Purpose line
  is tracked separately as `TanglmChris/keel#86` rather than fixed here. Covered by: 2.1
