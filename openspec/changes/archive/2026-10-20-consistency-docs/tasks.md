# Tasks

## 1. Make the configuration file and the docs follow their sources

- [x] 1.1 Order the configuration file's blocks, and correct `docs/updating.md` and the three README sentences
  - Covers:
    - keel-native-plugin-package / The configuration file and the Chinese docs follow their sources / The configuration file documents its declarations in order
    - D1
    - D3
  - Read:
    - openspec/changes/consistency-docs/design.md
    - keel/config.yaml
    - src/core/config.js
    - docs/updating.md
  - Touch:
    - keel/config.yaml
    - docs/updating.md
    - README.md
    - README.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario config-documents-in-declaration-order`: the `# <name> (optional):` comment blocks of `keel/config.yaml` name each entry of `CONFIG_DECLARATIONS` (read from `src/core/config.js`) exactly once and in that order, and its scoped-name sentence names `push-protected`; `docs/updating.md` no longer says "skills and agents" and names the hung-query fallback (`config.toml`) and the post-release `E404`; both READMEs no longer say "A clear there keeps no title" or "noticed expiry", and point to `keel chat help`. Fails with: `config-documents-in-declaration-order:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario continuation-docs`, `--scenario a-count-is-derived-from-what-it-counts`, `--scenario readme-states-the-cli`, `--scenario readme-zh-matches-english`, and the baseline pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:cdb7898c12d36ef496d84eea6a875108afdf73fd811123d442c6b886b99887f0 (keel 5.176.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario config-documents-in-declaration-order` reports `config-documents-in-declaration-order scenario passed.` (exit 0).
    - M1.red: fail. Before the change: `config-documents-in-declaration-order: keel/config.yaml documents ['owner_language', 'patrol', 'issue_roles', 'read_only_roles', 'fast_check', 'authorize', 'precedents', 'triage', 'patrol', 'full_mode_paths', 'merge', 'external_agents'], not [... 'fast_check' through 'owner_language'] in that order.` (exit 1).
    - M1.green: pass. The scenario passed after four changes:
      - `keel/config.yaml`:
        - the comment blocks follow `CONFIG_DECLARATIONS` order, one each, above their declarations;
        - the two patrol blocks are merged;
        - an `executor_tier` block is added;
        - `push-protected` is in the scoped-name sentence;
        - the `continuation` paragraph now says the name changes nothing since #414.

        The two pinned texts are verbatim, and the declared values are unchanged: `keel --doctor` lists the same authorize entries, and `keel context` reads the same merge rule.
      - `docs/updating.md` names skills only, and documents the #412 fallback and the #421 `E404`.
      - Both READMEs rewrite the three sentences and point to each group's help. All six help commands exit 0.
    - M2: pass. `continuation-docs`, `a-count-is-derived-from-what-it-counts`, `readme-states-the-cli`, `readme-zh-matches-english`, and `assertion-shape-count` (74) each pass, and the baseline reports `Keel v4.1.0 baseline validation passed.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: the order is read from `CONFIG_DECLARATIONS`, so the file now documents what the code says it does. Each corrected sentence was checked against the code or a command:
        - the help exit codes were measured;
        - the #412 fallback is as shipped in 5.174.0;
        - the `E404` text was seen at the 5.175.0 release.
      - Scope check: `git status --short` lists `keel/config.yaml`, `docs/updating.md`, both READMEs, `scripts/validate_plugin.py`, and this change's directory.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 Bring the Chinese docs to their English pages
  - Covers:
    - keel-native-plugin-package / The configuration file and the Chinese docs follow their sources / A Chinese doc matches its English page
    - D2
  - Read:
    - openspec/changes/consistency-docs/design.md
    - docs/shift-change.md
    - docs/chat-slack-setup.md
  - Touch:
    - docs/shift-change.zh-CN.md
    - docs/chat-slack-setup.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario docs-zh-match-english`: every `docs/*.zh-CN.md` has the same heading count and code-fence count as its `docs/*.md` and names every `keel <word>` command that page names, and `docs/chat-slack-setup.zh-CN.md` carries the edits-and-deletions sentence. Fails with: `docs-zh-match-english:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario readme-zh-matches-english` and `--scenario shift-change` pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f133e97db9ab81b92e3a83b23b913d7b16fecd37a6b2665c584294c1fc708c5c (keel 5.176.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario docs-zh-match-english` reports `docs-zh-match-english scenario passed.` (exit 0) over `chat-slack-setup`, `cli-team`, and `shift-change`.
    - M1.red: fail. Before the change: `docs-zh-match-english: shift-change.md has 8 headings and shift-change.zh-CN.md has 5.` (exit 1).
    - M1.green: pass. The scenario passed after two changes:
      - `docs/shift-change.zh-CN.md` was rewritten against the English page. It now has the same 8 sections, adds the `--role` rows, the background-CLI clear, the worktree-note status, the `unstarted` check item, and the waiter details, and names `keel patrol` and `keel tick`.
      - `docs/chat-slack-setup.zh-CN.md` gained "编辑和删除也会同步过去。"
    - M2: pass. `readme-zh-matches-english scenario passed.` and `shift-change scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: every Chinese doc that exists now carries its English page's sections, code fences, and commands, and the check covers any Chinese page added later.
      - Scope check: `git status --short` adds `docs/shift-change.zh-CN.md`, `docs/chat-slack-setup.zh-CN.md`, and `scripts/validate_plugin.py` to task 1.1's files.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E3
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
    - Reason: this task writes the version markers, a changelog entry, and the spec promotion. The behavior is proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-native-plugin-package`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2a0535eedd478279884d117397a696ac382d73c8daa62986fab24e6059cacaea (keel 5.176.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.176.0 → 5.177.0. With the section "The configuration file and the docs follow their sources" written, `version-alignment scenario passed.` (exit 0).
    - M2: the ADDED requirement "The configuration file and the Chinese docs follow their sources" is promoted into `keel-native-plugin-package`. `published-specs-validate-strictly scenario passed: 33 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test` ran on commit 3f9bb5a (clean tree), started 21:24 at load 5: `validation --all passed: baseline plus 298 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E3. The version markers, the 5.177.0 section, and the published spec carry the change, and the full suite passes on the committed tree.
      - Scope check: beyond tasks 1.1 and 1.2, the only files are the version markers, `keel/CHANGELOG.md`, and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: the comment blocks of `keel/config.yaml` out of `CONFIG_DECLARATIONS` order, the second `patrol (optional)` block, and "`issue`, `issue-close`, `cleanup`, and `chat-reply` are the names that carry the resource they reach" — `keel/config.yaml`. Updated by: 1.1.
- I2: "its skills and agents after `/reload-plugins`" and the "Skills and agents" row — `docs/updating.md`. Updated by: 1.1.
- I3: "A clear there keeps no title.", "release and noticed expiry tell them", and the ordinals beside the authorization list — `README.md` and `README.zh-CN.md`. Updated by: 1.1.
- I4: "## 便条" as the last of five sections, with no `keel patrol` or `keel tick` — `docs/shift-change.zh-CN.md`; the edit-sync list without "Edits and deletions carry over." — `docs/chat-slack-setup.zh-CN.md`. Updated by: 1.2.
- I5: "README and docs follow in the next part of #413" and "follow in the third part of #413" — the 5.175.0 and 5.176.0 sections of `keel/CHANGELOG.md`, which this release completes. Discard reason: a changelog section records what was true at its release and is not rewritten; the 5.177.0 section says the third part shipped.

## Expectation Coverage

- E1: `keel/config.yaml` documents its declarations once each, in order. `docs/updating.md` and the three README sentences say what Keel does (#413; D1, D3). Covered by: 1.1
- E2: Each Chinese doc matches its English page (#413; D2). Covered by: 1.2
- E3: The release carries both, and the spec is promoted. Covered by: 2.1
