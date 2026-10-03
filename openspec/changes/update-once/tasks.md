# Tasks

## 1. Running Claude sessions adopt an installed update

- [x] 1.1 A Claude hook hands off to the newest installed compatible copy of itself, and the guard waits for the active task
  - Covers:
    - keel-native-runtime-projection / A Claude hook runs the newest installed compatible copy of itself
    - keel-native-runtime-projection / The write guard keeps the loaded logic while a task is active
    - keel-native-runtime-projection / Keel reports runtime versions and does not manage them
    - D2
    - D3
    - F1
    - F2
  - Read:
    - plugins/keel/scripts/session-start.js
    - plugins/keel/scripts/mail-hook.js
    - plugins/keel/scripts/pretooluse-guard.js
    - .claude-plugin/plugin.json
  - Touch:
    - plugins/keel/scripts/forward.js
    - plugins/keel/scripts/session-start.js
    - plugins/keel/scripts/mail-hook.js
    - plugins/keel/scripts/pretooluse-guard.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario hook-hands-off-to-installed-update` builds a scratch Claude plugin cache `<plugins>/cache/m/keel/{5.0.0,5.1.0,6.0.0}`, each a copy of the plugin tree with its own `.claude-plugin/plugin.json` version, in which the newer trees' `session-start.js` and `mail-hook.js` are stubs that print their version, argv, stdin, `KEEL_HOOK_FORWARDED`, and `CLAUDE_PLUGIN_ROOT`, and `<plugins>/installed_plugins.json` names `keel@m` at a chosen path. It requires that the 5.0.0 copy of each script, run with a JSON stdin and an argument, prints the 5.1.0 stub's output with that stdin, that argument, `KEEL_HOOK_FORWARDED=5.0.0`, and the 5.1.0 root, and exits with the stub's status. It also requires that the 5.0.0 copy runs its own logic, with no stub output, when the record names 5.0.0 itself, names 6.0.0 (a different major), names a path that does not exist, names a 5.1.0 tree lacking the script, is absent, or when `KEEL_HOOK_FORWARDED` is already set, and when the same tree is laid out as a Codex cache with no record. Fails with: `hook-hands-off-to-installed-update:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario guard-keeps-loaded-logic-under-manifest` uses the same scratch cache with a 5.1.0 `pretooluse-guard.js` stub that always allows and prints `NEW-GUARD`, and a scratch repository whose `keel/guard.json` is a valid manifest whose Touch excludes `b.txt`. It requires that the 5.0.0 guard denies a Write to `b.txt` with no `NEW-GUARD` output while the manifest exists. After the manifest is removed, it requires that the same call prints `NEW-GUARD`. With the manifest removed and a 5.1.0 stub that sleeps past `KEEL_HOOK_FORWARD_TIMEOUT_MS`, it requires that the 5.0.0 guard's own decision is returned. Fails with: `guard-keeps-loaded-logic-under-manifest:`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if handing off would require changing any hook command string in `.claude-plugin/plugin.json` or `plugins/keel/hooks/codex.json`, because that breaks Codex hook trust and is outside D2.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e378b8b44b591c49bcdc54b167febcd84d783c3507a8cda1b7f44abf21011963
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario hook-hands-off-to-installed-update` reports `hook-hands-off-to-installed-update scenario passed.` Run from a scratch Claude cache, the 5.0.0 `session-start.js` and `mail-hook.js` hand off to 5.1.0's stubs when the record names 5.1.0. They pass the JSON stdin byte for byte, the `session-start` argument, `KEEL_HOOK_FORWARDED=5.0.0`, and the 5.1.0 root as `CLAUDE_PLUGIN_ROOT`, and they exit with the stub's status 3. They run their own logic, with no stub output, when the record names 5.0.0 itself, names 6.0.0, names a missing path, names a 5.2.0 tree lacking the scripts, is absent, or the marker is already set. A Codex-shaped install also runs its own logic, even with a newer sibling and a record beside its cache.
    - M1.red: fail. Before `forward.js` existed, the scenario reported `hook-hands-off-to-installed-update: session-start.js 5.0.0 did not hand off to installed 5.1.0: stdout='' stderr=''`, which carries the declared signature `hook-hands-off-to-installed-update:`.
    - M1.green: pass. The same scenario passes with `plugins/keel/scripts/forward.js`, whose `handOff` is called first in `session-start.js` and `mail-hook.js`.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario guard-keeps-loaded-logic-under-manifest` reports `guard-keeps-loaded-logic-under-manifest scenario passed.` With a real `keel gate task-start` manifest, the 5.0.0 guard denies a Write to `b.txt` and prints nothing from the always-allow 5.1.0 stub. After the manifest is removed, the same call prints the stub's output. A stub sleeping 5 s past `KEEL_HOOK_FORWARD_TIMEOUT_MS=300` leaves the loaded guard's own silent allow, with exit 0 and no output.
    - M2.red: fail. Before the guard called `handOff`, the scenario reported `guard-keeps-loaded-logic-under-manifest: the guard did not hand off once the manifest was gone: stdout='' stderr=''`, which carries the declared signature `guard-keeps-loaded-logic-under-manifest:`. Its first assertion, the deny under the manifest, already held, because the deferral costs nothing until a hand-off exists.
    - M2.green: pass. The same scenario passes once `pretooluse-guard.js` calls `handOff` only when the resolved repository has no `keel/guard.json`.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: Both scenarios run the real hook scripts as the host does, with a JSON stdin and the same arguments, from a cache laid out as Claude's. Only the newer install's copy is replaced, with a stub that reports what it received. Together they cover each clause of the two added requirements:
        - the hand-off happens only for a newer, same-major install that exists and carries the script, and relays input, output, and status unchanged;
        - every other case runs the loaded logic;
        - Codex never hands off;
        - the guard defers while a manifest exists and falls back on a failed hand-off.

        The modified requirement holds: no hook runs a package manager or makes a request. The hand-off spawns only `node` on a copy that is already installed.
      - Scope check: `git status --short` shows `plugins/keel/scripts/{forward.js,session-start.js,mail-hook.js,pretooluse-guard.js}` and `scripts/validate_plugin.py`, which are this task's Touch, plus this change's own directory. No hook command string changed in either manifest, so the Stop rule held. The guard header now says it may run a newer copy of itself (I3).
      - Findings: none

- [x] 1.2 A handed-off SessionStart is silent unless a reload is still needed
  - Covers:
    - keel-native-runtime-projection / An adopted update is silent unless a reload is still needed
    - D4
  - Read:
    - plugins/keel/scripts/session-start.js
    - openspec/specs/keel-native-runtime-projection/spec.md
  - Touch:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario adopted-update-is-silent-unless-reload` copies the real package tree twice into a scratch Claude cache, as 5.0.0 and 5.1.0, with the install record naming 5.1.0, and runs the 5.0.0 `session-start.js` in a scratch repository whose managed block declares 5.1.0. When the two trees are equal apart from their version, it requires the projection to run as 5.1.0 and to carry no version or update line on either channel. After one skill file in 5.1.0 is edited, it requires exactly one line naming 5.1.0, skills, and `/reload-plugins`, and no `claude plugin update`. Fails with: `adopted-update-is-silent-unless-reload:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:06f2489a1960bb00c390361832d4b82b33a2244fe92387587f658264ada699ec
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario adopted-update-is-silent-unless-reload` reports `adopted-update-is-silent-unless-reload scenario passed.` The scenario copies this tree's real package into a scratch cache as 5.0.0 and 5.1.0, with the install record naming 5.1.0 and no `keel` on PATH. The 5.0.0 `session-start.js` then delivers a real `context ready` projection in a repository declaring protocol 5.1.0, carrying no version, drift, or reload line on either channel. After one `SKILL.md` in 5.1.0 is edited, each channel carries exactly one line naming 5.1.0, the skills, and `/reload-plugins`, and neither names `claude plugin update`.
    - M1.red: fail. Before `adoptionReport` existed, the scenario reported `adopted-update-is-silent-unless-reload: additionalContext carries 0 lines naming /reload-plugins after a skill changed, not one: 'Keel session projection …'`, which carries the declared signature `adopted-update-is-silent-unless-reload:`. The silent half already held, because 1.1's hand-off makes the CLI and plugin versions the new ones.
    - M1.green: pass. The same scenario passes with `adoptionReport()` in `session-start.js`. It compares the loaded and running trees' `plugins/keel/skills`, `plugins/keel/agents`, and declared hooks, and adds its line to both channels only when one differs.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: M1 runs the real SessionStart chain: the loaded script, the hand-off, the newer script, and the newer package's own CLI computing `keel context`. Its silent case is a real projection, not a fallback, because the scenario refuses fallback text. Without a hand-off, the same fixture would report `plugin 5.0.0` against `protocol 5.1.0`, and the absence of that line is what shows the projection ran as 5.1.0. The changed-skill case asserts the single `/reload-plugins` line and no update command, which are the two scenarios of the added requirement. The existing `runtime-version-drift`, `drift-names-a-pending-reload`, and `drift-names-where-to-look` scenarios still pass.
      - Scope check: `git status --short` shows `plugins/keel/scripts/session-start.js` and `scripts/validate_plugin.py` changed by this task, plus 1.1's files and this change's own directory. `forward.js` is unchanged here: the loaded tree is found as its sibling version directory, so no new marker was needed.
      - Findings: none

## 2. One command updates the machine, and refreshes cover every target

- [ ] 2.1 `keel --update` updates the installed Claude and Codex plugins and reports each component
  - Covers:
    - keel-native-plugin-package / One owner-run update covers every installed Keel component
    - D1
    - D6
    - F3
  - Read:
    - bin/keel.js
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-covers-installed-hosts` runs `keel --update` with `KEEL_UPDATE_NPM`, `KEEL_UPDATE_CLAUDE`, and `KEEL_UPDATE_CODEX` pointing at fakes that log their argv. Each fake host answers `plugin list --json` with Keel at 5.0.0 before its update command and at 5.1.0 after it, from a Git marketplace. The scenario requires the CLI pack and install, then `claude plugin marketplace update keel-marketplace` and `claude plugin update keel@keel-marketplace`, then `codex plugin marketplace upgrade keel-marketplace` and `codex plugin add keel@keel-marketplace`, each once and in that order, and one line per component naming `5.0.0 -> 5.1.0` and when it applies. It then requires five more outcomes:
      - With `KEEL_UPDATE_CODEX` naming a missing executable, the Codex line reads `absent` and the exit status is 0.
      - With a non-Git Codex marketplace, the Codex line reads `manual`, names the source and `codex plugin marketplace add TanglmChris/keel --ref main`, and no Codex marketplace command runs.
      - With differing `hooks/codex.json` between the fake installed and new roots, the Codex line names `/hooks`.
      - With the Claude update command exiting 1, the Claude line reads `failed`, the Codex line still reports, and the exit status is nonzero.
      - `--dry-run` prints the host commands and the fakes log nothing.

      Fails with: `update-covers-installed-hosts:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a host offers no documented non-interactive command for a step, because Keel would have to drive the host in a way its owner did not document.
  - Evidence:
    - Contract: `todo`
    - Blocker: none
    - Reauthorizations: none

- [ ] 2.2 A protocol refresh brings every installed target's overlays forward, and doctor names stale ones
  - Covers:
    - keel-openspec-surface-overlay / A protocol refresh brings every installed target's overlays forward
    - D5
    - F4
  - Read:
    - bin/keel.js
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario refresh-covers-every-target` initializes a scratch repository for Claude and Codex, rewrites every overlay marker to `version=5.0.0`, and requires `keel --doctor` to report the Codex overlay stale with the refresh command. It requires `keel --install --target claude` to leave every Claude and Codex overlay at the running version, exactly once per surface, with the upstream body unchanged. It also requires that a Claude-only repository gains no `.agents/` or `.opencode/` surface from the same command. Fails with: `refresh-covers-every-target:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: `todo`
    - Blocker: none
    - Reauthorizations: none

- [ ] 2.3 The update steps and the per-host capability matrix are documented, and the Codex probe is a repeatable opt-in check
  - Covers:
    - F1
    - F2
    - D1
  - Read:
    - README.md
    - README.zh-CN.md
    - docs/codex-validation.md
    - scripts/validate_codex_receiving.py
  - Touch:
    - docs/updating.md
    - README.md
    - README.zh-CN.md
    - docs/codex-validation.md
    - scripts/validate_codex_receiving.py
  - Verify:
    - Strategy: evidence-first
    - Reason: the behavior this task documents is implemented and proven in 1.1, 1.2 and 2.1. The opt-in check reproduces a host fact already recorded on #204, so there is nothing for a red to fail on before it is written.
    - M1: `node scripts/run_python.js scripts/validate_codex_receiving.py --native-upgrade` passes. In an isolated `CODEX_HOME` with a request-capture endpoint and no model run, an already-running `codex app-server` thread's next hook after `codex plugin add` of a newer throwaway plugin runs the newer version from the new directory, and the hooks stay trusted.
    - M2: `docs/updating.md` carries the capability matrix for Claude and Codex across new session, resume, compact, clear, and next hook call, each cell citing its probe. Both READMEs name `keel --update` as the one update command and no longer say Codex needs a fresh session after a plugin update. A grep of the two READMEs and `docs/codex-validation.md` for `start a fresh session after updating the plugin` returns nothing.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: `todo`
    - Blocker: none
    - Reauthorizations: none

## 3. Release, and prove adoption across two releases

- [ ] 3.1 Release 5.89.0 with the change promoted
  - Covers:
    - E1
    - E2
    - E3
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-native-plugin-package/spec.md
    - openspec/specs/keel-native-runtime-projection/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and promoted specs. The behavior was proven in 1.1 through 2.3, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to 5.89.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.89.0 section written into the stub.
    - M2: the three deltas are promoted, `node node_modules/.bin/openspec validate update-once --strict` passes, and `npm test` reports no failing scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: `todo`
    - Blocker: none
    - Reauthorizations: none

- [ ] 3.2 A running Claude session and a running Codex session adopt 5.89.1 after one `keel --update`
  - Covers:
    - E1
    - E2
  - Read:
    - docs/updating.md
  - Touch:
    - docs/updating.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this proves on the owner's machine what 1.1 and 2.1 proved in scratch caches. It needs two published releases that both carry the hand-off, so it has no red that could run before them.
    - M1: with 5.89.0 installed on both hosts and loaded in a running Claude Code session, 5.89.1 is published and `keel --update` runs once. That session's next SessionStart (after `/compact` or `/clear`), with no `/reload-plugins`, projects `Keel: 5.89.1`, and its loaded plugin path is still the 5.89.0 directory.
    - M2: in a `codex app-server` started under 5.89.0 against the owner's real Codex home, a new thread after the same `keel --update` projects 5.89.1, and `codex plugin list` reports 5.89.1 with the hooks still trusted.
    - M3: the measured result is recorded in `docs/updating.md` under the capability matrix, with the date and the versions.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the owner's running session cannot be brought to 5.89.0 without the owner's own action, and ask them for that one action rather than restarting anything.
  - Evidence:
    - Contract: `todo`
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario once 1.1, 1.2, 2.1 and 2.2 have registered theirs.

## Change Evidence

- C1: `todo`

## Invalidates

- I1: "Keel MUST NOT install, update, pin, or resolve a plugin or CLI version" — `openspec/specs/keel-native-runtime-projection/spec.md`. Updated by: 3.1
- I2: "--update refreshes the global keel CLI, not project protocol files." — the usage text in `bin/keel.js`. Updated by: 2.1
- I3: "The hook never writes state, never spawns the keel CLI" — the header of `plugins/keel/scripts/pretooluse-guard.js`. It still never spawns the CLI, but it now may run a newer copy of itself. Updated by: 1.1
- I4: "For Codex, start a fresh session after updating the plugin" — `README.md`, and its counterpart in `README.zh-CN.md`. F1 shows a running session's next hook already runs the update. Updated by: 2.3
- I5: "`/reload-plugins` applies it in the running session, and otherwise it applies at the next start" — `README.md`, and "执行 `/reload-plugins` 即在当前会话生效" — `README.zh-CN.md`. Hooks now apply at the next hook call, and the sentence remains true only for skills and agents. Updated by: 2.3
- I6: "Update the Keel CLI and installed Codex plugin to the desired matching release" and "Start a fresh Codex session so the installed hook definitions are loaded" — `docs/codex-validation.md`. Updated by: 2.3
- I7: "a session's hooks are fixed when it loads the plugin, so an updated plugin applies after `/reload-plugins` or at the next session start" — the drift line in `plugins/keel/scripts/session-start.js` and its scenario in `keel-native-runtime-projection`. Discard reason: the drift line appears only when a session cannot hand off: it loaded a version without `forward.js`, or the install is incompatible. In exactly those cases the sentence is true.
- I8: "an updated plugin applies after `/reload-plugins` or at the next session start" — the Claude marketplace scenario in `keel-native-plugin-package`. Discard reason: that scenario is about the plugin as a whole, whose skills and agents still apply only then.

## Expectation Coverage

- E1: One command the owner runs updates the CLI and every installed Keel plugin on this machine, and says per component what took effect and what still needs the owner. Covered by: 2.1, 3.1, 3.2
- E2: Running sessions on Claude and Codex use the new hook logic at their next hook call without anyone updating them one by one, and say nothing when nothing else is needed. Covered by: 1.1, 1.2, 2.3, 3.2
- E3: An active task keeps the write guard it started under, project files are refreshed only by that project's own session, and a refresh covers every target the project carries. Covered by: 1.1, 2.2, 3.1
