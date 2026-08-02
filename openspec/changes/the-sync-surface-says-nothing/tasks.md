## 1. Cover the surface

- [x] 1.1 Project the overlay onto the sync surface, and derive the diagnostic from the managed set
  - Covers:
    - keel-openspec-surface-overlay / The sync surface carries the overlay that governs it
    - keel-target-surface-diagnostics / The overlay diagnostic reports every managed action
    - D1 — sync joins the managed actions rather than being handled specially
    - D2 — the sync overlay mirrors archive's structure, not its content
    - D3 — the doctor label is derived, not hardcoded
    - D4, D5 — explore stays uncovered; `sync` is not added to `authorize:`
    - F1, F2, F3, F4 — the missing marker, the identical gating, the one-sided delta note, the hardcoded label
    - A1 — every target's sync surface is at the path the projection expects
  - Touch:
    - bin/keel.js
    - .claude/commands/opsx/sync.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: installing into a fresh repository puts the overlay marker on the sync command surface and the sync skill for each target that receives it for apply and archive, and the sync surface exists at the path the projection expects on each of them
    - M2: the projected sync overlay names `keel gate change-close --action sync`, `keel-review-checklist`, and `keel openspec`, and states that sync promotes the spec delta so a following archive uses `--skip-specs`
    - M3: `keel --doctor` reports the overlay for every managed action, naming sync, and its label is derived from the managed action list rather than written separately
    - M4: the explore surface receives no overlay marker, and `sync` is not present in the standing-authorization vocabulary
    - M5 (regression): `openspec-surface-overlay` and `target-surface` stay green, so the propose, apply, and archive projections and the rest of the doctor surface are unchanged
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:fddd01f02b1359ab0dff65b2df07bc6b7ba8b449de592564c1f527f082e6c97a
    - M1: pass. New scenario `sync-surface-overlay` in `scripts/validate_plugin.py`, run as `python3.11 scripts/validate_plugin.py --scenario sync-surface-overlay`. It runs a real `keel --init` into a fresh repository for the Claude and Codex targets and asserts the overlay marker on `.claude/commands/opsx/sync.md`, `.claude/skills/openspec-sync-specs/SKILL.md`, and `.codex/skills/openspec-sync-specs/SKILL.md`. Each surface is checked to exist first, so a target whose sync surface is named differently fails by name rather than silently receiving nothing.
    - M1.red: fail. `M1 .claude/commands/opsx/sync.md carries no Keel overlay, so the surface that performs a gated action never names its gate.` This is the shipped state, not a mutation.
    - M1.green: pass, after `sync` joined `OPENSPEC_OVERLAY_ACTIONS` and the skill-name lookup became a map. The projection, the installer, and the doctor all read that one list, which is why adding the action to it covers all three at once.
    - M2: pass. The projected sync overlay names `keel gate change-close --action sync`, `keel-review-checklist`, `keel openspec`, and `--skip-specs`.
    - M2.red: fail. `M2 the sync overlay in .claude/commands/opsx/sync.md does not name that a following archive must skip specs ('--skip-specs')`, aimed by deleting that one line. It is the line most easily left out, because the archive overlay already carries the other half of the same fact — and a reader who only ever sees the sync surface would then never learn the pairing exists.
    - M2.green: pass.
    - M3: pass. `keel --doctor` names sync in its overlay line on both targets and reports it healthy after a fresh install.
    - M3.red: fail. `M3 the claude doctor overlay line does not name sync: ['Keel apply/archive overlay: ok - 8/8 under apply/archive skills and commands']`, aimed by hardcoding the label back to `apply/archive`. The red output is worth keeping: the count reads `8/8` — an internally consistent, entirely healthy-looking line that is describing two thirds of the managed set.
    - M3.green: pass. The label is derived from `OPENSPEC_OVERLAY_ACTIONS`, so an action added to the managed set cannot be left out of the diagnostic.
    - M4: pass, in both halves. The explore surface receives no overlay marker, and `sync` is absent from the standing-authorization vocabulary in `keel/config.yaml`.
    - M4.red: fail. `M4 the explore surface received an overlay. It reaches no gate and changes no state, so an overlay there reads as governance where there is none`, aimed by projecting an extra surface onto explore. A first attempt simply appended `"explore"` to the action list, which crashed `keel --init` and produced an M1 failure instead — that mutation proved nothing about M4 and was redone. The second half asserts a negative, and aiming a red at it would mean writing `keel/config.yaml`, which is outside Touch; the check was instead exercised against a synthetic document — `authorize:\n  - commit\n  - sync\n` matches and the shipped file does not — so the assertion is live rather than vacuously true.
    - M4.green: pass.
    - M5: pass. `openspec-surface-overlay` and `target-surface` both pass. `openspec-surface-overlay` failed first on the doctor label, which is declared as I1: it pinned the literal `Keel apply/archive overlay: ok`. Four occurrences were updated to the derived label, which is the pinned-wording maintenance the `## Invalidates` entry exists to make expected rather than surprising.
    - Review:
      - Status: pass
      - Acceptance check: every check runs the real `keel` binary — `--init` and `--doctor` — into a fresh repository per target and reads the files and output a user would. Both directions are covered: M1 and M2 prove the sync surface is covered and says the right things, M4 proves explore is not, so a change that projected the overlay everywhere would fail rather than pass. M3's red is the strongest evidence that the derived label was needed, since the hardcoded one reported a fully healthy `8/8` while describing a set that had grown to eleven.
      - Scope check: `git status --short` shows `bin/keel.js`, `.claude/commands/opsx/sync.md`, `.claude/skills/openspec-sync-specs/SKILL.md`, `.codex/skills/openspec-sync-specs/SKILL.md`, and `scripts/validate_plugin.py` — the Touch list exactly — plus this change's own directory, which is the record-write layer. The three projected surfaces changed because the local repository's own overlay was refreshed, which is the same projection the scenario exercises in a fixture.
      - Findings: two. First: `keel --uninstall` does not remove the overlay block from any OpenSpec surface, so after uninstalling Keel those files still instruct an agent to run `keel gate change-close` and `keel-review-checklist` — commands that no longer exist. Measured on archive as well as sync, so it is not specific to this change; found because M1 originally asserted that uninstall strips the marker "as it does from the others", which turned out to be a contract that has never existed for any action. M1 was corrected to assert only the install side and reauthorized from `sha256:950e7245…` to `sha256:fddd01f0…`. Fixing it changes `--uninstall` for all four actions and deletes content from files OpenSpec owns, which needs its own design and verification rather than being folded into a task about sync coverage. Durable owner: https://github.com/TanglmChris/keel/issues/50, which carries the measurement, why it is a defect, the implementation constraint that the two code paths do not currently meet, and the boundary that only the marked block may be removed. Second: this is the third task in two changes whose authored contract named something that was not real — a scenario that did not exist, a file that was not the right one, and now a behavior that had never shipped. Each was caught by executing the check rather than assuming it, which is the system working, but the recurrence says authored contracts are not being verified against the repository at authoring time. This task's own contract now matches what exists. Durable owner: https://github.com/TanglmChris/keel/issues/51, which records all four occurrences, separates the two mechanically decidable classes — a scenario name that is not registered, and a Touch path whose parent directory does not exist — from the one that is not, and carries a candidate check for each.
    - Blocker: none

## 2. Close

- [ ] 2.1 Release 5.14.0
  - Covers:
    - E5 — a reader of the release notes learns which of #34's layers were already delivered
    - I1, I2, I3 — the wordings this change makes stale
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
    - openspec/specs/keel-openspec-surface-overlay/spec.md
    - openspec/specs/keel-target-surface-diagnostics/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `version-alignment` passes, so every version marker names 5.14.0, including the eleven overlay markers
    - M2: `keel/CHANGELOG.md` carries a 5.14.0 entry naming the uncovered sync surface, why explore stays uncovered, that `sync` was deliberately not added to `authorize:`, and which of #34's layers were already delivered before this one
    - M3: the two spec deltas are promoted, `openspec validate the-sync-surface-says-nothing --strict` passes, and `openspec validate --specs --strict` reports errors byte-identical to those it reported before the promotion
    - M4: `npm test` passes with no failing scenario and no exception
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - M4: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Invalidates

- I1: "Keel apply/archive overlay" — the doctor label in `bin/keel.js` and every scenario asserting it. It names a hardcoded pair that stops describing the managed set the moment a third action joins it. Updated by: 1.1
- I2: "`OPENSPEC_OVERLAY_ACTIONS = [\"propose\", \"apply\", \"archive\"]`" — the constant in `bin/keel.js`, and the nine-marker count stated in the 5.11.0, 5.12.0, and 5.13.0 changelog entries as "the nine `keel:openspec-surface-overlay` markers". The count becomes eleven. The shipped changelog entries are historical records of what was true when written and are not edited; what goes stale is the standing expectation that there are nine. Updated by: 1.1, and the live count is restated by 2.1.
- I3: "version=5.13.0" — the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, `"version": "5.13.0"` in `package.json`, `package-lock.json`, and both plugin manifests, the AGENTS.md title and preflight line, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`. Updated by: 2.1

## Expectation Coverage

- E1: The surface an agent reads while syncing states the gate that decides whether the sync may complete. Covered by: 1.1
- E2: A surface added to the managed set cannot be left out of the diagnostic. Covered by: 1.1
- E3: Explore staying uncovered is a recorded decision rather than an oversight. Covered by: 1.1
- E4: Covering a surface does not widen what a repository may standing-authorize. Covered by: 1.1
- E5: A reader of the release notes learns which of #34's layers were already delivered. Covered by: 2.1
