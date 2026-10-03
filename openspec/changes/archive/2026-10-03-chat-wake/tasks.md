# Tasks

## 1. An addressed record wakes Codex, and nothing else does

- [x] 1.1 `keel chat wake run --once` starts one Codex turn per addressed record
  - Covers:
    - keel-cross-host-mailbox / An owner-installed waker starts one turn per addressed record
    - keel-cross-host-mailbox / Presence is visible and only an owner-installed waker launches a member
    - D2
    - D3
    - D4
    - D5
    - D6
    - F2
  - Touch:
    - src/core/chat/wake.js
    - src/core/chat/cli.js
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-run` checks, in a scratch repository with `chat-reply:lab` declared, a registration written by `keel chat wake add` under a scratch `KEEL_HOME` with a fake launchctl, and a fake `KEEL_CHAT_CODEX` that records its argv, working directory, and stdin and prints a `thread.started` event: with nothing unread, or only `@all`, or a mention in an undeclared group, `wake run --once` starts no turn; an `@cx` record in `lab` starts one `exec --json` turn in the worktree whose argv carries `model_auto_compact_token_limit=100000`, `sandbox_mode="workspace-write"`, and the git common directory as a writable root, and whose prompt carries no record text; `wake status --json` then reports the fake thread id; a second run with no new record starts nothing; a new `@cx` record starts `exec resume <thread>`; with `--max-per-hour 2` a third record starts nothing and status reports the registration held; a run while another holds the role's lock starts nothing; and `git status --porcelain` in the worktree stays empty. Fails with: `chat-wake-run:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8fff5d0aff865a976d0d7079cee1e278d7df53925e88bdc50b6bb7915a6a81ec
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-run` reports `chat-wake-run scenario passed.` With a fake Codex, `wake run --once` starts no turn with nothing unread, for an `@all` record, or for a mention in a group without `chat-reply`. One `@cx` record in `lab` starts one `exec --json` turn in the worktree whose arguments carry `model_auto_compact_token_limit=100000`, `sandbox_mode="workspace-write"`, and the git common directory as a writable root, and neither its arguments nor its standard input carry the record text. `wake status --json` then reports the fake thread id. A second run with no new record starts nothing, and a second `@cx` record starts `exec resume thread-fake-1`. With `--max-per-hour 2`, a third record starts nothing and status reports the registration held. A run while a live process holds the role's lock starts nothing, and the next run after release starts the turn. `git status --porcelain` in the worktree stays empty, and the registration is under `KEEL_HOME`.
    - M1.red: fail. Before `wake` existed the scenario reported `chat-wake-run: keel chat wake add failed: keel chat: No group wake. Create it with \`keel chat group create wake\`.`, carrying the declared signature `chat-wake-run:`.
    - M1.green: pass. The same scenario passes with `src/core/chat/wake.js` and the `wake add|status|run` routing in `src/core/chat/cli.js`.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: M1 drives the public `keel chat wake add`, `wake run --once --worktree`, and `wake status --json`, with only the Codex executable and launchctl replaced at the system boundary. It asserts each run clause of the added requirement: wake only for addressed, chat-reply, undelivered records; one turn per record; a new thread first and a resume after; the compaction and sandbox settings; no record text in the prompt; the hourly hold; the per-role lock; and nothing written into the worktree. The modified presence requirement's exception is exactly this owner-installed path. D4's fixed prompt is `PROMPT` in `src/core/chat/wake.js`.
      - Scope check: The diff adds `src/core/chat/wake.js` and changes `src/core/chat/cli.js` (options, usage, and `runWake` routed before location and presence) and `scripts/validate_plugin.py` (the fake Codex, the scratch helper, and the scenario), all in Touch, plus this change's own `tasks.md` (Change Verify). `remove` is in `wake.js` but not routed, and the add-time chat-reply warning is absent, so 1.2 keeps its own red. The Stop rule held: a turn runs only the configured Codex executable, and nothing is written in the repository.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - Starting a turn would need anything other than the configured Codex executable, or would write inside a repository.

- [x] 1.2 `keel chat wake add|remove|status` install and remove a LaunchAgent that watches the signal file
  - Covers:
    - keel-cross-host-mailbox / An owner-installed waker starts one turn per addressed record
    - D1
    - D5
  - Touch:
    - src/core/chat/wake.js
    - src/core/chat/cli.js
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-lifecycle` checks, with a scratch `KEEL_HOME`, `KEEL_CHAT_LAUNCH_AGENTS_DIR`, and a fake `KEEL_CHAT_LAUNCHCTL` that logs its arguments, that `keel chat wake add` in a worktree bound to `cx` writes a plist whose label starts `dev.keel.chat-wake.cx-`, whose `WatchPaths` names the role's signal file (which now exists), whose `ProgramArguments` end in `chat wake run --once --worktree <path>`, and which sets `RunAtLoad`, then calls `launchctl bootstrap`; that `wake add` in a worktree with no role, or with `--host` other than `codex`, is refused by name; that `wake status --json` lists the registration as installed; that `wake add` with no `chat-reply` declared says nothing will wake; and that `wake remove` calls `launchctl bootout`, deletes the plist and the registration, and keeps the log. Fails with: `chat-wake-lifecycle:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:554e569dc638ad8611b2ac650ed23bcc98c8e4c77a34b53d45ac84c1f6223393
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-wake-lifecycle` reports `chat-wake-lifecycle scenario passed.` With a scratch `KEEL_HOME`, LaunchAgents directory, and logging launchctl, `wake add` in the `cx` worktree writes one plist labelled `dev.keel.chat-wake.cx-…`. Its `WatchPaths` is the role's signal file, which now exists, and its `ProgramArguments` end in `chat wake run --once --worktree <the worktree>`. It sets `RunAtLoad`, and launchctl received `bootstrap`. `wake add` is refused naming a role in a worktree with none, and refused naming `--host` for `--host claude`. `wake status --json` lists the `cx` registration once as installed. `wake add` in a worktree without `chat-reply` says it `declares no chat-reply`. After one turn has written the log, `wake remove` sends `bootout`, deletes the plist and the registration, and keeps the log.
    - M1.red: fail. Before the warning and the `remove` route existed the scenario reported `chat-wake-lifecycle: wake add without chat-reply does not say nothing will wake: Registered a waker for rtl in …`, carrying the declared signature `chat-wake-lifecycle:`.
    - M1.green: pass. The same scenario passes after `src/core/chat/cli.js` prints the chat-reply line from `wake add` and routes `wake remove`.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: M1 drives the public `keel chat wake add`, `status --json`, `remove`, and `run --once`, with only launchctl and Codex replaced at the system boundary. It asserts D1's LaunchAgent contents (signal-file `WatchPaths`, `RunAtLoad`, the `run --once --worktree` program) and D5's machine-local registration and log. It also asserts the requirement's add, remove, and status clauses, including the refusals and the warning that nothing will wake without `chat-reply`.
      - Scope check: The diff changes `src/core/chat/cli.js` (the add-time chat-reply line and the `remove` route) and `scripts/validate_plugin.py` (the lifecycle scenario), both in Touch. `src/core/chat/wake.js` was not changed in this task: `remove` and the host and role refusals were written in 1.1, and this task routes and proves them. The task-start warning that 1.1 and 1.2 share a Touch set was considered: 1.2's red was real (the missing warning and the unrouted `remove`), so the split held. The Stop rule held: only the user's LaunchAgents directory and launchctl are touched.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - Installing would need anything beyond the user's own LaunchAgents directory and launchctl.

- [x] 1.3 The real Codex is woken in the playground, and the documentation describes the waker
  - Covers:
    - F1
    - D1
    - D3
  - Touch:
    - docs/chat-slack-setup.md
    - docs/chat-slack-setup.zh-CN.md
    - docs/codex-validation.md
    - README.md
    - README.zh-CN.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - Reason: the behavior is a real launchd trigger starting a real Codex turn on the owner's machine, which no scratch test can host; its unit behavior is proved by 1.1 and 1.2.
    - M1: with this tree's `keel` on the owner's machine, `keel chat wake add` runs in `~/my_github/chat-playground/.worktrees/codex`, then `owner` posts an `@cx` record to `lab` and nobody starts Codex; within five minutes `lab` shows a `codex` reply to that record, `keel chat wake status` names a thread, and the wake log shows one turn; a following `@all` post starts no turn within two minutes. The commands and their output are quoted in Evidence.
    - M2: each of the five documents describes `keel chat wake` as the way to wake Codex for addressed records, says it needs `chat-reply:<group>` and continues one thread with compaction, and keeps the warning against polling with the model; and `docs/codex-validation.md` no longer says that nothing wakes an idle Codex session. A one-off script greps the documents for these statements and its output is quoted in Evidence.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a418f9f205bf8970a3cfd3a906099c412b57cf92c9db1e072192faaf30f146a9
    - M1: pass. On 2026-10-03 the owner ran `node <this tree>/bin/keel.js chat wake add` in `~/my_github/chat-playground/.worktrees/codex`. That installed and loaded `dev.keel.chat-wake.codex-e29908b0`, with `launchctl list` showing it. At load the waker started one new-thread turn for three earlier `@cx` records that 5.86.0 replies had left unread, and Codex posted nothing new for them. `owner` then posted `20261003T063804648Z-owner-9522e8`, an `@cx` record in `lab`, and nobody started Codex. The log shows `06:38:05.095Z resuming 01a1007a-f7b7-75d3-9cbc-c2fb50afaa70 for 1 addressed record(s)` and `06:38:38.366Z turn exited 0`. `lab` shows the reply `20261003T063820863Z-codex-a0a924`, posted 16 seconds later: `根据本轮收到的 [keel chat wake] 提示，我是因有发给 codex 角色的待处理消息，由 keel chat 自动唤醒启动的。` `git status --porcelain` in the Codex worktree printed nothing. `owner` then posted the `@all` record `20261003T063832687Z-owner-48b623`, and two minutes later the log held no further turn. `keel chat wake status` reported `thread 01a1007a-f7b7-75d3-9cbc-c2fb50afaa70; last turn 2026-10-03T06:38:05.093Z; 2/10 turns in the last hour`.
    - M2: pass. `python3 openspec/changes/chat-wake/evidence/check_docs.py "$PWD"` printed `checked 5 documents x 4 statements, plus codex-validation wording and keel chat help` and `failures: none`. Within the section that names `keel chat wake add`, each of the five documents says it needs `chat-reply` and compacts one thread, and each document keeps the warning against polling with the model. `docs/codex-validation.md` no longer says nothing wakes an idle Codex session, and `keel chat help` lists `wake add`, `remove`, and `status`. A negative run against `README.zh-CN.md` with `会自动压缩的` removed reported `README.zh-CN.md: lacks one thread with compaction` and exited 1. Checker: artifact openspec/changes/chat-wake/evidence/check_docs.py sha256:86ee412221b5a4aacd863e8dad64f968b4cee44d0b1dddb59470fd30cf7f6544
    - Review:
      - Status: pass
      - Acceptance check: M1 is F1 and D1–D3 on the real machine: a launchd `WatchPaths` trigger started a real Codex turn for an addressed record with no one starting it, resumed the waker's own thread, and Codex answered in the chat under its `chat-reply:lab` authorization. A broadcast started nothing, and the worktree stayed clean. M2 shows the five documents describe what was built and keep the #194 warning, and the checker's negative run shows it detects a missing statement.
      - Scope check: The diff changes the five documents and `keel/CHANGELOG.md`, all in Touch, plus this change's own directory, which holds the checker. The LaunchAgent was installed by the owner, and the playground changes are chat records and Keel's machine-local state, none of them in this repository. The Stop rule held: Codex wrote only chat records, and each record started at most one turn.
      - Findings: The load-time turn spent one turn on three records already answered under 5.86.0, whose replies did not advance the cursor. That is #201, fixed on main and released with this change, and D2's delivered mark kept those records from waking Codex again. Discard reason: no further work is owed, because #201 is merged and ships in the same release.
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - The real run shows Codex writing anything other than a chat record, or more than one turn for one record.

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario, once 1.1 and 1.2 have both registered their scenarios.

## Change Evidence

- C1: pass. `npm test` reports `validation --all passed: baseline plus 215 scenarios, 1 skipped: output-survives-the-pipe.` once both `chat-wake-run` and `chat-wake-lifecycle` are registered.

## Invalidates

- I1: "Keel MUST NOT start any session" — `openspec/specs/keel-cross-host-mailbox/spec.md`. Updated by: 1.1
- I2: "nothing wakes an idle Codex session" — `docs/codex-validation.md`. Updated by: 1.3
- I3: "No idle polling/wake claim; receive on startup/next prompt" — `docs/codex-validation.md`. Updated by: 1.3
- I4: "Sessions that cannot wake on their own (Codex and others)" and "不能自己被唤醒的会话（Codex 等）" — `docs/chat-slack-setup.md` and `docs/chat-slack-setup.zh-CN.md`. Updated by: 1.3
- I5: "Codex idle wake-up and native write-guard enforcement remain unverified" — `README.md`, and "不能自己被唤醒的宿主（如 Codex）" — `README.zh-CN.md`. Updated by: 1.3
- I6: "Keel schedules nothing" — `AGENTS.md`. Discard reason: the waker is triggered by a file change that a mention causes, never by a schedule, so the sentence stays true.

## Expectation Coverage

- E1: An addressed record in a group where replying is authorized starts one Codex turn without anyone starting it, and nothing runs while nothing is addressed. Covered by: 1.1, 1.2, 1.3
- E2: The waker's turns continue one thread with a compaction limit. Covered by: 1.1, 1.3
- E3: The waker is installed only by the owner, and nothing it keeps enters a repository. Covered by: 1.2, 1.1
