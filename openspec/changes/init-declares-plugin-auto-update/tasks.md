# Tasks

## 1. Declare it

- [x] 1.1 `keel --init`/`--install` declare auto-update for the Keel marketplace in `.claude/settings.json`, uninstall removes only Keel's entry, and doctor reports the declaration
  - Covers:
    - keel-native-plugin-package / Project setup declares Claude plugin auto-update / Init declares auto-update
    - keel-native-plugin-package / Project setup declares Claude plugin auto-update / Existing settings are kept
    - keel-native-plugin-package / Project setup declares Claude plugin auto-update / Uninstall removes only Keel's entry
    - keel-native-plugin-package / Project setup declares Claude plugin auto-update / Doctor reports the declaration
    - keel-native-plugin-package / Project setup declares Claude plugin auto-update / Other targets are untouched
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
  - Read:
    - scripts/install_to_repo.py
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - scripts/install_to_repo.py
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `init-declares-plugin-auto-update` scenario runs `keel --init --target claude` in a scratch repository and requires `.claude/settings.json` to declare `keel-marketplace` with source `{"source": "github", "repo": "TanglmChris/keel"}` and `autoUpdate: true`. Fails with: `declared no plugin auto-update`
    - M2: the same scenario runs `keel --install --target claude` over three existing files. The first holds only `permissions`; it must keep them and gain Keel's entry. The second has a `keel-marketplace` entry with a local `directory` source and no `autoUpdate`; it must keep that source and gain `autoUpdate: true`. The third has an entry with `autoUpdate: false`; it must keep `false`. A second install must report `skip .claude/settings.json`. Fails with: `merge into an existing .claude/settings.json`
    - M3: the same scenario runs `keel --uninstall --target claude` over a file holding Keel's exact entry beside `permissions`, and requires the entry gone and `permissions` kept. Over a file whose entry the project changed, it requires the entry kept. Fails with: `uninstall left`
    - M4: the same scenario runs `keel --doctor --target claude` over the three states (on, off, absent). It requires one `plugin auto-update` line with `ok`, `manual` naming the project's `false`, and `manual` naming `keel --install --target claude`. Fails with: `no plugin auto-update line`
    - M5 (regression): the same scenario runs `keel --init --target codex` and requires no `.claude/settings.json`. Detects: `the settings strategy is collected for every target` -> `wrote .claude/settings.json for codex`
    - M6 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if an existing scenario asserts the exact set of files `--init` or `--install` writes and would need its expectation widened, because that is an interface other tools may read.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:72dc75008b1ceebbc79c1371908874b79c7417e86be7c181bc82783b56890731
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario init-declares-plugin-auto-update` reports the scenario passing. `keel --init --target claude` in a fresh scratch repository writes `.claude/settings.json` declaring `keel-marketplace` as `{"source": {"source": "github", "repo": "TanglmChris/keel"}, "autoUpdate": true}`.
    - M1.red: fail, for the declared reason. Calling the check's helper directly before any installer change reported `M1 keel --init declared no plugin auto-update: keel-marketplace in .claude/settings.json is None, …`. Carries the declared signature `declared no plugin auto-update`.
    - M1.green: pass. Same helper after `scripts/install_to_repo.py` gained the `claude-marketplace-settings` strategy, `merge_claude_marketplace_settings()`, collected on the Claude target only.
    - M2: pass. Same scenario. Three existing files:
      - a file with only `permissions` keeps them and gains Keel's entry;
      - an entry with a local `directory` source keeps that source and gains `autoUpdate: true`;
      - an entry with `autoUpdate: false` keeps `false`.
      A second `--install` reports `skip .claude/settings.json` for each.
    - M2.red: fail, for the declared reason. `M2 permissions-only: install did not merge into an existing .claude/settings.json as declared; entry is None, …`. Carries the declared signature `merge into an existing .claude/settings.json`.
    - M2.green: pass. Same helper after the merge: an existing entry keeps its `source`, `setdefault("autoUpdate", True)` never overwrites a stated value, and every other key is carried over.
    - M3: pass. Same scenario. `keel --uninstall --target claude` removes Keel's exact entry and keeps `permissions`, and keeps an entry the project changed to `autoUpdate: false`.
    - M3.red: fail, for the declared reason. `M3 uninstall left Keel's own marketplace entry behind: {'permissions': …, 'extraKnownMarketplaces': {'keel-marketplace': …}}`. Carries the declared signature `uninstall left`.
    - M3.green: pass. Same helper after `remove_claude_marketplace_settings()` and `plan_uninstall_claude_marketplace_settings()` were added. They remove only an entry equal to Keel's, drop an emptied `extraKnownMarketplaces`, and remove a file left as `{}`.
    - M4: pass. Same scenario. Doctor prints exactly one `plugin auto-update` line in each state:
      - on: `ok - … autoUpdate: true; Keel reads the declaration; the host does not expose whether updates run`;
      - off: `manual - … autoUpdate: false, which is the project's choice …`;
      - absent: `manual - not declared, … run keel --install --target claude, or enable it under /plugin → Marketplaces`.
    - M4.red: fail, for the declared reason. `M4 on: doctor printed no plugin auto-update line: []`. Carries the declared signature `no plugin auto-update line`.
    - M4.green: pass. Same helper after `pluginAutoUpdateDeclaration()` was added to `bin/keel.js` and printed on the Claude target after `native plugin runtime`.
    - M5: pass. Same scenario. `keel --init --target codex` writes no `.claude/settings.json`. Green before any change, as a regression check should be.
    - M5.detects: the mutation, the settings strategy collected for every target (`if "claude" in targets:` changed to `if True:` in `collect_actions()`), made the check fail with `M5 keel --init --target codex wrote .claude/settings.json for codex: {'extraKnownMarketplaces': …}`. Carries the declared failure `wrote .claude/settings.json for codex`. Restored from a backup afterwards.
    - M6: pass. `npm test` reports `validation --all passed: baseline plus 186 scenarios, 1 skipped: output-survives-the-pipe.` The first full run failed `uninstall` with `left empty directory behind: .claude`, because removing the settings file could leave `.claude/` empty. Uninstall now ends with the same `rmdir_if_empty_action` the other paths use, and the scenario's expectation was left as it was. The Stop Rule did not trigger: no scenario asserts the exact file set `--init` writes.
    - Review:
      - Status: pass
      - Acceptance check: every check drives the real CLI (`--init`, `--install`, `--uninstall`, `--doctor`) against scratch repositories, and each red was taken by calling that check's helper alone before its implementation existed. The merge never takes a decision away from the project: a local source and a stated `false` both survive. Doctor says it reads the declaration only, because the host's `marketplace list --json` carries no auto-update state (F2).
      - Scope check: `git status --short` shows `scripts/install_to_repo.py`, `bin/keel.js`, and `scripts/validate_plugin.py`, this task's Touch, plus this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 The install instructions say project setup turns on plugin auto-update
  - Covers:
    - E2
  - Read:
    - README.md
    - README.zh-CN.md
  - Touch:
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: evidence-first
    - Reason: the task changes install prose only; the behavior it describes is proven by 1.1, and a sentence has no failing state to observe first.
    - M1: `README.md` `## Install` states that `keel --init` declares auto-update for the Keel marketplace in `.claude/settings.json`, that updates then arrive in the background and apply after `/reload-plugins` or at the next start, and how a project opts out
    - M2: `README.zh-CN.md` states the same
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the prose would have to claim the host is observed to update, because Keel reports only the declaration.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:dc9e9f86f6e435c77d6a07ff9bf9e3c0d6967e4659fc81504046503f407a0631
    - M1: `README.md` `## Install` now says four things:
      - `keel --init --target claude` and `keel --install` declare auto-update for `keel-marketplace` in the project's `.claude/settings.json`, which Claude reads before its own default of off;
      - a release is fetched in the background after a session's first message, and applies after `/reload-plugins` or at the next start;
      - to opt out, set the entry's `autoUpdate` to `false`, which Keel keeps;
      - `keel --doctor` reports which value is declared.
    - M2: `README.zh-CN.md` `## 安装` states the same, in Chinese.
    - Review:
      - Status: pass
      - Acceptance check: the prose names the declaration and its effect as the host documents it. It does not claim that Keel observes updates happening, so the Stop Rule held, and the doctor wording in 1.1 draws the same line. It replaces the 5.74.0 sentence I1 names, keeping the reload guidance that stays true.
      - Scope check: `git status --short` shows `README.md` and `README.zh-CN.md`, this task's Touch, plus this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [ ] 2.1 Release, and declare auto-update in this repository
  - Covers:
    - E1
    - E3
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude/settings.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-native-plugin-package/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, a promoted spec, and running the shipped installer on this repository. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes after `node scripts/bump_version.js minor`, with the new section written into the stub
    - M2: `node bin/keel.js --install --target claude` on this repository leaves `.claude/settings.json` with its `permissions` intact and Keel's `keel-marketplace` entry, and `node bin/keel.js --doctor` reports `plugin auto-update: ok`
    - M3: the delta is promoted, `node node_modules/.bin/openspec validate init-declares-plugin-auto-update --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if `keel --install` on this repository changes any file outside this task's Touch.
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - M3: pending
    - Review: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "After an update, `/reload-plugins` applies it in the running session; otherwise it applies at the
  next start." — `## Install` in `README.md` and its counterpart in `README.zh-CN.md`, written in 5.74.0
  while updates still had to be started by hand. The wording stays true; what it omits is that the
  update now arrives by itself.
  Updated by: 1.2
- I2: "Still open on #164: declaring auto-update for the marketplace from `keel --init`" — the 5.74.0
  entry in `keel/CHANGELOG.md`. History, left as written; the new entry records that it is done.
  Updated by: 2.1

## Expectation Coverage

- E1: A project set up with `keel --init --target claude` gets Keel plugin updates without anyone
  toggling auto-update by hand (D1, D2). Covered by: 1.1, 2.1
- E2: A reader of the install instructions knows updates arrive by themselves and how to opt out.
  Covered by: 1.2
- E3: A project's own choices in `.claude/settings.json` survive install and uninstall (D1, D3).
  Covered by: 1.1
