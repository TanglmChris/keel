# Tasks

## 1. Remove the old shift's session by default

- [x] 1.1 Default `keep_old_sessions` to 0 and document `shift:`
  - Covers:
    - keel-shift-change / A CLI session changes its own shift and the next one is named for its start / By default the old shift leaves the session list
    - keel-shift-change / A CLI session changes its own shift and the next one is named for its start / The waker hands a CLI shift over once the old session is idle
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/shift-rm-old/design.md
    - src/core/shift.js
    - src/core/config.js
  - Touch:
    - src/core/config.js
    - src/core/shift.js
    - keel/config.yaml
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-keeps-old-sessions`: with no `shift:` declaration, and with the unreadable `keep_old_sessions: many`, a hand-over removes the session just handed over and the three older stopped sessions of verify's that have transcripts, each only after Keel's store holds its copy, and `keel shift status` names `keel shift history verify --show` for the old session; `keep_old_sessions: 2` still keeps the two newest. Fails with: `the default keeps the wrong number of old sessions`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift`: `ready --wake` in a CLI session with nothing kept says the old session is removed and names `keel shift history verify --show`, and the delivered hand-off still stops the old session before starting the new one.
    - M3: `node scripts/run_python.js scripts/validate_plugin.py --scenario config-documents-in-declaration-order` and `--scenario a-count-is-derived-from-what-it-counts` pass with `shift` in `CONFIG_DECLARATIONS` and its block in `keel/config.yaml`, and `docs-zh-match-english` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:7e53e8a39f9e72de066fe79622510172bcdd4f05e2733c65dc336f8f4abc9923 (keel 5.177.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-keeps-old-sessions` reports `shift-cli-keeps-old-sessions scenario passed.` (exit 0). With no declaration and with `many`, the hand-over removes `01010101`, `02020202`, `04040404`, and the shift just handed over, each after Keel's copy exists. Status names `keel shift history verify --show 5b14fbae`, and `keep_old_sessions: 2` still keeps two.
    - M1.red: fail. Before the change: `shift-cli-keeps-old-sessions: the default keeps the wrong number of old sessions (keep_old_sessions None): removed ['01010101']` (exit 1).
    - M1.green: pass. With `keepOldSessions` defaulting to 0 in `readShiftDeclaration`, the scenario passed.
    - M2: pass. `shift-cli-self-shift scenario passed.` (exit 0).
    - M2.red: fail. Before the change, `shift-cli-self-shift: ready --wake in a CLI session does not say how the old session is read once removed: 'Stored the shift note for verify at …'` (exit 1).
    - M2.green: pass. `clearHint` reads the declaration, and with nothing kept says the waiter removes the session once Keel holds the transcript, which `keel shift history <role> --show <id>` prints. With a number declared, it keeps the `claude attach` sentence.
    - M3: pass. `config-documents-in-declaration-order`, `a-count-is-derived-from-what-it-counts`, `docs-zh-match-english`, and `continuation-docs` each report `scenario passed.` Every other `shift-*` scenario and the baseline also pass.
    - M3.red: fail. With `shift` added to `CONFIG_DECLARATIONS` and no block yet: `config-documents-in-declaration-order: keel/config.yaml documents […, 'patrol', 'owner_language'], not […, 'patrol', 'shift', 'owner_language'] in that order.` and `a-count-is-derived-from-what-it-counts: keel/config.yaml's header does not name 'shift'`.
    - M3.green: pass. `keel/config.yaml` now has the `# shift (optional):` block after `patrol`, and its header names thirteen declarations including `shift`. The `docs/cli-team` pages in both languages state the 0 default.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel shift ready --wake` and `keel tick` with a stub claude, the old shift leaves the list by default, and only after Keel holds its transcript; status and the ready message name how to read it.
      - Scope check: the probes (F1, F2) measured the host side.
        - The owner's observation: a removed session no longer appears.
        - `claude rm` of a session started without `-w` left `probe-418-stop` in place.
        - `git status --short` lists only Touch files and this change's directory.
      - Findings: none.
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
    - openspec/specs/keel-shift-change/spec.md
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
    - M2: the delta is promoted into `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:72a6b3d3421d0d4b42bad60f70169eab4aa860a5ef73d2d155d050dc029fc7ca (keel 5.177.0)
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

- I1: "(default 3)" and "3 apply" — `keel-shift-change` and `src/core/config.js`. Updated by: 1.1, 2.1.
- I2: "keep_old_sessions: 3    # old shifts left in `claude agents` per role" and "(3 when nothing is declared; 0 keeps none)" — `docs/cli-team.md` and `docs/cli-team.zh-CN.md`. Updated by: 1.1.
- I3: "its conversation is kept, `claude attach <id>` reopens it" — the `ready --wake` message in `src/core/shift.js`. Updated by: 1.1.
- I4: "Twelve independent declarations live here" — `keel/config.yaml`. Updated by: 1.1.

## Expectation Coverage

- E1: After a hand-over the old shift no longer appears in the session list, its transcript is still readable, and `shift:` is documented (#418; D1, D2, D3). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
