# Tasks

## 1. A hand-over starts the new session on the owner's default model

- [x] 1.1 Resolve the model, pass it, record it, and declare it
  - Covers:
    - keel-shift-change / A CLI hand-over starts the new session on the owner's default model / A hand-over passes the model the owner would get
    - keel-shift-change / A CLI hand-over starts the new session on the owner's default model / The host's own order decides between sources
    - keel-shift-change / A CLI hand-over starts the new session on the owner's default model / A declaration wins over every default
    - keel-shift-change / A CLI hand-over starts the new session on the owner's default model / Nothing to name passes nothing
    - keel-shift-change / A CLI hand-over starts the new session on the owner's default model / An unreadable declaration is named and ignored
    - D1
    - D2
    - D3
    - D4
    - D5
    - D6
  - Read:
    - openspec/changes/shift-keeps-default-model/design.md
    - src/core/config.js
    - src/core/shift.js
    - scripts/validation/shift.py
    - docs/cli-team.md
  - Touch:
    - src/core/config.js
    - src/core/shift.js
    - scripts/validation/common.py
    - scripts/validation/shift.py
    - scripts/validation/registry.py
    - keel/config.yaml
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
    - docs/host-contract.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-handover-passes-default-model`: with the fake `claude` of `shift-cli-self-shift`, a scratch `HOME` and no `CLAUDE_CONFIG_DIR`, a pending hand-off over a user `settings.json` naming `opus` makes the real hand-over start `--bg -n "verify · <MM-DD HH:MM>" --permission-mode auto --model opus <prompt>`, records `model: opus` and a user-settings source on the delivered entry, and `keel shift status` prints both; then adding in turn the worktree's `.claude/settings.json` (`sonnet`), its `.claude/settings.local.json` (`haiku`) and `ANTHROPIC_MODEL=fable` changes the passed model to each in turn. Fails with: `shift-cli-handover-passes-default-model:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-declared-model-wins`: `shift: model: sonnet` and `shift: effort: high` declared over settings and `ANTHROPIC_MODEL` naming other models make the call carry `--model sonnet --effort high` after `--permission-mode auto`; `effort: extreme` is not passed and `keel shift status` names `extreme` and the five accepted levels. Fails with: `shift-cli-declared-model-wins:`
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-handover-names-no-model-when-none`: with no source, and then with only an invalid-JSON user `settings.json`, the call carries neither `--model` nor `--effort` and the hand-off is delivered, and a user `settings.json` naming a non-string `model` names nothing, an empty `model` names nothing.
    - M4 (regression): run one at a time, each passes: `--scenario shift-cli-self-shift`, `--scenario assertion-shape-count`, `--scenario surfaces-agree-with-code`, and `node scripts/run_python.js scripts/validate_plugin.py --group shift --jobs 4`.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4dd154cb6f9eb225ff442fb62741b93184f5214243f76181de794330d1b545f3 (keel 5.215.0)
    - M1: pass. `shift-cli-handover-passes-default-model scenario passed.` (exit 0). Four hand-overs through the real `keel tick` and the fake `claude`: user settings `opus`, then adding project settings `sonnet`, project-local `haiku`, `ANTHROPIC_MODEL=fable`, the start call is `--permission-mode auto --model <that model>` before the prompt, the entry records the model and its source, and `keel shift status` shows both.
    - M1.red: fail. Before any code change, exit 1: `shift-cli-handover-passes-default-model: with ['user'] the start call is ['--bg', '-n', 'verify · 11-03 11:09', '--permission-mode', 'auto', 'verify: your new shift starts now. Run keel context, then keel shift resume.'], not `--permission-mode auto --model opus` before the prompt.`
    - M1.green: pass. `resolveShiftModel` in `src/core/shift.js` takes the first source naming a model in the host's order (D1) and the start call inserts `--model` after `--permission-mode` (D2); the delivered entry records `model` and `model_source` and `describeHandOff` prints them (D5).
    - M2: pass. `shift-cli-declared-model-wins scenario passed.` (exit 0). `shift: model: sonnet` and `effort: high` over settings and `ANTHROPIC_MODEL` naming other models give `--model sonnet --effort high`, recorded as `declared`; `effort: extreme` is not passed, the model still is, and `keel shift status` names `extreme` and `low, medium, high, xhigh, max`.
    - M2.red: fail. Before any code change, exit 1: `shift-cli-declared-model-wins: the declaration did not win: ['--bg', '-n', 'verify · 11-03 11:09', '--permission-mode', 'auto', 'verify: your new shift starts now. Run keel context, then keel shift resume.']`
    - M2.green: pass. `readShiftDeclaration` in `src/core/config.js` returns `model` and `effort` and a `message` for an unreadable value (D3, D4), which `deliver` puts on the entry's notice for `keel shift status`.
    - M3: pass. `shift-cli-handover-names-no-model-when-none scenario passed.` (exit 0). No source, invalid JSON, a non-string `model` and an empty `model` each deliver the hand-off with neither `--model` nor `--effort` and no `model` on the entry. It also passed before the code change, which is why it is tagged (regression) and owes no red.
    - M4: pass. Run one at a time, each exit 0: `shift-cli-self-shift scenario passed.`, `assertion-shape-count scenario passed: 74 sites, a bound on a shape and not a count of defects.` (the three new `or` conditions were split so each failure has its own message, instead of raising the bound), `surfaces-agree-with-code scenario passed.`, and `validation --group shift passed: 73 scenarios.`. Also measured on this machine with the real settings: the same resolution code returns `{"model":"opus","source":"user settings"}`.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel tick` hand-over and `keel shift status`, a hand-over started with no declaration names the model the owner's own settings name, in the host's order, and a declaration wins (M1, M2); with nothing to name it names nothing and still delivers (M3); the existing hand-over behavior is unchanged (M4).
      - Scope check: `git status --short` lists `src/core/config.js`, `src/core/shift.js`, `scripts/validation/shift.py`, `scripts/validation/registry.py`, `keel/config.yaml`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md`, `docs/host-contract.md`, and this change's directory, all in Touch. `scripts/validation/common.py` is in Touch and unchanged.
      - Findings: Discard reason: managed policy settings are deliberately not read (D1) — they are not a file Keel can find on every host, and a machine whose managed settings name a model is not known to exist; `docs/cli-team.md` states the limit. Resolved here: M1 and M3 — two `or` conditions in the new scenarios that reported "not delivered" for a missing start call as well were split so each failure names its own cause.
    - Blocker: none
    - Reauthorizations: M3 was tagged (regression) and the contract re-recorded before any implementation, because its assertion already held on the unchanged code; `docs/host-contract.md` was added to Touch and the contract re-recorded again for the same reason, with no evidence yet recorded under either earlier contract.

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
    - scripts/validation/common.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-shift-change/spec.md
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
    - Reason: this task changes only version markers, a changelog entry, and the spec promotion. Task 1.1 proves the behavior, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:92de825057c51da9b275085db3e4d10129e044ad0d24b25f57cc3ece4cfa8750 (keel 5.215.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.215.0 → 5.216.0. With the section "A shift change does not change the default model" written into the stub, `version-alignment scenario passed.` (exit 0).
    - M2: the added requirement is appended to `openspec/specs/keel-shift-change/spec.md`, and `published-specs-validate-strictly scenario passed: 34 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - M3: pass. `npm test`: `validation --all passed: baseline plus 360 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: the release carries task 1.1's behavior, the markers agree at 5.216.0, the promoted spec validates strictly, and the full suite passes.
      - Scope check: `git status --short` lists the bumped markers, `keel/CHANGELOG.md`, the published spec, task 1.1's files, and this change's directory, all in Touch of 1.1 or 2.1.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "claude --bg -n \"<role> · <MM-DD HH:MM>\" --permission-mode <mode>" — the start call as `docs/cli-team.md`, `docs/cli-team.zh-CN.md` and `docs/host-contract.md` state it, without a model. Updated by: 1.1.
- I4: "start a new session with `claude --bg -n \"<role> · <MM-DD HH:MM>\" --permission-mode <mode>`" — the requirement "A CLI session changes its own shift and the next one is named for its start" in `openspec/specs/keel-shift-change/spec.md`. Discard reason: it stays true as the start of the call; the added requirement "A CLI hand-over starts the new session on the owner's default model" states what follows `--permission-mode`.
- I2: "Mode comes from `keel/config.yaml`, and is `auto` when nothing is declared" — `docs/cli-team.md` and `docs/cli-team.zh-CN.md`, which list the `shift:` keys without `model` and `effort`. Updated by: 1.1.
- I3: "# This repository declares none." — `keel/config.yaml`, the `shift:` comment, which lists two keys. Updated by: 1.1.

## Expectation Coverage

- E1: A shift change does not change the default model: the new session is started on the model the owner's own settings name, unless `shift: model:` says otherwise (D1–D6) (#500). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
