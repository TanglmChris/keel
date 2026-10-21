# Tasks

## 1. Name, and on request adopt, the sessions on an older plugin

- [ ] 1.1 Add `keel --update --adopt` and the `claude sessions` line
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
    - M1:
    - M1.red:
    - M1.green:
    - M2:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [ ] 2.1 Release and promote the spec
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
    - Contract:
    - M1:
    - M2:
    - M3:
    - Review:
      - Status:
      - Acceptance check:
      - Scope check:
      - Findings:
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "| Skills | Stay at the loaded version until `/reload-plugins` or a new session." — `docs/updating.md`, which does not say a CLI hand-over starts that new session or that `--adopt` restarts idle ones. Updated by: 1.1.
- I2: "keel --update [--dry-run] [--source <npm package or git spec>]" — the Commands block of both READMEs, and the `keel --help` usage line, which gain `--adopt`. Updated by: 1.1.

## Expectation Coverage

- E1: A release reaches running background sessions without a `/reload-plugins` in each: a CLI hand-over already adopts it, and `keel --update --adopt` restarts the idle sessions on an older plugin without interrupting a busy one, a guarded one, or itself (#424; D1–D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
