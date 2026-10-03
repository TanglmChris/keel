# Tasks

## 1. The directory sees keel-openspec, and each release refreshes it

- [x] 1.1 `scripts/directory_tree.js` builds the directory tree from the npm package, renamed and with an icon
  - Covers:
    - keel-native-plugin-package / Each release updates the directory branch / The tree is the package with the directory's name
    - D1
    - D4
    - F3
  - Read:
    - package.json
    - .claude-plugin/plugin.json
  - Touch:
    - scripts/directory_tree.js
    - assets/directory/icon.png
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario directory-tree-is-the-package-renamed` builds the tree into an empty scratch directory with `node scripts/directory_tree.js`. It requires the tree's file set to equal the paths in `npm pack --dry-run --json` plus `.claude-plugin/plugin.json` and `.claude-plugin/icon.png`. It requires the tree manifest to equal the root manifest except for `name`, which is `keel-openspec`. It requires every `skills`, `agents`, and hook script path in that manifest to resolve to a file inside the tree, and the icon to be a PNG whose IHDR gives equal sides between 512 and 2048 px and that is under 2 MB. It requires the repository's root manifest to still name `keel`, and a second build into the now non-empty directory to exit non-zero. Fails with: `directory-tree-is-the-package-renamed:`
    - M2: on this machine, `claude plugin validate <tree>` on a tree built by `node scripts/directory_tree.js` reports the manifest valid.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3edb20a0d27662c0e4ad17f6f17b268966174259b6df670078c9dcb111bf1faf
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario directory-tree-is-the-package-renamed` reports `directory-tree-is-the-package-renamed scenario passed.` The tree built into an empty scratch directory holds exactly the `npm pack --dry-run --json` paths plus `.claude-plugin/plugin.json` and `.claude-plugin/icon.png`. Its manifest equals the root manifest except `name: keel-openspec`. Every skill, agent, and hook script path in it resolves inside the tree, and the icon's IHDR reads 1024×1024 at 8,733 bytes. The repository's root manifest still names `keel`, and a second build into the non-empty directory exits non-zero.
    - M1.red: fail. Before the script existed, the scenario reported `directory-tree-is-the-package-renamed: scripts/directory_tree.js does not exist.`, which carries the declared signature `directory-tree-is-the-package-renamed:`.
    - M1.green: pass. The same scenario passes with `scripts/directory_tree.js`. It runs `npm pack --json` into a temporary directory, extracts `package/`, writes the renamed manifest, and copies `assets/directory/icon.png`.
    - M2: pass. On this machine, a tree built by `node scripts/directory_tree.js` (69 files) passes `claude plugin validate <tree>` (Claude Code 2.1.283) with `✔ Validation passed`.
    - M2.red: fail. It was taken after implementation, by moving `scripts/directory_tree.js` aside and running the same two commands. The build failed with `Error: Cannot find module '…/scripts/directory_tree.js'`, and `claude plugin validate` on the absent tree printed `✘ Validation failed`. The script was restored and checked present afterwards.
    - M2.green: pass. With the script in place, the same commands give a 69-file tree and `✔ Validation passed`.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: M1 builds through the public script and compares against npm's own file list rather than a list the test restates, so the tree is the package by construction. The rename is checked as the only difference from the root manifest, and M2 runs the host's own manifest validator on the result. The icon check uses the same bounds the portal states: square, 512 to 2048 px, under 2 MB.
      - Scope check: `git status --short` shows `scripts/directory_tree.js` and `assets/directory/icon.png` (new) and `scripts/validate_plugin.py`, this task's Touch, plus this change's own directory. `the-tarball-is-the-repository` now counts 67 packed files, because the icon and the script are both under npm `files`.
      - Findings: none

- [ ] 1.2 `scripts/directory_branch.js` advances `claude-directory`, and the release job runs it in place of the pinned entry
  - Covers:
    - keel-native-plugin-package / Each release updates the directory branch / Each release advances the directory branch
    - keel-native-plugin-package / Each release updates the directory branch / The release notes name the branch commit
    - D2
    - D3
    - F1
  - Read:
    - .github/workflows/publish.yml
    - scripts/official_entry.js
  - Touch:
    - scripts/directory_branch.js
    - scripts/official_entry.js
    - .github/workflows/publish.yml
    - scripts/validate_plugin.py
    - README.md
    - README.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario directory-branch-advances` clones this repository into a scratch directory whose `origin` is a scratch bare repository. It runs `node <repo>/scripts/directory_branch.js 9.9.9 <40-hex>` there. It requires origin's `claude-directory` to exist with one commit whose message names `9.9.9` and the sha, whose tree's `.claude-plugin/plugin.json` names `keel-openspec`, and whose file list equals a `directory_tree.js` build. It requires the script to print that commit. It requires a second run with the same inputs to leave origin's branch at the same commit, and a run after a planted change to the package add exactly one commit. Fails with: `directory-branch-advances:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario release-notes-name-the-directory-branch` reads the release step in `.github/workflows/publish.yml`. It requires the step to run `node scripts/directory_branch.js "$VERSION" "$SHA"`, to write notes naming `keel-openspec`, `claude-directory`, and the printed commit, and to no longer reference `official_entry.js`, which no longer exists. Fails with: `release-notes-name-the-directory-branch:`
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if pushing a branch from the release job would need a permission or secret the workflow does not already have, because granting one is the owner's decision.
  - Evidence:
    - Contract: `todo`
    - Blocker: none
    - Reauthorizations: none

## 2. Release, and the owner submits

- [ ] 2.1 Release 5.90.0 with the change promoted
  - Covers:
    - E1
    - E2
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
    - M1: `node scripts/bump_version.js minor` moves every marker to 5.90.0, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.90.0 section written into the stub.
    - M2: the delta is promoted, `node node_modules/.bin/openspec validate directory-branch --strict` passes, and `npm test` reports no failing scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: `todo`
    - Blocker: none
    - Reauthorizations: none

- [ ] 2.2 The release job creates `claude-directory`, and the portal validates it as keel-openspec
  - Covers:
    - E1
    - E2
  - Read:
    - .github/workflows/publish.yml
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - Reason: this observes what the real release job and the real portal did with 5.90.0. Neither can run before the release, so there is no red.
    - M1: after 5.90.0 lands, `git ls-remote origin claude-directory` names a commit. That commit's `.claude-plugin/plugin.json` names `keel-openspec` at 5.90.0, and the v5.90.0 release notes name that commit.
    - M2: the portal's Validate on `TanglmChris/keel` at branch `claude-directory` passes with no "Name matches a known brand" hold, scans every file, and finds the icon. Submitting is done only after the owner confirms the filled-in submission.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop before the portal's final submit, and ask the owner to confirm what it will publish.
  - Evidence:
    - Contract: `todo`
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario once 1.1 and 1.2 have registered theirs.

## Change Evidence

- C1: `todo`

## Invalidates

- I1: "Each release's notes also carry the entry Anthropic's official plugin directory would list for it, pinned to the commit the release tag points at" — `README.md`, and "每个版本的 release notes 里还附有 Anthropic 官方插件目录对应的条目，锁定到该版本 tag 指向的 commit" — `README.zh-CN.md`. Updated by: 1.2
- I2: "a `url` source naming the Keel repository pinned to that commit" — the requirement "Each release states its official directory entry" in `openspec/specs/keel-native-plugin-package/spec.md`, removed. Updated by: 2.1
- I3: "The directory pins every third-party plugin to a commit of its git repository" — `scripts/official_entry.js`, which is deleted. Updated by: 1.2
- I4: "Every third-party entry there is pinned by `sha`" and "Submit … The owner submits, using the entry from the latest release's notes" — the body of https://github.com/TanglmChris/keel/issues/175. Durable owner: https://github.com/TanglmChris/keel/issues/175#issuecomment-5969374155, which records the portal and the branch tracking.

## Expectation Coverage

- E1: Anthropic's directory sees a plugin named `keel-openspec`, with an icon, small enough to be scanned whole, while npm, the repository name, and `keel@keel-marketplace` installs are unchanged. Covered by: 1.1, 2.1, 2.2
- E2: Each release refreshes what the directory tracks without the owner acting, and only the owner submits. Covered by: 1.2, 2.1, 2.2
