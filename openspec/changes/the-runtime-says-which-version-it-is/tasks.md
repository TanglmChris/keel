## 1. The comparison

- [x] 1.1 Report a version disagreement on both channels, and stay silent when there is none
  - Covers:
    - keel-native-runtime-projection / The session projection reports runtime version alignment
    - keel-native-runtime-projection / An undiscoverable version is not reported as drift
    - D1 — Keel reports and does not manage
    - D2 — silence when aligned
    - D3 — missing is not mismatched
    - D4 — exact string equality, not semantic ordering
    - D6 — both channels, because the remedy is the person's action
    - D7 — the report names the restart requirement
    - F1 — the hook already fetches and discards the CLI version
    - F3 — the hook never speaks in a non-Keel repository
    - F5 — the observed drift this change exists to have caught
    - A1 — the plugin version is read relative to the hook's own location
  - Touch:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: with the plugin manifest, the CLI, and the repository's stamped protocol version not all equal, both `systemMessage` and `additionalContext` name each discovered version, state that they disagree, and state that hooks are fixed at session start so an update applies after restart
    - M2: with all three equal, neither channel gains a version line, and the rest of both payloads is byte-identical to the same run with the capability's comparison disabled
    - M3: the report performs no installation or update and names only the host's own command as the reader's option, asserted by driving the hook with a mismatch and confirming it spawns nothing beyond the `keel` invocations it already made
    - M4: a repository whose `AGENTS.md` carries no managed block, with plugin and CLI equal, produces no version line on either channel
    - M5: when one version is undiscoverable and the two that are readable disagree, the report names that disagreement and names the third as undiscovered rather than folding it into the comparison
    - M6 (regression): with the plugin manifest missing or unreadable, and with `CLAUDE_PLUGIN_ROOT` unset, the projection still delivers its status, selection, and next action, and no comparison failure degrades or blocks the continuity report
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3ba2bd7b093a157047cee2364b53816b051ddd8adff9e64de43ef15edea31719
    - M1: pass. New scenario `runtime-version-drift` in `scripts/validate_plugin.py`, run as `python3.11 scripts/validate_plugin.py --scenario runtime-version-drift`. It reproduces F5 exactly — plugin 5.2.1, CLI 5.2.1, protocol 5.7.1 — and asserts on both `systemMessage` and `additionalContext` that each discovered version is named, that they are stated to disagree, and that the restart requirement is stated.
    - M1.red: fail. With no comparison in the hook, `additionalContext does not state that the versions disagree`, printing the whole four-line projection it did emit.
    - M1.green: pass, after `versionReport()` and the two readers were added and their line pushed onto both channels.
    - M2: pass. Same scenario. An aligned run (plugin, CLI, and the repository's block all 5.7.1) carries neither the drift statement nor the version string on either channel; lifting the single drift line off the mismatched payload leaves both channels byte-identical to the aligned run, which is the comparison disabled on the same run.
    - M2.red: fail. `additionalContext spoke about versions that agree`, quoting `runtime versions disagree: plugin 5.7.1, CLI 5.7.1, protocol 5.7.1` — the first implementation reported unconditionally, which is what M2 exists to catch.
    - M2.green: pass, after the equality guard returned null for a matching set.
    - M3: pass. Same scenario. The report names `claude plugin update` and carries no Keel-side remedy (`keel update`, `npm install`). A `--require` preload patches `child_process` inside the hook's own process and logs every spawn; the log holds exactly the two `keel` invocations the hook already made, which is also the recorder's positive control — a recorder that had stopped working would leave an empty log and fail the same count.
    - M3.red: fail. `report does not name the host's own update command, leaving the reader with no move`, quoting the sentence as it then stood.
    - M3.green: pass, after `pluginManifest()` began returning the remedy belonging to whichever target's manifest was read.
    - M4: pass. Same scenario. A repository whose `AGENTS.md` carries no managed block, with plugin and CLI equal, produces no version line on either channel.
    - M4.red: fail. `additionalContext called an undiscoverable protocol version a disagreement`, quoting `plugin 5.7.1, CLI 5.7.1, protocol null` — the defect that also broke the shipping `native-plugin-session-start` scenario and is what merged this task with the one that followed it.
    - M4.green: pass, after the comparison was taken over discoverable versions only, with fewer than two treated as nothing to compare rather than as agreement.
    - M5: pass. Same scenario. With the protocol version unreadable and plugin 5.7.1 against CLI 5.2.1, both channels report that disagreement, name the protocol version as `undiscovered, not compared`, and print no `null` or `undefined` in place of a version.
    - M5.red: fail. `additionalContext reported a partial comparison as a complete one, without naming the version it never read`, quoting `runtime versions disagree: plugin 5.7.1, CLI 5.2.1`.
    - M5.green: pass, after the unread names were appended to the sentence.
    - M6: pass. Same scenario. With no manifest beside the hook and `CLAUDE_PLUGIN_ROOT` empty, the hook exits 0 and `additionalContext` still carries `demo#1.1`, `task-start`, and the disclosure instruction. Positive control: the same assertions run against a deliberately throwing copy of the script exit 1 with empty stdout, so the check bites.
    - Review:
      - Status: pass
      - Acceptance check: The Acceptance is behavioral and every check drives the real hook as a subprocess through its two published channels, asserting the emitted text rather than the shape of any function. M1 and M5 prove what is said, M2 and M4 prove what is not said, M3 proves the report is a report — the spawn log answers "does it act?" with the process table rather than with the wording. Nothing here asserts that the file parses or that a helper returns a given type.
      - Scope check: Both Touch files changed and nothing else. `git status --short` against the `fcc3bc8` base shows `plugins/keel/scripts/session-start.js`, `scripts/validate_plugin.py`, this `tasks.md`, and `keel/guard.json` — the last two are the record-write layer and the disposable guard, neither of which is product state. The shared `run_session_start_hook` helper gained two optional parameters that default to today's behavior, so no existing call site changed.
      - Findings: This task and the task that followed it were authored as a split that could not be executed. Implementing the first alone left `protocol null` in the projection of every repository without a managed block, which broke the shipping `native-plugin-session-start` scenario, and once it was implemented correctly two of the second task's three checks were already green, leaving a `vertical-tdd` task with no honest red. The guard hard-stopped the contract edit, the two were merged, and `keel gate task-start --record` reauthorized at `sha256:3ba2bd7b…`. Discard reason: the defect itself is closed — the merged task is the correction, and D2 and D3 are now covered by one contract. The remaining question is why authoring did not flag the split; that half is deferred, and its durable owner is https://github.com/TanglmChris/keel/issues/41, which carries the evidence, the rationale, and a candidate identical-Touch check.
    - Blocker: none

## 2. Close

- [ ] 2.1 Promote the delta and record the release
  - Covers:
    - keel-native-runtime-projection / Keel reports runtime versions and does not manage them
    - I1, I2
  - Touch:
    - openspec/specs/keel-native-runtime-projection/spec.md
    - keel/CHANGELOG.md
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
  - Verify:
    - Strategy: evidence-first
    - M1: `keel openspec validate the-runtime-says-which-version-it-is` passes and every `### Requirement:` and `#### Scenario:` heading in the delta appears in the live spec
    - M2: the changelog entry states that the check reports rather than manages, that it is silent when aligned and why that diverges from issue #38's wording, and that an undiscoverable version is not drift
    - M3: `version-alignment` passes with every marker at the new version, including the changelog-head comparison added in 5.8.0
    - M4: `npm test` passes, with the two environment failures owned by issue #36 as the only exceptions
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

- I1: "Keel MUST derive native runtime projection from OpenSpec and MUST NOT treat native goal, task UI, transcript, memory, checkpoint, or subagent state as input authority" — the opening requirement of `openspec/specs/keel-native-runtime-projection/spec.md`. The sentence stays true and is not edited: a plugin manifest and a `--version` string are facts about the runtime rather than state it accumulated, so reading them is not treating native state as authority. Discard reason: recorded because a reader arriving at the new requirement will reasonably ask whether it contradicts this one, and the answer belongs beside the question.
- I2: "keel: OpenSpec apply/archive overlay refreshed" and the version markers `5.8.0` across `package.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, and `scripts/validate_plugin.py` — every one names the shipping version and goes stale the moment this change releases. Updated by: 2.1

## Expectation Coverage

- E1: A human and an agent both learn at session start when the runtime enforcing the protocol is not the protocol. Covered by: 1.1
- E2: The signal stays credible — nothing is said when everything agrees. Covered by: 1.1
- E3: An undiscoverable version is never reported as drift, and never produces a line on its own. Covered by: 1.1
- E4: A partial comparison still happens; one unreadable version does not suppress the others. Covered by: 1.1
- E5: The projection keeps working when the comparison cannot. Covered by: 1.1
- E6: Keel reports and never installs, updates, or resolves a version. Covered by: 1.1, 2.1
- E7: The check is local, offline, and deterministic, consistent with every other Keel answer. Covered by: 1.1
- E8: A reader who updates the plugin and sees no change is told why. Covered by: 1.1
