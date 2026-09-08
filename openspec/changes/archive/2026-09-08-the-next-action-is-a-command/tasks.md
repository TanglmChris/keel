# Tasks

## 1. The command, printed

- [x] 1.1 `keel context` reports the invocation for its next action in both text and JSON, naming change and task explicitly and including the argument `change-close` requires, and reports none where there is no command
  - Covers:
    - keel-stateless-continuity / The next action is reported as a command
    - D1
    - D5
    - A1
    - F1
    - F2
  - Read:
    - src/core/context.js
    - bin/keel.js
    - scripts/validate_plugin.py
    - openspec/changes/the-next-action-is-a-command/design.md
  - Touch:
    - src/core/context.js
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `the-next-action-is-a-command` scenario in `scripts/validate_plugin.py` drives `keel context` through the real CLI against fixture repositories. A task awaiting `task-start` reports a command naming the stage, `--change demo` and `--task 1.1`; the same fixture with completion evidence recorded reports the `task-complete` invocation. A change whose tasks are all checked reports the `change-close` invocation **including `--action`**, and running exactly the string reported does not produce the `requires --action` input error — asserted by running it. An idle repository reports no command rather than an empty one. `--json` carries the same string as the text surface, compared character for character.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario stateless-continuity` passes unchanged, so every status, reason, and warning keeps its shape.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the reported command depends on inference to resolve its change or task, because A1 records that a reader may run it later or elsewhere.
    - Stop if reporting a command causes `context` to run or write anything.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:dc3bfcad336989c84229bd37db1d29749be5d139d585eb49e9ebfa1c9d9697a8
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-next-action-is-a-command` reports `the-next-action-is-a-command scenario passed.` A task awaiting `task-start` reports `Run: keel gate task-start --change demo --task 1.1`; the same fixture with completion evidence reports the `task-complete` invocation; a change whose tasks are checked reports `keel gate change-close --change demo --action archive`. The `--json` result carries the identical string, compared character for character against the text surface. The change-close command is then executed exactly as printed and does not produce `requires --action` — the failure issue #112 reports. An idle repository carries no `command` key at all rather than an empty one.
    - M1.red: fail, for the right reason. Before `nextActionCommand()` existed the scenario reported `the next action carries no command; {'kind': 'task-start'}` — the whole result, showing that the change and task the command needs were already in it.
    - M1.green: pass. Same command after `result()` attached the invocation and the renderer printed it on a `Run:` line.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario stateless-continuity` reports `stateless-continuity scenario passed.` Every status, reason, and warning keeps its shape.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 168 scenarios.` — up from 167 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the next action is reported as a runnable command naming its change and task explicitly, including what `change-close` requires, with none where there is nothing to run. M1 proves each, and the strongest assertion is the one that runs the printed string: asserting `--action` appears in it would pass against a command that named the flag and still failed for some other reason, while executing it tests the claim the line makes. The text-versus-JSON comparison is character for character because two surfaces drifting apart is how a printed command stops being the one a program would run.
      - Scope check: `git status --short` shows exactly this task's three Touch paths plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: one, fixed in this task. Eight scenarios asserted `nextAction` by whole-dictionary equality, so attaching a field broke every one of them — and my first repair made it worse by writing the exact command string into three of them, which would have made unrelated scenarios fail whenever the wording moved. They now compare the `kind` and leave the command to the scenario that owns it. The lesson is in the shape rather than the fix: an assertion on a whole payload is an assertion that nothing will ever be added to it. Resolved here: M2
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 Every Keel OpenSpec surface overlay names `keel openspec` as the invocation and points at `keel --doctor`, with the OpenSpec-authored body of each file unchanged
  - Covers:
    - keel-openspec-surface-overlay / The overlay states the invocation that resolves
    - D2
    - D3
    - F3
    - F4
  - Read:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - bin/keel.js
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
    - Strategy: vertical-tdd
    - M1: a new `the-overlay-names-the-invocation` scenario in `scripts/validate_plugin.py` installs into a fixture repository through the real CLI and asserts that every file carrying a Keel OpenSpec surface overlay names `keel openspec` and `keel --doctor` inside the overlay block. It then asserts the boundary: the text outside the overlay markers is byte-identical to the same file before the overlay was merged, so Keel added a block and edited nothing of OpenSpec's.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes unchanged, so the twelve installed surfaces keep their markers.
    - M3 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if stating the invocation requires changing any text outside the overlay markers, because D2 records that those files belong to OpenSpec and the next upstream change would collide with the edit.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:096d60d976ac179eeb5427bb0746fc18662e076914d5505d49e618af606bec11
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-overlay-names-the-invocation` reports `the-overlay-names-the-invocation scenario passed.` The scenario writes the eight OpenSpec surfaces with a body in the shape OpenSpec writes, instructing the reader to run a bare `openspec new change` command, installs through the real CLI, and asserts that every file carrying an overlay names `keel openspec` and `keel --doctor` **inside the overlay block**. It then asserts the boundary from the other side: the text outside the markers carries no Keel invocation text, so Keel appended a block and edited nothing of OpenSpec's. Re-running the install against this repository refreshed all twelve installed surfaces, and the note reads directly under the precedence sentence, which is where an agent meets it before running anything else in the file.
    - M1.red: fail, for the right reason, twice. The first red was the fixture's: `the install wrote no file carrying an overlay` — `--install` merges into surfaces OpenSpec has already written and the bare temp repository had none, so the scenario now creates them. With the fixture correct the real red followed: `the overlay in apply.md does not name 'keel --doctor'`.
    - M1.green: pass. Same command after the invocation note was added to all three overlay bodies — the authoring overlay, the sync overlay, and the shared apply/archive body.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` The twelve installed surfaces keep their markers, now with the note inside them.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 169 scenarios.` — up from 168 by the one scenario this task added.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that every overlay names the working invocation while the OpenSpec-authored body stays untouched. M1 proves both, and the second is the one that needed asserting rather than assuming: the obvious way to fix this defect is to rewrite `openspec` to `keel openspec` in those files, which would work and would collide with the next upstream change. The scenario fails if Keel invocation text appears anywhere outside the markers, so the boundary is enforced rather than remembered.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `bin/keel.js`, `scripts/validate_plugin.py`, and the twelve installed surfaces the re-install refreshed — plus `src/core/context.js` from task 1.1, already declared complete and untouched here, plus this change's own untracked directory. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — the next action is reported as a runnable command
    - E2 — the overlay names the invocation that resolves, without editing upstream text
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
    - keel/CHANGELOG.md
    - scripts/validate_plugin.py
    - openspec/specs/keel-stateless-continuity/spec.md
    - openspec/specs/keel-openspec-surface-overlay/spec.md
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
    - Reason: this task's whole effect is version markers, published wording, and promoted spec text. Both behaviors were proven red-green in tasks 1.1 and 1.2, and nothing here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry naming issue #112's fifth group, stating what each of the three costs was, and recording the one deliberately not fixed with its reason
    - M3: both spec deltas are promoted, `node node_modules/.bin/openspec validate the-next-action-is-a-command --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:c9e9ecf5e8148057a784e3e14599cd5a84fb5caac1f17e89ea8aa5e0a60aebda
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` after `node scripts/bump_version.js minor` rewrote every marker to 5.56.0 — the npm package, both native plugin manifests, the protocol docs, and this changelog.
    - M2: pass. `keel/CHANGELOG.md` carries the `5.56.0 - the next action is a command` entry. It names issue #112's fifth group, states what each of the two fixed costs was in the reporter's own terms — assembling the invocation by hand from arguments already printed one line up, and an agent instructed to run a bare `openspec` that does not resolve in a Keel-only install — and records `keel openspec validate --change X` as deliberately not fixed, with the reason: the proxy passes arguments through unaltered, and translating them there would make it behave differently from the tool it proxies.
    - M3: pass. Both deltas are promoted — `The next action is reported as a command` into `openspec/specs/keel-stateless-continuity/spec.md` and `The overlay states the invocation that resolves` into `openspec/specs/keel-openspec-surface-overlay/spec.md`. `node node_modules/.bin/openspec validate the-next-action-is-a-command --strict` reports `Change 'the-next-action-is-a-command' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 169 scenarios.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the release carries both behaviors and the published wording is true of them. M1 proves the markers agree, M3 proves the promoted requirements validate against the store rather than only against the delta, and M2 is the one that needed writing rather than checking: the entry records the discard beside the two fixes, because a reader who hits `validate --change` next month needs the reason it stayed, not silence where a third fix would have been.
      - Scope check: `git status --short` shows the version markers, the changelog, the two promoted specs, and this change's own directory. The twelve installed OpenSpec surfaces were already refreshed by task 1.2 and are unchanged here. `keel guard status` reports the fingerprint unchanged from task-start.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "keel gate task-start|task-complete|change-close [repo] [--change name] [--task id] [--action sync|archive]" — the usage line in `bin/keel.js`.
  One line covers three stages, so the argument one of them requires is shown as optional for all.
  Updated by: 1.1
- I2: "Next action: ${result.nextAction.kind}" — the context renderer in `src/core/context.js` and the
  scenarios asserting that line. It keeps the kind and gains the command beneath it.
  Updated by: 1.1

## Expectation Coverage

- E1: `keel context` reports a runnable command for its next action, in text and JSON, naming change and task explicitly, and reports none where there is no command. Covered by: 1.1, 2.1
- E2: Every installed OpenSpec surface names `keel openspec` and `keel --doctor` in Keel's own overlay, with the OpenSpec-authored body unchanged. Covered by: 1.2, 2.1
- E3: `keel openspec validate --change X` accepting the flag that `status` accepts. Discard reason: D4 records it — the proxy passes arguments through unaltered, and translating them would make `keel openspec` behave differently from the tool it proxies, which a user discovers when the same command fails run directly. The inconsistency is OpenSpec's CLI surface, and https://github.com/TanglmChris/keel/issues/112 records the discard.
