# Tasks

## 1. The plugin carries its CLI

- [x] 1.1 The SessionStart hook runs the CLI its package ships, reports a `keel` on PATH that shadows it, and names `/reload-plugins` instead of a restart
  - Covers:
    - keel-native-runtime-projection / The session projection reports runtime version alignment / A mismatch names how an update applies
    - keel-native-runtime-projection / The session projection reports runtime version alignment / A shadowing CLI on PATH is reported
    - keel-native-runtime-projection / The session projection reports runtime version alignment / No CLI on PATH is not drift
    - keel-native-plugin-package / Plugin and CLI compatibility is explicit / The Claude plugin runs its own CLI
    - D5
    - D6
    - D8
    - F8
  - Read:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Touch:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `runtime-version-drift` requires both channels of a mismatched projection to name `/reload-plugins` and neither to say an update applies only after restarting. Fails with: `omits how an update applies`
    - M2: a new `plugin-runs-its-own-cli` scenario plants a package (`package.json` named `@christang/keel`, a fake `bin/keel.js`, the shipping hook at `plugins/keel/scripts/session-start.js`), runs the hook with `KEEL_CLI` unset and a different fake `keel` first on PATH, and requires the spawn log to show the package's `bin/keel.js` answering `context`. Fails with: `ran the keel on PATH instead of`
    - M3: the same scenario requires the drift line on both channels to name the PATH version, to say it shadows the plugin's CLI, and to name `npm rm -g @christang/keel`. Fails with: `did not report the keel that shadows`
    - M4: the same scenario, with no `keel` on PATH at all, requires a normal projection with no version line. Fails with: `with no keel on PATH`
    - M5 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the hook would need to write any file or reach the network to decide which CLI to run, because the projection is read-only and offline.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8ff3e7d7ac3823d2257ecd5c86de92dd229c64f6a3b79235c850482f4ad4e594
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario runtime-version-drift` reports the scenario passing. Both channels of the mismatched projection now carry `fixed when it loads the plugin` and `/reload-plugins`, and neither carries `only after restarting`.
    - M1.red: fail, for the declared reason. `runtime-version-drift additionalContext omits how an update applies ['fixed when it loads the plugin', '/reload-plugins'], or still says it applies 'only after restarting', …` against the shipping line `A session's hooks are fixed at session start, so an updated plugin applies only after restarting.` Carries the declared signature `omits how an update applies`. The combined check was later split into two, and each message still carries the signature.
    - M1.green: pass. Same command after `versionReport()` in `plugins/keel/scripts/session-start.js` was changed to say `fixed when it loads the plugin, so an updated plugin applies after \`/reload-plugins\` or at the next session start`.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario plugin-runs-its-own-cli` reports the scenario passing. The spawn log of the planted package's hook, with `KEEL_CLI` unset and a fake `keel` 5.70.0 first on PATH, shows `<package>/bin/keel.js … context --json` answering.
    - M2.red: fail, for the declared reason. `plugin-runs-its-own-cli M2 ran the keel on PATH instead of the CLI its package ships (…/package/bin/keel.js): ['spawnSync keel --version', 'spawnSync keel context --json']`. Carries the declared signature `ran the keel on PATH instead of`.
    - M2.green: pass. Same command after `packagedCli()` and `keelCommand()` were added: `KEEL_CLI` first, then the package's own `bin/keel.js`, recognized by `package.json` name `@christang/keel` and run under `process.execPath`, then `keel`.
    - M3: pass. Same scenario. Both channels name `PATH keel 5.70.0`, say it `shadows` this plugin's CLI, and name `npm rm -g @christang/keel` and `npm i -g @christang/keel@5.80.0`. A PATH `keel` at the plugin's own version produces no version line.
    - M3.red: fail, for the declared reason. After M2's green, the same command reported `plugin-runs-its-own-cli M3 additionalContext did not report the keel that shadows the plugin's CLI, with its version and remedies: '… - report this state to the user in your first reply; it authorizes nothing.'`, with no version line at all. Carries the declared signature `did not report the keel that shadows`.
    - M3.green: pass. Same command after `versionReport()` gained the `PATH keel` entry and the shadow sentence, and `pathCliVersion()` asks the bare `keel` only when the hook ran its packaged CLI.
    - M4: pass. Same scenario. With PATH holding only a directory containing `node`, the projection is the normal `demo#1.1` one, with no version line.
    - M4.red: fail, for the declared reason. The scenario was run from a scratch copy with the M2 and M3 blocks disabled and the hook read from `git show HEAD:plugins/keel/scripts/session-start.js`. It reported `plugin-runs-its-own-cli M4 the projection fell back with no keel on PATH, which is the plugin-only install: 'Keel hook fallback: the keel CLI is missing or incompatible with this plugin; …'`. Carries the declared signature `with no keel on PATH`.
    - M4.green: pass. Same scenario against the working tree: the packaged CLI answers, and a PATH with no `keel` is not compared.
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 185 scenarios, 1 skipped: output-survives-the-pipe.` Along the way, `assertion-shape-count` refused the first draft's OR-guarded checks (81 sites against 80 recorded). They were split into one message per failure, and the bound was left at 80. The Stop Rule held: the hook writes nothing and spawns only local `keel`/`node` processes.
    - Review:
      - Status: pass
      - Acceptance check: all four checks run the real hook. M2 is asserted by a spawn recorder inside the hook's own process rather than by the projection text, because both CLIs print the same context. M3 and M4 together pin the boundary: a PATH copy that disagrees is named, one that agrees or is absent is not. `runtime-version-drift`'s existing count of exactly two `keel` spawns still passes, because a pinned `KEEL_CLI` never takes the packaged branch, so the extra `--version` probe costs nothing outside the package.
      - Scope check: `git status --short` shows `plugins/keel/scripts/session-start.js` and `scripts/validate_plugin.py`, this task's Touch, plus this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 The Claude marketplace installs the published package, and the package runs as a plugin
  - Covers:
    - keel-native-plugin-package / The Claude plugin is the published package / One artifact carries the plugin and its CLI
    - keel-native-plugin-package / The Claude plugin is the published package / The entry's hooks cannot drift from the plugin's
    - keel-native-plugin-package / The Claude plugin is the published package / The package runs as a plugin
    - keel-native-plugin-package / Native marketplaces install and update Keel in isolation / Claude marketplace installs Keel
    - keel-native-plugin-package / Plugin and CLI compatibility is explicit / OpenSpec is resolved through Keel
    - D1
    - D2
    - D3
    - D4
    - D7
    - F1
    - F2
    - F4
    - F6
    - F7
  - Read:
    - .claude-plugin/marketplace.json
    - plugins/keel/hooks/hooks.json
    - bin/keel.js
    - scripts/bump_version.js
    - scripts/validate_plugin.py
  - Touch:
    - .claude-plugin/marketplace.json
    - bin/keel
    - bin/keel.js
    - package.json
    - package-lock.json
    - npm-shrinkwrap.json
    - scripts/bump_version.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `native-plugin-manifests` requires the Claude entry's source to be the `@christang/keel` npm package with `source.version` and `version` both equal to `package.json`, and its skills and agent paths to exist in the repository. Fails with: `claude marketplace entry is not the published package`
    - M2: `native-plugin-manifests` requires the entry's inline hooks to equal `plugins/keel/hooks/hooks.json` event by event after prefixing each script path with `plugins/keel/`. Fails with: `entry hooks diverge from`
    - M3: `native-plugin-manifests` packs the repository with `npm pack --dry-run --json` and requires `bin/keel` with an executable mode and `npm-shrinkwrap.json` in the packed set. Fails with: `packed set lacks`
    - M4: `doctor-reads-the-diagnosed-repository` plants a repository whose `npm-shrinkwrap.json` and `package-lock.json` declare different OpenSpec versions, and requires the doctor line to attribute the shrinkwrap's. Fails with: `read package-lock.json over npm-shrinkwrap.json`
    - M5: `version-alignment` requires the Claude entry's `version` and `source.version` to equal `PACKAGE_VERSION`, and `node scripts/bump_version.js` in a scratch copy to move both. Fails with: `claude marketplace entry version`
    - M6 (regression): `native-plugin-marketplaces` validates and installs the Claude plugin from a temporary marketplace whose entry points at a local copy of the package, where both the codex and claude CLIs are installed. Detects: `the scenario installs from the committed npm entry` -> `claude plugin install failed`
    - M7 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if `claude plugin validate` refuses an entry that is the manifest for an npm source, because D1 rests on F2.
    - Stop if any scenario needs the network to pass, because the suite runs offline apart from `native-plugin-marketplaces`, which is skipped in CI.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ce738a4f5520cda0e54d3001e62530fa6445414325bc557089622da6cc238b2d
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario native-plugin-manifests` reports the scenario passing. The Claude entry's source is `{source: npm, package: @christang/keel, version: 5.73.1}`, its `version` is `5.73.1`, and `./plugins/keel/skills/` and `./plugins/keel/agents/keel-single-task-goal-claude.md` exist.
    - M1.red: fail, for the declared reason. `native-plugin-manifests claude marketplace entry is not the published package: source './plugins/keel'`. Carries the declared signature `claude marketplace entry is not the published package`.
    - M1.green: pass. Same command after `.claude-plugin/marketplace.json` was rewritten with the npm source and pinned versions, and the skills and agent paths.
    - M2: pass. Same scenario. The entry's inline `hooks` equal `plugins/keel/hooks/hooks.json` with `${CLAUDE_PLUGIN_ROOT}/scripts/` read as `${CLAUDE_PLUGIN_ROOT}/plugins/keel/scripts/`. `claude plugin validate .` also passes, with one warning: no marketplace description.
    - M2.red: fail, for the declared reason. With the entry written without hooks: `native-plugin-manifests claude marketplace entry hooks diverge from plugins/keel/hooks/hooks.json after resolving script paths from the package root: None`. Carries the declared signature `entry hooks diverge from`.
    - M2.green: pass. Same command after the hooks were generated from `hooks.json` into the entry.
    - M3: pass. Same scenario. `npm pack --dry-run --json` lists `bin/keel` with an executable mode, and lists `npm-shrinkwrap.json`. `the-tarball-is-the-repository` reports `44 packed files, all tracked`.
    - M3.red: fail, for the declared reason. `native-plugin-manifests packed set lacks what the host needs to run the package as a plugin: ['bin/keel', 'npm-shrinkwrap.json'] (bin/keel must be executable)`. Carries the declared signature `packed set lacks`. After `bin/keel` (`100755`) and `git mv package-lock.json npm-shrinkwrap.json`, the same check still reported `['npm-shrinkwrap.json']`: npm 11.17.0 does not pack a shrinkwrap on its own when `files` is declared. That was the reauthorization below.
    - M3.green: pass. Same command after `npm-shrinkwrap.json` was added to `files` in `package.json`.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario doctor-reads-the-diagnosed-repository` reports the scenario passing. A repository with `npm-shrinkwrap.json` declaring OpenSpec 0.0.2 and `package-lock.json` declaring 0.0.1 gets `repo pins 0.0.2`.
    - M4.red: fail, for the declared reason. `doctor-reads-the-diagnosed-repository M4 doctor read package-lock.json over npm-shrinkwrap.json, while npm installs from the shrinkwrap when both exist.`, with the line showing `repo pins 0.0.1`. Carries the declared signature `read package-lock.json over npm-shrinkwrap.json`.
    - M4.green: pass. Same command after `declaredOpenSpecVersion()` in `bin/keel.js` tries `npm-shrinkwrap.json` and then `package-lock.json`, and the unreadable detail names the file it read. The suite's two reads of this repository's own lockfile now read `npm-shrinkwrap.json`.
    - M5: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports the scenario passing. The entry's `version` and `source.version` are `5.73.1`, and `bump_version.js 99.0.0`, run in a scratch copy, moves both to `99.0.0`.
    - M5.red: fail, for the declared reason. `version-alignment scenario claude marketplace entry version was not moved by bump_version.js: {'version': '5.73.1', 'source.version': '5.73.1'}`. Carries the declared signature `claude marketplace entry version`. The first run crashed earlier, with `ENOENT … package-lock.json`, because the script still read the renamed lockfile. `LOCK_PATH` was pointed at `npm-shrinkwrap.json` before this red was taken.
    - M5.green: pass. Same command after `bumpClaudeMarketplace()` was added to `scripts/bump_version.js`.
    - M6: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario native-plugin-marketplaces` reports the scenario passing on this machine, which has codex and claude installed. The scenario packs the tree, extracts it beside a copy of the committed entry whose source is `./package`, validates, installs into an isolated `CLAUDE_CONFIG_DIR`, requires a sentinel planted only in the packed tree at the recorded `installPath`, and requires `Version: 5.73.1` in `plugin list`.
    - M6.detects: the mutation, the scenario installing from the committed npm entry (the source rewrite disabled in a scratch copy), made the scenario fail with `native-plugin-marketplaces claude plugin install failed to use the package under test; it installed from ['…/claude-config/plugins/cache/keel-marketplace/keel/5.73.1'], which does not carry the sentinel the packed tree does.` Carries the declared failure `claude plugin install failed`. Without the sentinel, the same mutation first *passed*: it installed the registry's published 5.73.1 and tested nothing in this tree. The sentinel check was added because of that. With the entry at the unpublished 5.74.0, the release state, the install itself fails with `Could not resolve @christang/keel@5.74.0 from the npm registry: E404`.
    - M7: pass. `npm test` reports `validation --all passed: baseline plus 185 scenarios, 1 skipped: output-survives-the-pipe.` `native-plugin-marketplaces` ran inside it. Separately, `npm ci --ignore-scripts` from `package.json` and `npm-shrinkwrap.json` alone installs `node_modules/.bin/openspec`, which is what CI and the host's dependency step run. Neither Stop Rule triggered: `claude plugin validate` accepted the entry as the manifest, and only `native-plugin-marketplaces`, which is skipped in CI, packs for install.
    - Review:
      - Status: pass
      - Acceptance check: every check runs a real tool: the packer's own `--json`, `claude plugin validate`, an isolated `claude plugin install`, the bump script, and doctor. M6's first detects run is the finding worth keeping. Once the npm entry was committed, the smoke would have passed on any published version by installing the registry's copy, so it tested nothing. The sentinel closes that, and it binds the smoke to the tree whatever the version.
      - Scope check: `git status --short` shows `.claude-plugin/marketplace.json`, `bin/keel`, `bin/keel.js`, `package-lock.json` → `npm-shrinkwrap.json`, `package.json`, `scripts/bump_version.js`, and `scripts/validate_plugin.py`, this task's reauthorized Touch, plus this change's own directory. The header comment of `bump_version.js` still told the reader to tag by hand, a line #162 missed. It was corrected here because the same comment had to name the new markers anyway.
      - Findings: Resolved here: M5 — the header comment of `scripts/bump_version.js` still said "tag `vX.Y.Z`, push, and publish a GitHub Release" after #162 corrected its closing hint. It now points to the printed steps and says nothing is tagged by hand; M5 runs the script.
    - Blocker: none
    - Reauthorizations: 2026-09-27 — `package.json` added to Touch. npm 11.17.0 does not pack `npm-shrinkwrap.json` when `package.json` declares `files` (`npm pack --dry-run --json` listed only `LICENSE`, `README.md`, `README.zh-CN.md`, `package.json` at the root), so the lockfile has to be named in `files`. No evidence had been recorded, so none went stale.

- [x] 1.3 The install instructions say the Claude plugin carries its CLI
  - Covers:
    - E1
    - E4
  - Read:
    - README.md
    - README.zh-CN.md
  - Touch:
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: evidence-first
    - Reason: the task changes install prose only; the behavior it describes is proven by 1.1 and 1.2, and a sentence has no failing state to observe first.
    - M1: `README.md` `## Install` states that on Claude Code the plugin alone is enough, that the agent's `keel` comes from it, that a global npm install is for terminals and Codex, and that a stale global copy shadows the plugin's and is reported
    - M2: `README.zh-CN.md` states the same, and names `/reload-plugins`
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the README would have to promise automatic updates, because enabling auto-update is the next change on #164 and not this one.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8a0e170a029b1ad9ef8d2ce23d02d55e5e3a314e4da936e33513f52e480bdad8
    - M1: `README.md` `## Install` now opens with **Claude Code**: the plugin is the whole install. It is the published `@christang/keel` package, carrying the CLI and bundled OpenSpec, and the agent's `keel` runs the plugin's copy. An update applies after `/reload-plugins` or at the next start. **Codex, and your own terminal** keep `npm install -g`. A closing paragraph says a global `keel` comes first on PATH, ahead of the plugin's copy, to keep it at the plugin's version or remove it with `npm rm -g @christang/keel`, and that the session-start line names it when the two disagree.
    - M2: `README.zh-CN.md` `## 安装` states the same three points in Chinese, including `/reload-plugins` and `npm rm -g @christang/keel`.
    - Review:
      - Status: pass
      - Acceptance check: the prose describes exactly what 1.1 and 1.2 made true, and nothing more. It does not mention automatic updates, because auto-update is still off for this marketplace until the next change on #164 declares it, so the Stop Rule held. The marketplace commands name `TanglmChris/keel` and `keel@keel-marketplace`, the name `.claude-plugin/marketplace.json` declares.
      - Scope check: `git status --short` shows `README.md` and `README.zh-CN.md`, this task's Touch, plus this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [ ] 2.1 Release
  - Covers:
    - E2
    - E3
    - I3
    - I5
    - I9
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-native-plugin-package/spec.md
    - openspec/specs/keel-native-runtime-projection/spec.md
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
    - Reason: this task's whole effect is version markers, a changelog entry, and promoted specs. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes after `node scripts/bump_version.js minor`, with the new section written into the stub
    - M2: `keel/CHANGELOG.md` states that on Claude the plugin and CLI are one artifact, what an existing user sees on the next update, and the merge-to-publish window
    - M3: both deltas are promoted, `node node_modules/.bin/openspec validate the-plugin-is-the-published-package --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "so an updated plugin applies only after restarting" — `versionReport()` in
  `plugins/keel/scripts/session-start.js`. `/reload-plugins` applies it in the running session.
  Updated by: 1.1
- I2: `VERSION_DRIFT_RESTART_TOKENS = ("fixed at session start", "restart")` — `scripts/validate_plugin.py`,
  which asserts the wording I1 removes.
  Updated by: 1.1
- I3: "the report states that a session's hooks are fixed at session start, so an updated plugin applies
  only after restarting" — `openspec/specs/keel-native-runtime-projection/spec.md`.
  Updated by: 2.1
- I4: "Two pieces: the `keel` CLI and the `keel` plugin." — `## Install` in `README.md`, and its
  counterpart in `README.zh-CN.md`. On Claude the plugin is both.
  Updated by: 1.3
- I5: "Keel's native plugin MUST treat the separately installed `@christang/keel` CLI and OpenSpec
  dependency as executable prerequisites" — `openspec/specs/keel-native-plugin-package/spec.md`. True
  on Codex only after this change.
  Updated by: 2.1
- I6: `claude_entry.get("source") != "./plugins/keel"` — `native-plugin-manifests` in
  `scripts/validate_plugin.py`, which requires the relative-path source this change replaces.
  Updated by: 1.2
- I7: "package-lock.json, both native plugin manifests" and `LOCK_PATH` — `scripts/bump_version.js`,
  which moves the lockfile this change renames and not the marketplace entry's two versions.
  Updated by: 1.2
- I8: "repo package-lock.json unreadable" — the doctor detail in `bin/keel.js`, which names one
  lockfile when two are read.
  Updated by: 1.2
- I9: "update and restart semantics pick up a changed temporary test version" —
  `openspec/specs/keel-native-plugin-package/spec.md`, `Claude marketplace installs Keel`.
  Updated by: 2.1
- I10: "a session's hooks are pinned at start, so a plugin update needs a **restart** to take effect" —
  native memory `keel-moved-from-windows-to-mac.md`, outside this repository.
  Discard reason: already corrected in memory on 2026-09-27 during authoring; `/reload-plugins` made it
  untrue before this change, so no task of this change owns it.

## Expectation Coverage

- E1: On Claude Code, installing the plugin is enough: the agent's `keel` and the hooks' CLI come from
  it, with no separate npm install (D1, D3, D5). Covered by: 1.1, 1.2, 1.3
- E2: On Claude Code, the plugin and the CLI cannot be at different versions, because they are one
  published artifact (D1, D2). Covered by: 1.2
- E3: A version mismatch tells the user an update applies after `/reload-plugins` or the next start,
  not after a restart (D8). Covered by: 1.1
- E4: A stale global `keel` that shadows the plugin's copy is reported with its remedies, and its
  absence is not (D6). Covered by: 1.1, 1.3
- E5: Codex behavior is unchanged: `plugins/keel` keeps its manifest, default-discovered hooks, and
  separately installed CLI. Discard reason: nothing in this change touches the Codex manifest, the Codex
  marketplace, or `hooks.json`; 1.2's M2 compares against `hooks.json` without editing it.
