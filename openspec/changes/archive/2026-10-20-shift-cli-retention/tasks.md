# Tasks

## 1. The CLI hand-over and the history of a past shift

- [x] 1.1 Wait for the old session's process to exit before the rename resume
  - Covers:
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / The rename waits for the stop to take effect
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / A session that never stops is not resumed
    - D1
  - Read:
    - src/core/shift.js
    - openspec/changes/shift-cli-retention/design.md
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` with the fake `claude`'s live row carrying the pid of a real child process, `stop` dropping the row's `status` at once and ending that process about a second later, and a resume while it still runs starting a copy (F1, F2): the `/rename` resume runs only after the process has exited, no copy is started, and the old session takes the shifted name. Fails with: `the rename resumed a session that was still running`
    - M2: the same scenario's never-stops section, with a process `stop` never ends and `KEEL_SHIFT_STOP_WAIT_MS` short: no `/rename` resume runs, the new session still starts, and status says the rename was not shown. Fails with: `a session that never stopped was resumed for its rename`
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:78e7b6b3570b863984396b071b0ab15bc9d77b7eb8044a911d423d54eef2b646 (keel 5.166.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-self-shift` reports `shift-cli-self-shift scenario passed.`; no `sleep 600` process is left afterwards (`pgrep -f "sleep 600" | wc -l` → 0).
    - M1.red: fail. With the fake's live row carrying a real detached process, `stop` dropping the status at once and ending the process a second later, and 5.166.0's code: `shift-cli-self-shift: the rename resumed a session that was still running, starting a copy: [...]` — the original stopped and still named `verify`, a copy `c0c0c0c0` named `verify · shifted …` — the shape of the probes np0/np8 (F2). A first attempt passed by mistake: the fake's killer kept the fake's stdout open, so Node's `spawnSync` of `stop` waited the second out; its stdio now goes to /dev/null.
    - M1.green: pass. With `retire()` waiting for the pid its row showed before the stop to exit, the resume ran after the process was gone, no copy was started, and the original took the shifted name.
    - M2: pass. The never-stops section (a process `stop` never ends, `KEEL_SHIFT_STOP_WAIT_MS` 1000) passes: no `--resume` call, one new session, status `delivered` with `rename not shown`.
    - M2.red: fail. With the main path's stop set to end the process at once (so the scenario reached this section) and 5.166.0's code: `shift-cli-self-shift: a session that never stopped was resumed for its rename: [['stop', '5b14fbae'], ['--bg', '--resume', '5b14fbae-…', '/rename verify · shifted 2026-10-20 00:30'], ['stop', '5b14fbae'], ['--bg', '-n', 'verify', …]]`; the scenario was restored afterwards.
    - M2.green: pass. A process still running at the bound is stopped again and not resumed, and the hand-over is delivered with the rename recorded as not shown.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: against a fake `claude` that drops the status before the process exits and copies a running session on resume (F1, F2), the hand-over resumes only once the process has exited, leaves no copy and renames the original; a process that never exits is not resumed and the hand-over still delivers. The full suite is C1's.
      - Scope check: `git status --short` lists `src/core/shift.js`, `scripts/validate_plugin.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md` and this change's directory, all in Touch or the record layer.
      - Findings:
        - Durable owner: https://github.com/TanglmChris/keel/issues/397 — the next real CLI shift checks that the original is renamed and no copy is left; b4d145a2's revert after a hand rename (a queued task notification) is recorded there and still unexplained.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 Keep the newest old sessions and remove older ones whose transcript Keel holds
  - Covers:
    - keel-shift-change / A CLI session changes its own shift through the waker's queue / Only the newest old sessions stay listed
    - D2
  - Read:
    - src/core/shift.js
    - src/core/config.js
    - src/core/chat/notice.js
  - Touch:
    - src/core/shift.js
    - src/core/config.js
    - scripts/validate_plugin.py
    - keel/config.yaml
    - docs/cli-team.md
    - docs/cli-team.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-keeps-old-sessions`: with `shift: keep_old_sessions: 2` and, after a hand-over, five stopped background rows in verify's worktree (one with no transcript anywhere), one stopped row in rtl's worktree and the new session, the calls include `rm` for exactly the two oldest of verify's rows that have a transcript, each after Keel's store holds its copy; the row with no transcript, rtl's row and the new session stay; `keel shift status` names the removed ids. Fails with: `the hand-over removed no old session`
    - M2: the same scenario with no `keep_old_sessions:` declared and four old rows: exactly the oldest is removed (default 3), and with `keep_old_sessions: many` a message names the ignored value and 3 applies. Fails with: `the default keeps the wrong number of old sessions`
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8f5fa94ed9bee485774f89ac0b478e90b198c579c74f4744140c8f89915a51f6 (keel 5.166.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-cli-keeps-old-sessions` reports `shift-cli-keeps-old-sessions scenario passed.`: with `keep_old_sessions: 2`, `rm` ran for `01010101` and `02020202` only, each when Keel's copy existed; `03030303` (no transcript), rtl's `05050505`, `newsess1`, the handed-over `5b14fbae` and `04040404` stayed; status named both removed ids.
    - M1.red: fail. With the scenario written and no removal code: `shift-cli-keeps-old-sessions: the hand-over removed no old session: '{"argv": ["agents", "--json", "--all"]}\n{"argv": ["stop", "5b14fbae"]}…` — the calls held no `rm`.
    - M1.green: pass. With `removeOldSessions()` run after a delivered hand-over and `keep_old_sessions` read by `readShiftDeclaration`, the scenario passed.
    - M2: pass. The default and unreadable-value sections pass: with no declaration and three older rows plus the handed-over one, only `01010101` was removed; with `keep_old_sessions: many` the same, and `keel shift status` names `keep_old_sessions`.
    - M2.red: fail. With the first section cut out (so the scenario reached this one) and no removal code: `shift-cli-keeps-old-sessions: the default keeps the wrong number of old sessions (keep_old_sessions None): removed []`; the scenario was restored afterwards.
    - M2.green: pass. Default 3 applied with no declaration and with `many`, whose message is stored on the entry and shown by status.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: against a fake `claude` with the measured row shapes and an `rm` that logs whether Keel's copy existed when it ran, the hand-over keeps the newest N of the role's stopped background sessions and removes only older ones whose transcript Keel holds; another worktree's session, the new one and one with no transcript stay; the default is 3 and an unreadable value is named.
      - Scope check: `git status --short` lists `src/core/shift.js`, `src/core/config.js`, `scripts/validate_plugin.py`, `docs/cli-team.md`, `docs/cli-team.zh-CN.md` and this change's directory, all in Touch or the record layer; `keel/config.yaml` was in Touch and left unchanged, since it does not document `shift:` at all.
      - Findings:
        - Discard reason: removal counts every stopped background session in the role's bound worktrees, not only those a hand-over retired, so a stopped probe there is removed too; that is D2 as authored — the role owns its worktree, and the removed session's conversation stays in the host file and Keel's copy.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.3 Show a past shift's whole conversation
  - Covers:
    - keel-shift-change / A past shift is shown in full / A removed session's shift is shown from the kept copy
    - keel-shift-change / A past shift is shown in full / An id that matches no segment
    - D3
    - F5
  - Read:
    - src/core/shift.js
  - Touch:
    - src/core/shift.js
    - scripts/validate_plugin.py
    - docs/shift-change.md
    - docs/shift-change.zh-CN.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-history-show`: a found transcript of verify with a user prompt, an assistant reply longer than any snippet, a tool call and its result is kept in Keel's store, its host file is deleted, and `keel shift history verify --show <8-character id>` prints the header and all four in order, each in full. Fails with: `--show printed no conversation`
    - M2: the same scenario: `--show 00000000` exits 1 and says no segment matches. Fails with: `--show of an unknown id did not exit 1`
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:359f4d9b8a1fb9c73226e8e10c64da9e5da4aa1343728eb63c6ece5d1e21f95f (keel 5.166.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario shift-history-show` reports `shift-history-show scenario passed.`: with the host file deleted, `--show 4162aee5` printed a header naming the transcript and 2026-10-14, then the prompt, the 600-character reply uncut, the `Bash` call and its result, in order, from Keel's kept copy. Also run on this machine's real store: `node bin/keel.js shift history keel-maint --show 4162aee5` printed the 2026-10-14 → 2026-10-18 shift, 3033 lines, exit 0.
    - M1.red: fail. With the scenario written and no `--show`: `shift-history-show: --show printed no conversation: 0 '2026-10-20T00:35:18+08:00 → now  …/b.jsonl…` — the option was ignored and the listing printed.
    - M1.green: pass. With `showSegment()` matching the segment by transcript-name prefix, reading the host file or the kept copy, and `shownEntries()` printing text, tool calls and results in full, the scenario passed.
    - M2: pass. `--show 00000000` exits 1 with `keel shift: no segment of verify matches "00000000"; …`; on the real store an ambiguous `--show 4` exits 1 naming the two matching transcripts.
    - M2.red: fail. With the M1 section cut out (so the scenario reached this one) and no `--show`: `shift-history-show: --show of an unknown id did not exit 1: 0 '…'`; the scenario was restored afterwards.
    - M2.green: pass. No match, or more than one, raises a `ShiftError` that names the candidates and exits 1.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: through the public `keel shift history --show`, a past shift whose host file is gone is printed in full from Keel's copy, in order, tool calls included; an unknown id exits 1 and says so. The owner's requirement (F5) is met for any session Keel recorded or found, listed in `claude agents` or not.
      - Scope check: `git status --short` adds `docs/shift-change.md` and `docs/shift-change.zh-CN.md` to task 1.1/1.2's files; `src/core/shift.js`, `scripts/validate_plugin.py` and both docs are in Touch. The zh-CN doc had no history paragraph at all; one was written, covering list, grep and show.
      - Findings:
        - Discard reason: `--show` prints the whole conversation including system reminders injected into user turns; the owner asked for the complete content, so nothing is filtered.
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
    - Contract: keel-task-capsule/v1 sha256:2bb80df3311f80a2f29a7ff18e675b9fdddb095042f23753eee0814165a51099 (keel 5.166.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.166.0 → 5.167.0; with the "CLI shifts keep a bounded number of old sessions, and any past shift can be read in full" section written into the stub the bump left, `version-alignment scenario passed.` (exit 0).
    - M2: the MODIFIED requirement replaced the CLI one and the ADDED "A past shift is shown in full" was placed after the history requirement in `keel-shift-change`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E4 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond tasks 1.1–1.3's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: characterization
- C1: `npm test` passes once every task of the change is in place: `validation --all passed`.

## Change Evidence

- C1: pass. `npm test` after tasks 1.1–2.1: `validation --all passed: baseline plus 307 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0; load 8.5 at start). An earlier run failed `assertion-shape-count` (82 vs 80) on two `if`s of `shift-history-show` that joined two failures behind one message; both were split, and that scenario and `assertion-shape-count` passed before this run.

## Invalidates

- I1: "once `claude agents` shows the session stopped (`claude stop` returns before the process exits" — `docs/cli-team.md` and its zh-CN twin, and the `retire()` comment in `src/core/shift.js`: the listing shows it stopped before the process exits. Updated by: 1.1.
- I2: "waiting until `claude agents` shows it stopped or gone" — the CLI requirement in `openspec/specs/keel-shift-change/spec.md`. Updated by: 2.1.
- I3: "old session kept, reopen it with `claude attach`" — `describeHandOff` in `src/core/shift.js` and the hand-off paragraph of `docs/cli-team.md` and its zh-CN twin: true only for the newest kept ones now. Updated by: 1.2.
- I4: "`keel shift history <role>` lists those transcripts" — `docs/shift-change.md` and its zh-CN twin, and the `keel shift history` usage line in `src/core/shift.js`: it now also shows one. Updated by: 1.3.

## Expectation Coverage

- E1: Retiring the old session never starts a copy of it (#397; D1). Covered by: 1.1
- E2: Each role keeps at most the declared number of old sessions listed, and none is removed before its transcript is in Keel's store (#397; D2). Covered by: 1.2
- E3: A shift no longer listed can be read in full (#397; D3). Covered by: 1.3
- E4: The release carries it. Covered by: 2.1
