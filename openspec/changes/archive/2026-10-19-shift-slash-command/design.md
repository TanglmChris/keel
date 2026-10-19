## Context

#386 asks for the three things a session does when it changes its own shift — check, note, `ready --wake` — as one command. The host steps after `ready` differ by host and `ready` already prints them, so the command points at that output instead of copying it.

## Facts

- F1 — The Claude plugin is the npm package root (`.claude-plugin/plugin.json`); its skills, agent and hooks are declared there with paths under `plugins/keel/`. Claude names a plugin command after its file, so `commands/shift.md` in the `keel` plugin is `/keel:shift`.
- F2 — `keel shift check` skips the checking process and its ancestors. A child the host started under the session, such as `caffeinate -i -t 300`, is neither, so it is reported as a running process.
- F3 — `keel shift ready` takes the note from `--file -` on stdin, and refuses while the check reports items unless `--force-reason` is given.
- F4 — On the CLI `ready --wake` leaves a waiter that replaces the session once it has finished its turn (5.162.0, #388); a session that keeps working or asks the owner a question after `ready` is not replaced. On the desktop app it prints four steps that `self-shift` in `keel/config.yaml` lets a session take unasked.

## Decisions

- D1 — The command lives at `plugins/keel/commands/shift.md`, next to the skills and agents, and the root manifest lists it under `commands`. The Codex manifest and `plugins/keel/hooks/` are untouched: Codex has no plugin commands, and nothing in the command is host code.
- D2 — The command orders the steps and names the judgement each needs; it carries no logic. It tells the session to deal with each item `check` reports or ask the owner, and to tell a host keep-awake from a process the session started: the first may stay, with `--force-reason` naming it; the second is stopped or asked about. Keel does not classify the process: `check` stays as it is, and a rule that decided which processes are the host's would be a second shift feature.
- D3 — The note is written to `ready` through a quoted heredoc on stdin, so backticks in it are not executed (the owner's standing shell rule).
- D4 — The command does not decide that a shift happens. It runs because the owner typed it; a session reaching the task-boundary rule of `docs/shift-change.md` still chooses to suggest it.
- D5 — The scenario runs the command's own fenced `keel shift` lines in a fixture worktree bound to a role and checks the stored note, so a command that names a flag `keel` no longer accepts, or a heredoc that stores nothing, fails.
