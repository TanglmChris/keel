# Tasks

## 1. Nothing to do here, and why

- [x] 1.1 A change declaring `keel: status: paused` in its `.openspec.yaml` is skipped by inference and named with its reason, an all-paused repository reports each reason instead of reporting nothing, explicit selection still reaches it, an unreadable declaration pauses nothing, and no gate verdict moves
  - Covers:
    - keel-stateless-continuity / A change its owner paused is not inferred as the next action
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
    - A1
    - F1
    - F2
  - Read:
    - src/core/context.js
    - scripts/validate_plugin.py
    - openspec/changes/a-paused-change-is-not-the-next-action/design.md
  - Touch:
    - src/core/context.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-paused-change-is-not-the-next-action` scenario in `scripts/validate_plugin.py` drives `keel context --json` through the real CLI against fixture repositories. With two active changes, one declaring `keel: status: paused` with a reason and one not, inference selects the unpaused change and its warnings name the paused change and quote its reason; without the declaration the same pair is `ambiguous`, so the skip is what changed the answer. With every change paused, the status is `idle` and each change and reason appears. `keel context --change <paused>` still selects it and reports that it is paused. A change whose `keel:` block is not a readable pause declaration stays available to inference and is reported. `keel gate task-start` against a task of a paused change returns the verdict it returns when the change is not paused, asserted by running the identical fixture both ways.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario stateless-continuity` passes unchanged, so handoff, storage-only, and ambiguity keep their behavior.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if pausing changes any gate verdict, because D4 records that priority is not authority and a gate refusing a paused change would make the declaration a lock nobody asked for.
    - Stop if a paused change can be skipped without being named, because D2 records that an invisible skip replaces a wrong recommendation with a hidden one.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1784039f7adb64d3039d0e6d6cde718e77a47a8360629f278ad492abac947767
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-paused-change-is-not-the-next-action` reports `a-paused-change-is-not-the-next-action scenario passed.` Two active changes with no declaration report `ambiguous`, which is the control: the skip is what changes the answer, not the fixture. Declaring `keel: status: paused` on one makes inference select the other and report `Paused change not inferred: alpha — 打分寻优要等赛题，当前优先级是不依赖工具的知识沉淀 (since 2026-09-05). Select it explicitly with \`keel context --change alpha\` if it is what you mean.` With both paused the status is `idle` and both changes and both reasons appear. `keel context --change alpha` still selects it and reports it is paused. A `keel:` block reading `status: perhaps-later` leaves the change in inference and is reported by name. `keel gate task-start` against a task of the paused change returns the same status as the identical task in the unpaused fixture.
    - M1.red: fail, for the right reason. Before `pauseDeclaration()` existed the scenario reported `inference did not pass over the paused change; 'ambiguous' 'Multiple active OpenSpec changes are plausible: alpha, beta'` — the declaration was written and nothing read it. A second red followed the first implementation: the block regex spelled the end of the `keel:` body as a lookahead for the next top-level key and matched nothing, so the declaration parsed as absent; it now matches the indented body directly.
    - M1.green: pass. Same command after inference filtered paused changes, reported each with its reason, reported an all-paused repository as `idle` with both reasons, and explicit selection reported the pause instead of hiding it.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario stateless-continuity` reports `stateless-continuity scenario passed.` Handoff, storage-only, and ambiguity keep their behavior; the pause notes are appended to the existing warning list rather than replacing it.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 166 scenarios.` — one more scenario than the 163 task 1.3 of the previous change left, plus the two that had been skipping. `native-plugin-marketplaces` and `native-plugin-install-matrix` skip when the `codex` and `claude` CLIs are absent; both are now on this machine's PATH, so they ran and passed. That is an environment change and not this task's: both were verified individually, and neither reads anything this task touched.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a paused change is skipped and named, that an all-paused repository reports each reason, that explicit selection still reaches it, that an unreadable declaration pauses nothing, and that no gate verdict moves. M1 proves all five, and two of them carry the weight. The `ambiguous` control matters because a scenario that only asserted "selects beta" would pass against an implementation that always picked the second change. The gate assertion compares the same task under both fixtures rather than checking for a particular verdict, so it holds whatever that verdict is and would catch pausing leaking into authority.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/context.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: one, still open. The declaration is read only where it is declared, so a repository with many paused changes reports one note per change on every inference — proportionate at two, noisy at twenty. The alternative, collapsing them into a count, would return to the state this change removes: a skip the reader cannot check. If a repository ever accumulates enough paused changes for the notes to crowd the output, the answer is probably that they should be archived rather than that Keel should say less about them. Durable owner: https://github.com/TanglmChris/keel/issues/112
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a paused change is not inferred and is never skipped silently
    - E2 — an all-paused repository reports each reason
    - E3 — pausing changes no gate verdict
    - I1 — the published wording this change makes stale
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
    - README.md
    - keel/CHANGELOG.md
    - scripts/validate_plugin.py
    - openspec/specs/keel-stateless-continuity/spec.md
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
    - Reason: this task's whole effect is version markers, published wording, and promoted spec text. The behavior was proven red-green in task 1.1, and nothing here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `README.md` documents the declaration with its exact shape, states that it changes only what is recommended and no gate, and says how to override it
    - M3: `keel/CHANGELOG.md` carries an entry stating what the wrong recommendation cost — a paragraph of project documentation written to cancel the tool's own output — and why the declaration is namespaced rather than written at the top level as the report suggested
    - M4: the spec delta is promoted into `openspec/specs/keel-stateless-continuity/spec.md`, `node node_modules/.bin/openspec validate a-paused-change-is-not-the-next-action --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M5: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a6ca87d1dfec3fb61262a64ba6cb809b0665a4095b48884fc2146f4979d589c5
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.53.0 to 5.54.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `README.md` gains a `## Pausing a change` section immediately before `## Commands`. It shows the exact file and the exact keys, states that a skip is always named because an invisible one would be worse than the wrong recommendation it replaces, and says plainly that no gate reads it and that `keel context --change <paused>` still selects it.
    - M3: pass. `keel/CHANGELOG.md` carries `## 5.54.0 - a paused change is not the next action`. It states what the wrong recommendation cost in the reporter's own words — a paragraph of project documentation written to cancel the tool's primary output — and why the key is namespaced under `keel:` rather than written at the top level as the report asked, distinguishing the measured fact that OpenSpec tolerates extra keys from the claim that it will never define `status` itself.
    - M4: pass. The delta is promoted — `openspec/specs/keel-stateless-continuity/spec.md` carries `A change its owner paused is not inferred as the next action` with its five scenarios. `node node_modules/.bin/openspec validate a-paused-change-is-not-the-next-action --strict` reports `Change 'a-paused-change-is-not-the-next-action' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 166 scenarios.` — the same count task 1.1 left, with no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and M4 asserts the promotion through both tools that consume the published store. M2 and M3 are the prose checks. What M2 has to carry is the boundary rather than the syntax — a reader who learned the keys but not that pausing touches no gate would reasonably fear that pausing a change locks it. What M3 has to carry is the deviation from what the reporter asked for, stated with the measurement that justified going part of the way and the reason for not going all of it.
      - Scope check: `git status --short` shows exactly this task's Touch entries — the package and lockfile, both plugin manifests, the three `keel:start` files, `README.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-stateless-continuity/spec.md`, and the twelve `.claude/`/`.codex/` marker files — plus `src/core/context.js` from task 1.1, already declared complete and untouched by this task, plus this change's own untracked directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "No active OpenSpec change was found." — the idle reason in `src/core/context.js` and the
  scenarios asserting it. A repository whose every change is paused is not a repository with no
  change, and after this release those two states report differently.
  Updated by: 1.1
- I2: "Storage-only backlog ignored during inference" — the sibling warning in the same file. It stays
  and gains a companion, so a reader searching for how inference reports what it passed over finds
  two forms rather than one.
  Discard reason: the sentence is still true of storage-only backlogs, which are derived from a change
  having no artifacts rather than declared by a person. Rewording it to cover both would merge two
  states whose difference is the point: one is Keel observing, the other is the owner deciding.

## Expectation Coverage

- E1: A paused change is not inferred, and every skip is named with its reason. Covered by: 1.1, 2.1
- E2: An all-paused repository reports each paused change and reason rather than reporting that none exists. Covered by: 1.1, 2.1
- E3: Every gate, the write guard, and completion behave identically on a paused change, and explicit selection still reaches it. Covered by: 1.1
- E4: Keel deciding on its own that a change is paused. Discard reason: A1 records why — every automatic criterion available describes work that has stalled, which is the state a person most needs reminding of, not one to hide. https://github.com/TanglmChris/keel/issues/112 owns any later proposal to infer it.
