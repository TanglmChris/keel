# Tasks

## 1. The plugin is the tagged repository

- [x] 1.1 A root manifest describes the plugin, and Keel's marketplace installs the tagged tree from git
  - Covers:
    - keel-native-plugin-package / The Claude plugin is the tagged repository / One tree carries the plugin and its CLI
    - keel-native-plugin-package / The Claude plugin is the tagged repository / The git install carries the pinned OpenSpec
    - keel-native-plugin-package / The Claude plugin is the tagged repository / An npm-sourced install updates to the git-sourced one
    - D1
    - D2
    - D4
    - D5
    - F2
    - F3
    - F4
    - F6
  - Read:
    - .claude-plugin/marketplace.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/hooks/hooks.json
    - scripts/bump_version.js
    - scripts/validate_plugin.py
  - Touch:
    - .claude-plugin/plugin.json
    - .claude-plugin/marketplace.json
    - scripts/bump_version.js
    - scripts/validate_plugin.py
    - plugins/keel/scripts/session-start.js
    - bin/keel
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `native-plugin-manifests` requires `.claude-plugin/plugin.json` at the root, with the name, version, and description of `plugins/keel/.claude-plugin/plugin.json`, skills and agent that resolve inside the repository, and hooks equal to `plugins/keel/hooks/hooks.json` after resolving script paths from the root. Fails with: `no root plugin manifest`
    - M2: `native-plugin-manifests` requires the Claude marketplace entry's source to be `{source: url, url: https://github.com/TanglmChris/keel.git, ref: v<package version>}`, its `version` the package version, and no `skills`, `agents`, or `hooks` on it. Fails with: `is not the tagged repository`
    - M3: `version-alignment` runs `bump_version.js 99.0.0` in a scratch copy and requires the root manifest's version to be `99.0.0` and the entry's `version` and `source.ref` to be `99.0.0` and `v99.0.0`. Fails with: `root plugin manifest was not moved by bump_version.js`
    - M4 (regression): `native-plugin-marketplaces`, run on this machine with the `claude` CLI, stages the working tree as a scratch git repository tagged `v<version>`, installs it in an isolated configuration through a copy of the committed entry pointed at it with a `file://` URL, and requires the sentinel, the six Keel skills and both hooks in `claude plugin details`, and `node_modules/.bin/openspec --version` equal to the shrinkwrap's OpenSpec version.
    - M5 (regression): in an isolated configuration, Keel installed from the published 5.79.0 npm-sourced entry is updated with `claude plugin update` after that marketplace is replaced by the staged git-sourced entry at a higher version, and the updated install carries the sentinel and OpenSpec at the shrinkwrap's version.
    - M6 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the host refuses the root manifest beside `marketplace.json`, or installs the git source without `node_modules`, because D1 and the owner's decision rest on F2 and F3.
    - Stop if M5 shows an npm-sourced install cannot update to the git-sourced one, because existing users would then need a manual step the proposal says they do not.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2c44467bf643a1a1f56aa20315f15a873a87093853ac9e9777e04cf48f0f9be3
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario native-plugin-manifests` reports the scenario passing. `.claude-plugin/plugin.json` carries the name, version 5.79.0, and description of `plugins/keel/.claude-plugin/plugin.json`, `skills: ["./plugins/keel/skills/"]`, the Claude agent, and hooks equal to `hooks.json` with script paths under `plugins/keel/scripts/`.
    - M1.red: fail, for the declared reason. Before the manifest existed the scenario reported `native-plugin-manifests has no root plugin manifest at .claude-plugin/plugin.json, so a git-sourced entry has nothing to read the skills, agent, and hooks from.` Carries the declared signature `no root plugin manifest`.
    - M1.green: pass. Same command after `.claude-plugin/plugin.json` was written from the plugin manifest and `hooks.json`; it then stopped at M2.
    - M2: pass. Same scenario. The entry reads `{"name": "keel", "version": "5.79.0", "source": {"source": "url", "url": "https://github.com/TanglmChris/keel.git", "ref": "v5.79.0"}, "description": …}` and restates no component.
    - M2.red: fail, for the declared reason. With the root manifest in place, the scenario reported `native-plugin-manifests claude marketplace entry is not the tagged repository at v5.79.0: source {'source': 'npm', 'package': '@christang/keel', 'version': '5.79.0'}, version '5.79.0', restated components ['skills', 'agents', 'hooks']`. Carries the declared signature `is not the tagged repository`.
    - M2.green: pass. Same command after the entry's source became the git URL at `v5.79.0` and its `skills`, `agents`, and `hooks` were removed.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports the scenario passing; its scratch `bump_version.js 99.0.0` moves the root manifest to `99.0.0` and the entry to `version: 99.0.0`, `source.ref: v99.0.0`.
    - M3.red: fail, for the declared reason. Before `bump_version.js` changed, the scenario reported `version-alignment scenario root plugin manifest was not moved by bump_version.js: '5.79.0'`. Carries the declared signature `root plugin manifest was not moved by bump_version.js`.
    - M3.green: pass. Same command after `bumpClaudeMarketplace()` wrote the root manifest's version and the entry's `version` and `source.ref`, and refused an entry that is not git-sourced.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario native-plugin-marketplaces` reports the scenario passing in about 10 s. `stage_claude_market_under_test` now stages `git ls-files --cached --others --exclude-standard` as a scratch repository tagged `v5.79.0`, and the committed entry's copy points at it by `file://` URL. `claude plugin details` lists the Keel skills with `SessionStart` and `PreToolUse`, and the installed `node_modules/.bin/openspec --version` prints `1.13.2`, the shrinkwrap's pin. With `pinned` forced to `9.9.9` the same scenario failed with `… does not carry the pinned OpenSpec 9.9.9: … -> '1.13.2\n'`, so the assertion is reached; restored afterwards. `native-plugin-install-matrix`, the other caller of the staging helper, passes too.
    - M5: pass. A one-off script under an isolated `CLAUDE_CONFIG_DIR` added a local marketplace holding `origin/main`'s npm-sourced entry and installed `keel` 5.79.0 from npm. It then rewrote that marketplace to the staged git entry relabeled `5.79.1` at `v5.79.1`, and ran `claude plugin marketplace update keel-marketplace` and `claude plugin update keel@keel-marketplace`, which printed `Plugin "keel" updated from 5.79.0 to 5.79.1`. The new install path carries the sentinel, `node_modules/.bin/openspec` prints `1.13.2` against the pinned `1.13.2`, and `claude plugin details` lists six skills and both hooks. The Stop Rules held.
    - M6: pass. `npm test` reports `validation --all passed: baseline plus 189 scenarios, 1 skipped: output-survives-the-pipe.` The first run failed `assertion-shape-count` (81 sites against 80 recorded): two of the new M4 conditions guarded distinct failures behind one message. Each was split into its own message rather than raising the bound.
    - Review:
      - Status: pass
      - Acceptance check: M1 to M3 pin the shape the official directory needs: one root manifest, an entry that only says where the repository is, and a bump that moves all three markers. M4 and M5 prove the shape works on the real host, as a fresh install and as an update from today's npm-sourced install, both ending with the OpenSpec the lockfile pins. That is E1.
      - Scope check: `git status --short` shows `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `scripts/bump_version.js`, `scripts/validate_plugin.py`, `plugins/keel/scripts/session-start.js`, `bin/keel`, `README.md`, and `README.zh-CN.md`, this task's Touch, plus this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 Each release states its official directory entry
  - Covers:
    - keel-native-plugin-package / Each release states its official directory entry / The entry is pinned to the release commit
    - keel-native-plugin-package / Each release states its official directory entry / A malformed pin is refused
    - keel-native-plugin-package / Each release states its official directory entry / The release notes carry the entry
    - D3
    - F1
    - F5
  - Read:
    - .github/workflows/publish.yml
    - scripts/validate_plugin.py
  - Touch:
    - scripts/official_entry.js
    - .github/workflows/publish.yml
    - scripts/validate_plugin.py
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `official-directory-entry` scenario runs `node scripts/official_entry.js 5.80.0 <40 hex>` and requires one JSON object with `name: keel`, `category: development`, the homepage, the root manifest's description, and `source` equal to `{source: url, url: https://github.com/TanglmChris/keel.git, sha: <that sha>}`. Fails with: `printed no official directory entry`
    - M2: the same scenario runs the script with `5.80` and with a 39-character sha, and requires a non-zero exit and empty stdout for each. Fails with: `accepted a malformed pin`
    - M3: the same scenario reads `.github/workflows/publish.yml` and requires the release step to run `scripts/official_entry.js` with `$VERSION` and `$SHA` and append its output to `notes.md` before `gh release create`. Fails with: `release notes do not carry the official directory entry`
    - M4 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if appending to the notes would need a new permission or secret in `publish.yml`.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2e7015de6878108f7f98066b082fe03b68d643d0b4d946cf8d627e247a595dae
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario official-directory-entry` reports the scenario passing. `node scripts/official_entry.js 5.80.0 0123…4567` prints `{name: keel, description: <root manifest's>, category: development, source: {source: url, url: https://github.com/TanglmChris/keel.git, sha: 0123…4567}, homepage: https://github.com/TanglmChris/keel}`.
    - M1.red: fail, for the declared reason. Before the script existed the scenario reported `official-directory-entry M1 printed no official directory entry: exit 1, "… Cannot find module '…/scripts/official_entry.js' …"`. Carries the declared signature `printed no official directory entry`.
    - M1.green: pass. Same command after `scripts/official_entry.js` printed the entry from the root manifest; it then stopped at M2.
    - M2: pass. Same scenario. `5.80` and a 39-character sha each exit 1 with empty stdout and a usage line on stderr.
    - M2.red: fail, for the declared reason. With only the happy path written, the scenario reported `official-directory-entry M2 accepted a malformed pin ('5.80', '0123…4567'): exit 0, stdout '{ "name": "keel", … }'`. Carries the declared signature `accepted a malformed pin`.
    - M2.green: pass. Same command after the script refused a version that is not `X.Y.Z` or a sha that is not 40 lowercase hex characters, before printing anything.
    - M3: pass. Same scenario. The release step in `.github/workflows/publish.yml` appends `## Official directory entry` and a fenced block holding `node scripts/official_entry.js "$VERSION" "$SHA"` to `notes.md` before `gh release create`. The same lines run locally under `bash -euo pipefail` with `VERSION=5.79.0` and the commit of `v5.79.0` produced the section, pinned to `385ea4bca81f54457f55ef0ba5d7403ba1a99d37`. No permission, secret, or network call was added, so the Stop Rule held.
    - M3.red: fail, for the declared reason. Before the workflow changed the scenario reported `official-directory-entry M3 release notes do not carry the official directory entry: …`. Carries the declared signature `release notes do not carry the official directory entry`.
    - M3.green: pass. Same command after the three lines were added to the release step.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 190 scenarios, 1 skipped: output-survives-the-pipe.` The first run failed two scenarios. `the-tarball-is-the-repository` refused the new script because Git did not track it yet, and staging it with `git add` resolved that. `assertion-shape-count` counted M3's single condition as guarding four failures behind one message, so it is now four checks, each with its own message.
    - Review:
      - Status: pass
      - Acceptance check: E2 asks that every release state its pinned entry and submit nothing. M1 and M2 prove the entry is exactly the directory's shape and cannot be half-formed. M3 proves the release job carries it, and the local run of those lines shows the real output for the current release.
      - Scope check: `git status --short` shows `scripts/official_entry.js`, `.github/workflows/publish.yml`, `scripts/validate_plugin.py`, `README.md`, and `README.zh-CN.md` for this task, plus the files 1.1 declared complete and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1
    - E2
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/plugin.json
    - .claude-plugin/marketplace.json
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
    - Reason: this task's effect is version markers, a changelog entry, and a promoted spec. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes after `node scripts/bump_version.js minor`, with the new section written into the stub
    - M2: the delta is promoted, `node node_modules/.bin/openspec validate plugin-installs-from-git --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ef0b04ad2c87dc4846072bb00e38ba995fd28dfa6aca101e1786be591aed1f51
    - M1: pass. `node scripts/bump_version.js minor` moved every marker from 5.79.0 to 5.80.0, including `.claude-plugin/plugin.json` and the entry's `ref` (`v5.80.0`). `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.80.0 section written into the stub. The Stop Rule held.
    - M2: pass. The delta is promoted into `keel-native-plugin-package`: the npm requirement is replaced by the two ADDED ones, and the catalog and CLI-compatibility requirements no longer name the published package, which the delta records as MODIFIED. `node node_modules/.bin/openspec validate plugin-installs-from-git --strict` reports the change valid, `openspec validate --specs --strict` reports `26 passed, 0 failed`, and `npm test` reports `validation --all passed: baseline plus 190 scenarios, 1 skipped: output-survives-the-pipe.`, with `native-plugin-marketplaces` installing the staged tree at `v5.80.0`.
    - Review:
      - Status: pass
      - Acceptance check: E1 and E2 hold at the released version: the entry and the root manifest both read 5.80.0, the install smoke ran at that tag, and the release job will append the entry pinned to the tag's commit. The spec no longer claims the plugin is the npm package anywhere.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, and the promoted spec, this task's Touch, plus the files 1.1 and 1.2 declared complete and this change's own directory.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/175 — the submission to Anthropic's official directory, and how a listed plugin's pin advances to a new release, are the owner's and not yet known.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "The Claude plugin is the published package" — the requirement of that name in
  `openspec/specs/keel-native-plugin-package/spec.md`, and the Claude catalog clause "the Claude
  catalog MUST reference the published package that contains it" in the same file.
  Updated by: 2.1
- I2: "It is the published `@christang/keel` package, so it carries the `keel` CLI and the bundled
  OpenSpec" — `README.md`'s Claude Code install paragraph, and its counterpart in `README.zh-CN.md`.
  Updated by: 1.1
- I3: "On Claude the plugin is the published package" — comments in
  `plugins/keel/scripts/session-start.js`, `bin/keel`, `scripts/bump_version.js`, and
  `scripts/validate_plugin.py`, and `bump_version.js`'s refusal "expected an npm-sourced keel entry".
  Updated by: 1.1
- I4: "The committed entry installs the published package at this release" — the docstring of
  `stage_claude_market_under_test` in `scripts/validate_plugin.py`.
  Updated by: 1.1

## Expectation Coverage

- E1: Keel's own marketplace and Anthropic's official directory install the same tagged repository
  tree, and an existing npm-sourced install moves to it on update (D1, D2, D5). Covered by: 1.1, 2.1
- E2: Every release states the official directory entry pinned to its tag's commit, ready for the
  owner to submit, and Keel submits nothing (D3). Covered by: 1.2, 2.1
