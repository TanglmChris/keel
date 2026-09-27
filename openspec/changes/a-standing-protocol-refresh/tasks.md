# Tasks

## 1. The refresh and its authorization

- [x] 1.1 `authorize:` accepts `protocol-refresh`, and `keel context` names the refresh of an older managed protocol with its authorization state
  - Covers:
    - keel-standing-authorization / A protocol-refresh authorization covers refreshing an older managed protocol / The name is accepted and reported
    - keel-standing-authorization / A protocol-refresh authorization covers refreshing an older managed protocol / Other names stay unauthorized
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary / A declared action is authorized for the whole repository
    - keel-stateless-continuity / Context names the refresh of an older managed protocol / An older protocol names its refresh
    - keel-stateless-continuity / Context names the refresh of an older managed protocol / A declared authorization is reported on the line
    - keel-stateless-continuity / Context names the refresh of an older managed protocol / A write guard defers the refresh
    - keel-stateless-continuity / Context names the refresh of an older managed protocol / An aligned or newer protocol says nothing
    - keel-stateless-continuity / Context names the refresh of an older managed protocol / The target follows the installed surface
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
    - F3
    - F6
  - Read:
    - src/core/config.js
    - src/core/context.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/config.js
    - src/core/context.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `context-names-the-protocol-refresh` scenario installs a Claude-target scratch repository, restamps its managed block `5.0.0`, and requires `keel context` to print exactly one `Protocol:` line naming `5.0.0`, the running Keel, `keel --install --target claude`, and asking before running it. It also requires `keel context --json` to carry `protocol.stamped == "5.0.0"`. Fails with: `printed no Protocol line`
    - M2: the same scenario declares `authorize: [protocol-refresh]`, and requires the line to say standing-authorized, `keel --doctor` to report `protocol-refresh: authorized`, and `commit: not authorized`. Fails with: `did not read protocol-refresh as authorized`
    - M3: the same scenario plants `keel/guard.json` with the authorization declared, and requires the line to say the refresh is deferred while a write guard is active. Fails with: `not deferred while a write guard`
    - M4: the same scenario restamps the block `99.0.0`, and separately runs context in Keel's own source repository, requiring no `Protocol:` line and no `protocol` JSON field in both. Fails with: `offered a refresh for a protocol that is not older`
    - M5: the same scenario installs a Codex-target scratch repository with an older stamp, and requires the command to be `keel --install --target codex`. Fails with: `named the wrong target`
    - M6 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if reporting the refresh would change `status`, `nextAction`, or selection for any existing context scenario, because the report is advisory.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2528bc1d15d6ac4ba81c7f898348d4f5f66de1c8ef0d1b496d55c25b965f5271
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario context-names-the-protocol-refresh` reports the scenario passing. A Claude-target scratch repository restamped `5.0.0` gets exactly one line: `Protocol: AGENTS.md is stamped 5.0.0, older than Keel 5.75.0; refresh with \`keel --install --target claude\` — ask before running it; keel/config.yaml does not standing-authorize protocol-refresh`. `keel context --json` carries `protocol.stamped == "5.0.0"`.
    - M1.red: fail, for the declared reason. Calling the check's helper alone before any change reported `M1 context printed no Protocol line for a 5.0.0 stamp under Keel 5.75.0: []`. Carries the declared signature `printed no Protocol line`.
    - M1.green: pass. Same helper after `stampedProtocol()`, `installedTarget()`, `protocolRefresh()`, and `renderProtocol()` were added to `src/core/context.js`, with `context.protocol` set only when a refresh applies.
    - M2: pass. Same scenario. With `authorize: [protocol-refresh]` the line reads `— standing-authorized (authorize: protocol-refresh); run it before other work and leave the diff for the owner to commit`, and `keel --doctor` reports `protocol-refresh: authorized` beside `commit: not authorized`.
    - M2.red: fail, for the declared reason. `M2 context did not read protocol-refresh as authorized: []`. Carries the declared signature `did not read protocol-refresh as authorized`.
    - M2.green: pass. Same helper after `protocol-refresh` joined `STANDING_AUTHORIZATION_ACTIONS` in `src/core/config.js`. Doctor's authorization list needed no change, because it iterates that array (F3). The line reads `authorization.scopes`.
    - M3: pass. Same scenario. With `keel/guard.json` planted and the authorization declared, the line reads `— deferred while a task's write guard is active, because the refresh writes outside the task's Touch`.
    - M3.red: fail, for the declared reason. `M3 the refresh was not deferred while a write guard is active: []`. Carries the declared signature `not deferred while a write guard`.
    - M3.green: pass. Same helper after `protocolRefresh()` set `deferred` from `keel/guard.json`, which `renderProtocol()` checks first.
    - M4: pass. Same scenario. A `99.0.0` stamp, and Keel's own source repository, each produce no `Protocol:` line and no `protocol` JSON field.
    - M4.red: fail, for the declared reason. With the first slice comparing `stamped.version === running`, the helper reported `M4 context offered a refresh for a protocol that is not older (a 99.0.0 stamp): ['Protocol: AGENTS.md is stamped 99.0.0, older than Keel 5.75.0; …']`. That is a newer stamp called older. Carries the declared signature `offered a refresh for a protocol that is not older`.
    - M4.green: pass. Same helper after `olderThan()` compares `X.Y.Z` numerically and only a strictly older stamp yields a report.
    - M5: pass. Same scenario. A Codex-target scratch repository restamped `5.0.0` gets `keel --install --target codex`.
    - M5.red: fail, for the declared reason. `M5 context named the wrong target for a Codex repository: ['Protocol: … refresh with \`keel --install --target claude\` …']`. Carries the declared signature `named the wrong target`. The red also exposed D3's premise as wrong: a Codex install writes no `.codex/` surface (F6). That was the reauthorization below.
    - M5.green: pass. Same helper after `installedTarget()` returns `claude` for the managed Claude import, `opencode` for `.opencode/commands`, and `codex` otherwise.
    - M6: pass. `npm test` reports `validation --all passed: baseline plus 187 scenarios, 1 skipped: output-survives-the-pipe.` The Stop Rule held: no existing context scenario changed `status`, `nextAction`, or selection. The report is one more line and one optional JSON field.
    - Review:
      - Status: pass
      - Acceptance check: each check runs the real `keel context`, `--json`, or `--doctor` against a repository the real installer wrote, then restamped. M1–M3 and M5 were red before any code existed. M4 was red against the first slice's equality test, the plausible shortcut it guards against. The reds were measured before the reauthorization, and none of the check texts changed in it, only D3 and F6.
      - Scope check: `git status --short` shows `src/core/config.js`, `src/core/context.js`, and `scripts/validate_plugin.py`, this task's Touch, plus this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: 2026-09-27 — D3 corrected and F6 added. A Codex-target install writes no `.codex/` surface into the repository, so the target is `codex` when neither the Claude import nor `.opencode/commands` is present. Measured by M5's first red, which named `--target claude` for a Codex repository. The evidence gathered so far is kept and re-measured after the fingerprint moved.

- [x] 1.2 The protocol, the bootstrap, and the vocabulary's documentation carry `protocol-refresh`
  - Covers:
    - D6
    - F5
    - E2
  - Read:
    - AGENTS.md
    - assets/bootstrap/AGENTS.md
    - README.md
    - keel/config.yaml
    - scripts/validate_plugin.py
  - Touch:
    - AGENTS.md
    - README.md
    - keel/config.yaml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `continuation-docs` requires the README vocabulary comment and `keel/config.yaml`'s comment to name all seven names, including `protocol-refresh`, and requires a README paragraph for it. Fails with: `lacks: protocol-refresh`
    - M2: a new cell in `continuation-docs` requires `AGENTS.md` `## Session Start` to state the rule: run the named refresh under `protocol-refresh`, never while a write guard is active, and leave the diff uncommitted. It also requires the bootstrap to keep `Start every session with \`keel context\``, the sentence through which the `Protocol:` line reaches a consumer. Fails with: `does not carry the protocol-refresh rule`
    - M3 (regression): `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the bootstrap must grow past a size bound a scenario enforces, because the bootstrap is resident in every consumer session.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0191ccb7b63b685245d13996e61cdd68f3611603b90d34f637f87ecbbd5c17fa
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario continuation-docs` reports the scenario passing. `README.md`'s example reads `accepted names: commit, push, release, archive, continuation, issue:<owner>/<repo>, protocol-refresh`, says `The seven names above are the whole vocabulary.`, and has a `` `protocol-refresh`, the seventh name `` paragraph. `keel/config.yaml`'s comment names the seven-name vocabulary and says what `protocol-refresh` covers.
    - M1.red: fail, for the declared reason. `continuation-docs: README.md lacks: protocol-refresh, as 'accepted names: commit, push, release, archive, continuation, issue:<owner>/<repo>, protocol-refresh'`. Carries the declared signature `lacks: protocol-refresh`.
    - M1.green: pass. After the README example, the count, the new paragraph, and the config comment were written, the same command moved past every M1 needle and stopped at M2.
    - M2: pass. Same command. `AGENTS.md` `## Session Start` carries the rule: run the named refresh only under `protocol-refresh`, before other work, never while a task's write guard is active, report it, and leave the diff uncommitted; without the authorization, ask. The bootstrap still opens with `Start every session with \`keel context\``.
    - M2.red: fail, for the declared reason. `continuation-docs: AGENTS.md Session Start does not carry the protocol-refresh rule; it lacks '\`protocol-refresh\`'.` Carries the declared signature `does not carry the protocol-refresh rule`.
    - M2.green: pass. Same command after the Session Start bullet was added.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 187 scenarios, 1 skipped: output-survives-the-pipe.` The bootstrap is unchanged at 1325 bytes, under its 1400-byte budget.
    - Review:
      - Status: pass
      - Acceptance check: all four surfaces that spell out the vocabulary now spell all seven names: the README example, the README count, `keel/config.yaml`, and the code in 1.1. The old six-name needles were replaced rather than kept beside the new ones, so a stale list cannot pass. The rule lives where an agent reads it: `AGENTS.md` for this repository, and the `Protocol:` line itself for a consumer whose bootstrap has no room. That keeps the budget comment's argument intact.
      - Scope check: `git status --short` shows `AGENTS.md`, `README.md`, `keel/config.yaml`, and `scripts/validate_plugin.py`, this task's reauthorized Touch, plus this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: 2026-09-27 — M2 no longer requires the rule in `assets/bootstrap/AGENTS.md`, and the bootstrap left Touch. The bootstrap block is 1325 bytes against a 1400-byte `BOOTSTRAP_BLOCK_BYTE_BUDGET`, whose comment rejects compressing other bullets to make room. A consumer is already served: the bootstrap opens with `Start every session with \`keel context\``, and 1.1's `Protocol:` line states in each of its three states what to do. That is how `full_mode_paths` routing reaches consumers. The Stop Rule was reached as a question and not triggered, because the budget does not move. No evidence had been recorded.

## 2. Close

- [ ] 2.1 Release
  - Covers:
    - E1
  - Read:
    - keel/CHANGELOG.md
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-standing-authorization/spec.md
    - openspec/specs/keel-stateless-continuity/spec.md
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
    - M2: both deltas are promoted, `node node_modules/.bin/openspec validate a-standing-protocol-refresh --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: pending
    - M1: pending
    - M2: pending
    - Review: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "accepted names: commit, push, release, archive, continuation, issue:<owner>/<repo>" — the
  `authorize:` example in `README.md`, and "The six names above are the whole vocabulary." beside it.
  Updated by: 1.2
- I2: "continuation, issue:<owner>/<repo> — and an unrecognized entry is reported" — the vocabulary
  comment in `keel/config.yaml`.
  Updated by: 1.2
- I3: "The accepted action names MUST be a closed set — `commit`, `push`, `release`, `archive`,
  `continuation`, `issue`" — `openspec/specs/keel-standing-authorization/spec.md`.
  Updated by: 2.1
- I4: `STANDING_AUTHORIZATION_ACTIONS = ("commit", "push", "release", "archive", "continuation",)` —
  `scripts/validate_plugin.py`, the suite's copy of the vocabulary.
  Updated by: 1.1
- I5: "Still open on #164: a standing authorization for the agent to refresh the managed protocol
  block." — the 5.75.0 entry in `keel/CHANGELOG.md`. History, left as written; the new entry records
  that it is done.
  Updated by: 2.1

## Expectation Coverage

- E1: Under a declared `protocol-refresh`, an older managed protocol is refreshed by the agent at
  session start with nobody asked, and the only human act left is the commit (D1, D4, D6).
  Covered by: 1.1, 1.2, 2.1
- E2: Without the declaration, or while a task is guarded, nothing is refreshed unasked (D4, D6).
  Covered by: 1.1, 1.2
