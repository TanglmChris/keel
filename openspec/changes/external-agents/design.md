## Context

Issue #219, with the owner's decisions recorded at https://github.com/TanglmChris/keel/issues/219#issuecomment-5978896700 and two further answers given in the session on 2026-10-04.

## Facts

- F1 — `keel-authorized-delegation` already makes the caller the only owner, treats a delegate's report as a claim, and keeps task completion, the checkbox, and Review with the current agent. `keel project --event subagent-start [--subagent-mode implementation]` compiles the brief, and implementation refuses without a guard matching the task, fingerprint, and Touch (`src/core/projection.js`, `delegationRefusal`).
- F2 — The write guard is the host's PreToolUse hook. A process the session launches through a shell writes without passing through it. `keel gate task-complete` compares the worktree against Touch, so writes carried back into the session's checkout are still attributed there.
- F3 — codex-cli 0.159.3 (`codex exec --help`, 2026-10-04) offers `-s read-only|workspace-write|danger-full-access`, `-C <dir>`, `-o <file>`, and reads the prompt from stdin when given `-`.
- F4 — dsh 0.2.0-rc.2 (`dsh headless --help`, 2026-10-04) is at `/Applications/DeepSeek Harness.app/Contents/Resources/runtime/cli/bin/dsh`, not on PATH. `dsh --profile headless [--json] [--session-id <id>] -` reads the task from stdin. It offers no sandbox flag and no working-directory flag.
- F5 — rtl_ppa_prj `docs/toolchain.md` (main 632ad85) records the pitfalls: a prompt argument without `< /dev/null` waits on stdin; `codex exec resume` against a Desktop thread breaks; a shared branch staled the other session's index and nearly overwrote its commits; PATH does not inherit the caller's environment script; a ten-hour autonomous run spent most of its time packaging about 1.9 GB of evidence; macOS has no `timeout`; codex has a usage quota.
- F6 — `keel/config.yaml` is read line by line, and Keel carries no YAML dependency (`src/core/config.js`). Per-machine state already lives under `~/.keel/`, overridable by `KEEL_HOME`.

## Decisions

- D1 — Keel compiles the brief and prints the command line; it never launches the agent. Spawning would make Keel a tool that starts external processes and sends data, which nothing else in it does, and the session's own shell already runs commands. (Owner, 2026-10-04.)
- D2 — The catalog records facts only: command template, sandbox per mode, where data goes, and pitfalls each stamped with a date and a source. It carries no field saying what an agent is good at. Which work suits an external agent is the project's to write, the way lenses are. The catalog is read on demand through `keel agents`, never at session start, so it cannot steer a session that was not already considering a call. (Owner.)
- D3 — Registration is split. Tool paths, versions, and templates are machine facts and live in the bundled catalog plus `~/.keel/agents.json`. Which agents a project allows and what it must not send are project rules and live in `keel/config.yaml` under `external_agents:`. The machine file is JSON because Keel has no YAML parser (F6) and the file is small; a malformed file is reported and its entries are not used. (Owner chose the split; the format is mine, reversible.)
- D4 — The egress check runs when the brief compiles: a Read or Touch path that matches an `egress_deny` pattern refuses the brief and names the path, the pattern, and its reason. The output also says Keel cannot observe what the agent reads beyond the brief. (Owner.)
- D5 — `egress_deny` is a deny list, each entry `- <glob>: <reason>`, the same shape as `full_mode_paths`. An entry without a reason is unreadable and refuses every brief until corrected, because a deny list that silently drops an entry sends what it was written to keep. (Owner chose the deny list.)
- D6 — With no `external_agents:` block, or an agent not in `allow:`, the brief is refused and the message says how to declare. Every other declaration in that file authorizes nothing when absent, and data leaving the machine is the decision a project makes once, explicitly. (Owner.)
- D7 — The checkout is the write boundary for an external agent (F2). Implementation mode always needs `--dir` to be a separate worktree of the same repository. Helper mode needs one when the catalog entry declares no read-only sandbox, which today is dsh (F4). A separate worktree is recognised by a different `git rev-parse --show-toplevel` and the same `--git-common-dir` as the current checkout.
- D8 — Every refusal of `keel project --event subagent-start` still applies, because the brief is that projection. Implementation still needs the matching active guard in the session's checkout (F1). The prompt file adds the prohibitions that matter for a process outside the host: no commit, push, branch switch, issue, or OpenSpec and Keel state, and stay inside `--dir`.
- D9 — The protocol gains one sentence under Full mode naming `keel agents` and `keel agents brief`. Pitfalls stay in the catalog, out of the resident protocol.

## Risks

- A catalog fact goes stale when a CLI changes. Each fact carries its date and source, so its age is visible, and `~/.keel/agents.json` overrides an entry without a release.
- The egress check sees only the paths the brief names. An agent with a read sandbox still reads anything in its directory. The output says so; the deny list is a guard against handing a file over, not a confinement.
