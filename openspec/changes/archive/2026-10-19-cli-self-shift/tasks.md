# Tasks

## 1. A CLI session changes its own shift through the waker's queue

- [x] 1.1 Queue CLI hand-offs in `ready --wake`; let `keel tick` stop the old and start the new
  - Covers:
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / The waker hands a CLI shift over once the old session is idle
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / A failed hand-off is a risk
    - D1
    - D2
    - D3
    - D4
    - D5
  - Read:
    - src/core/shift.js
    - src/core/tick.js
    - src/core/patrol.js
    - src/core/config.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/shift.js
    - src/core/tick.js
    - src/core/patrol.js
    - src/core/config.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` runs the real `keel shift ready --wake` as CLI session `5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea` and the real `keel tick` with `KEEL_CLAUDE` pointing at a fake whose `agents --json` the test controls, in the measured shape (`sessionId` the full id, `id` the 8-character job id): the note records `CLI session: 5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea.`; a tick while busy stops and starts nothing and status shows `pending`; a tick while idle runs `stop 5b14fbae` once and `--bg -n verify --permission-mode auto <prompt naming keel shift resume>` once in verify's worktree; status shows `delivered`, `newsess1` and `claude attach 5b14fbae`; a further tick starts nothing; a start that exits 1 with `Workspace not trusted.` shows `failed` with that reason and `keel patrol` reports a `risk:` naming the hand-off. Fails with: `does not say keel tick will hand over`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:92ca1620d0a2edd94d5b3d0d7bd352b986cffcb9828cea9cb10a3bd85c473637 (keel 5.156.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` reports `shift-cli-self-shift scenario passed.`
    - M1.red: fail. With the scenario written first and the code unchanged: `shift-cli-self-shift: ready --wake in a CLI session does not say keel tick will hand over: 'Stored the shift note … Now clear …'`, carrying the declared signature. After the reauthorization, with the measured id shape in the fake: `the idle old session was not stopped once: [{'argv': ['stop', '5b14fbae-b6aa-40b6-a72a-b3f89d2c6eea'], …}]`.
    - M1.green: pass. With `ready --wake` recording `CLI session:`/`CLI process:` and queueing `shift/queue/<role>.json`, `handOver` (from `keel tick`) waiting on `busy`, stopping the old job by its `id`, starting `claude --bg -n <role> --permission-mode <mode> <resume prompt>` in the worktree and recording `delivered`/`failed`, the status `Hand-offs:` section, the patrol risk and `shift: permission_mode:`, the scenario passed.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 300 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit. An earlier run failed `assertion-shape-count` on combined checks in the new scenario; they were split.
    - Review:
      - Status: pass
      - Acceptance check: the real `ready --wake` in a CLI session records the session and queues the hand-off; the real `keel tick` waits while `busy`, then stops job `5b14fbae` once and starts one `--bg -n verify --permission-mode auto` session with a `keel shift resume` prompt in verify's worktree, never `--resume`; status shows pending, then delivered with `newsess1` and `claude attach 5b14fbae`; a failed start shows `Workspace not trusted` and is a patrol risk.
      - Scope check: `git status --short` lists `src/core/shift.js`, `src/core/tick.js`, `src/core/patrol.js`, `src/core/config.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Resolved here: M1 — `claude stop` and `claude attach` refuse the full session id (`No job matching`, read-only `claude logs` on a live session, 2026-10-19); the fake now has the measured `id` field and the code stops by it.
        - Discard reason: no live CLI hand-off ran end to end here — it would stop a real role session; the owner's first `keel shift ready --wake` under the installed `keel tick` job is the live run, and `keel shift status` shows its result.
    - Blocker: none
    - Reauthorizations: 2026-10-19 — before any Evidence: a read-only `claude logs <full sessionId>` on a live session answered `No job matching`, while the 8-character `id` from `claude agents --json` worked, so `stop` and `attach` take the job id; D2, D3, the spec scenario and M1 now use the measured shape; anchor re-recorded.

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
    - M2: the delta requirements are promoted into `keel-shift-change`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6fd7c52f04a393c47e1a48d4bf55bc292062324840d1213faf5a37b34394dbeb (keel 5.156.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.156.0 → 5.157.0; with the "A CLI session hands over its shift through `keel tick`" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-shift-change`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Now clear" as the only next step `keel shift ready --wake` gives — `src/core/shift.js`. Updated by: 1.1

## Expectation Coverage

- E1: A CLI role changes its own shift unattended, with a clean context and the old session kept, through the one waker, and a failure is visible (#357, owner 2026-10-19; D1, D2, D3, D4, D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
- E3: #346 is closed as desktop-only rather than fixed (D6). Discard reason: the team no longer runs the desktop clear path (owner, 2026-10-19), and the CLI hand-off waits for an idle session instead of racing a clear.
