# Tasks

## 1. Name, and on request adopt, the sessions on an older plugin

- [x] 1.1 Add `keel --update --adopt` and the `claude sessions` line
  - Covers:
    - keel-native-plugin-package / An update names the sessions on an older plugin and adopts the idle ones on request / Adopting restarts only the idle sessions on the older plugin
    - keel-native-plugin-package / An update names the sessions on an older plugin and adopts the idle ones on request / Without adopting, the older sessions are only named
    - D1
    - D2
    - D3
    - D4
  - Read:
    - openspec/changes/update-adopt/design.md
    - bin/keel.js
  - Touch:
    - bin/keel.js
    - docs/updating.md
    - README.md
    - README.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-adopts-idle-sessions`: with a fake claude whose `plugin list --json` carries `lastUpdated` and whose `agents --json` lists an idle, a busy, and a guarded background session started before it, an idle one started after it, and the session named by `CLAUDE_CODE_SESSION_ID`, `keel --update --adopt` stops only the idle older session, resumes it with exactly `--bg --resume <its session id>` after its process has exited, prints a `claude sessions` line naming it adopted and the busy and guarded ones left, and exits 0; `keel --update` without `--adopt` stops and resumes nothing and prints a line naming the older sessions and `keel --update --adopt`; `--adopt` outside `--update` is refused with exit 2. Fails with: `update-adopts-idle-sessions:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario update-covers-installed-hosts`, `--scenario update-codex-from-disk`, `--scenario readme-states-the-cli`, `--scenario readme-zh-matches-english`, and the baseline pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:059be25e9badf3221ac4a7420524d35b111b43adc942c1c959a4ed9104994222 (keel 5.178.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario update-adopts-idle-sessions` reports `update-adopts-idle-sessions scenario passed.` (exit 0), also after merging 5.179.0 (#421) into the branch.
      - `--adopt` stopped only `aaaaaaaa`, then resumed it with exactly `--bg --resume aaaaaaaa-0000-0000-0000-000000000001` in its worktree, after its process had exited.
      - The line names it adopted, and names the busy and guarded sessions left. It does not name the fresh session or the command's own session.
      - Without `--adopt`, nothing was stopped or resumed, and the line names the three older sessions and `keel --update --adopt`.
      - `keel --adopt` exits 2.
    - M1.red: fail. Before the change: `update-adopts-idle-sessions: keel --update --adopt exited 2: '' 'keel: unknown option: --adopt'` (exit 1).
    - M1.green: pass. After these changes:
      - `--adopt` is parsed and refused outside `--update`.
      - `claudeKeel` returns `lastUpdated`.
      - `adoptClaudeSessions` runs after the Claude plugin step. It waits on the pid with `waitForExit`, then resumes in the row's `cwd`.

      The scenario's own first run was wrong: a killed `sleep` it spawned stayed a zombie, which still answers `kill(pid, 0)`. The sleepers are now started through `sh -c '… &'`, so they are reparented, like a real host process.
    - M2: pass. `update-registry-lag`, `update-covers-installed-hosts`, `update-codex-from-disk`, `update-host-query-timeout`, `readme-states-the-cli`, `readme-zh-matches-english`, `config-documents-in-declaration-order`, and `assertion-shape-count` (74) each pass, and the baseline exits 0.
      - Live: this tree's `node bin/keel.js --update` without `--adopt` printed `claude sessions: manual - 5 started before the plugin was installed …`. It named kaiwu-flow, kaiwu-pm-iecc, kaiwu-design-iecc, kaiwu-spec-iecc, and keel-maint-2, stopped nothing, and left out this session.
    - Review:
      - Status: pass
      - Acceptance check: E1 is met for both paths.
        - The hand-over path is proven by the transcripts' `skill_listing` (F1).
        - The restart is measured on the probe (F2).
        - The real `keel --update` path is exercised end to end with a stub claude, and the naming line was seen live.
        - Busy, guarded, and own sessions are left, and the resume keeps the id. The chat role, note, and read cursors live in Keel's store and are untouched by a restart.
      - Scope check: `git diff origin/main --stat` lists `bin/keel.js`, `docs/updating.md`, both READMEs, `scripts/validate_plugin.py`, and this change's directory. Merging #421's release took no file outside them.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E2
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-native-plugin-package`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:01bd0a5f60264f78f58f5ec8f27ce6d085e1585b48bdc262f5196b487abeca9a (keel 5.179.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.179.0 → 5.180.0, after merging 5.179.0 into the branch. With the section "keel --update --adopt restarts the idle sessions still on an older plugin" written, `version-alignment scenario passed.` (exit 0).
    - M2: the added requirement "An update names the sessions on an older plugin and adopts the idle ones on request" is promoted into `keel-native-plugin-package`. `published-specs-validate-strictly scenario passed: 33 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test` on commit 46491482 (clean tree), started 09:04 at load 6: `validation --all passed: baseline plus 301 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2. The markers, the 5.180.0 section, and the published spec carry the change, and the full suite passes on the committed tree.
      - Scope check: beyond task 1.1, the files are the version markers, `keel/CHANGELOG.md`, and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "| Skills | Stay at the loaded version until `/reload-plugins` or a new session." — `docs/updating.md`, which does not say a CLI hand-over starts that new session or that `--adopt` restarts idle ones. Updated by: 1.1.
- I2: "keel --update [--dry-run] [--source <npm package or git spec>]" — the Commands block of both READMEs, and the `keel --help` usage line, which gain `--adopt`. Updated by: 1.1.

## Expectation Coverage

- E1: A release reaches running background sessions without a `/reload-plugins` in each: a CLI hand-over already adopts it, and `keel --update --adopt` restarts the idle sessions on an older plugin without interrupting a busy one, a guarded one, or itself (#424; D1–D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
