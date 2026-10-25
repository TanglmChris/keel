# A team of Claude Code CLI sessions

The desktop path of `keel chat`, `keel shift` and `keel patrol` relies on the Claude desktop app: its scheduled tasks run the patrol, and its session tools wake and clear sessions. A team can instead run each role as a background session of the Claude Code CLI (`claude --bg`), with no desktop app running (#369). This page is that path, end to end. Measured on Claude Code 2.1.303. In Chinese: [cli-team.zh-CN.md](cli-team.zh-CN.md).

## What does what

| Need | Desktop app | CLI |
|---|---|---|
| One session per role | an app session in the role's worktree | `claude --bg -n <role>` in the role's worktree |
| Wake an idle session | a mention, an assigned todo or a direct message | the same: the chat's file hook wakes an idle background session |
| Wake a session that has ended | `send_message` to the session | `keel chat wake now <role>`, or `keel tick` once per new record |
| Run the patrol on a schedule | a host scheduled task (`host_task:`) | `keel tick`, run by launchd (`runner: tick`) |
| Change shift | the session clears itself; a waiter wakes the new shift | a waiter stops the old session and starts a new one named for its start; `keel tick` does the same if the waiter is gone |
| Open a previous shift's conversation | the archived app session | `claude attach <id>` on the stopped session |

## Setting up a role

1. Create the role's worktree and run `claude` there once, interactively, to accept the trust prompt. Trust is per directory and is not inherited from a trusted parent: `claude --bg` in a directory nobody trusted fails with `Workspace not trusted`, and so does every later start there, including the one a shift change makes.
2. Start the session in the background: `claude --bg -n <role>`. The name is the session's title in `claude agents`.
3. In that session, bind the role: `keel chat role --set <role>`. From then on its presence records the CLI session's id and process, which is what lets Keel resume or replace it.

Run one session per role. If a second session is bound to the same role — for example a `claude --resume` of a session that is still running — both post under one name and share one read cursor, so whichever reads first hides records from the other. `keel context`, and `keel chat post`, `dm`, `todo`, `unread` and `read` on stderr, warn while two live sessions are bound to one role. Stop one of them.

## Waking

An idle background session is woken like any Claude session: only a mention, an assigned todo or a direct message wakes it, and everything else waits for its next prompt.

A session that has ended — stopped, or its process gone — sees nothing. `keel chat post` and `keel patrol` say which addressed roles are in that state and name the step: `keel chat wake now <role>` resumes the role's recorded session with `claude --bg --resume <session id>` and a prompt to read its unread records. It passes no other flag, because any flag given with `--resume` starts a copy with a new session id instead of continuing the same one; the resumed session keeps its saved options, its permission mode included.

`keel tick` does the same by itself, once per new record: on each run it resumes every role whose CLI session has ended while a record that wakes it waits, and it does not resume that role again until a newer one arrives. A parked role (`keel chat role --park`) is left alone.

## The patrol, run by `keel tick`

`keel tick` is one model-free step for a host scheduler to call every few minutes. On each run it resumes ended sessions (above), carries out queued shift hand-offs (below), and runs the coordinator's `keel patrol --since-last --notify` — after a `git fetch` — only once the previous patrol's recommended next run has passed. Keel schedules nothing: launchd recurs it.

```yaml
patrol:
  role: pm
  every: 30m
  runner: tick
  cadence: adaptive
```

`runner: tick` tells the coordinator's new sessions and `keel shift resume` that the patrol runs outside the session, so they are not reminded to re-create a schedule. `keel tick task` prints the launchd job — a plist that calls `keel tick` every 300 s in the coordinator's worktree, logging to `tick/tick.log` in the chat store — with the two commands that install it and the one that removes it. Keel installs nothing; run the commands yourself. The plist carries the `PATH` of the shell that printed it, so `claude` and `git` must be on it then, minus any Claude plugin cache directory, which belongs to one release. It runs the `node` found on that `PATH` that is the same binary as the one that printed it, such as `/opt/homebrew/bin/node` rather than its versioned `Cellar` target, so a `brew upgrade` does not break the job; `keel chat wake add` and the chat bridge do the same. `keel --doctor` prints a `launchd` line for each `dev.keel.*` LaunchAgent and names any whose node no longer exists, with the command that re-creates it.

Every patrol prints a `next:` line with its recommended next run, and `keel tick` waits for it. Without `cadence: adaptive` that is `every:` (rule `fixed`). With it, the first rule that holds sets it:

| Rule | When | Default |
|---|---|---|
| `risk` | the patrol reported a risk | `30m` |
| `quota` | `--quota` is at 90 or above | `4h` |
| `night` | now is inside `quiet:` (for example `23:00-08:30`) | until the window ends |
| `busy` | another role is active, or an active role holds an open todo or wait | `1h` |
| `idle` | otherwise | `3h` |

Each default can be overridden by a flat key under `patrol:` (`risk: 15m`), and `min:` and `max:` clamp every rule but `night`.

## Changing shift

A CLI session cannot clear itself, so a shift change replaces the session instead. The role runs `keel shift check` and `keel shift ready --wake "<note>"` as on any host. In a CLI session, `ready --wake` records the session in the note (`CLI session:` and `CLI process:`) and queues a hand-off in the chat store, leaves a detached waiter that carries it out, then tells the session to end its turn.

The waiter looks the session up in `claude agents` every few seconds (`keel tick` does the same on each run, as the fallback when the waiter has died; a lock keeps the two from starting two sessions, and a repository needs no tick for its shift changes). While `claude agents` shows the session busy, or waiting for input — it is blocked on a question to you — it waits: a hand-over never cuts a conversation off. It reads the status, not the job state, which labels the session's last message rather than whether its turn has ended (#393). Once the session is idle, stopped, or gone, it stops it with `claude stop`, which keeps the conversation, and does not resume it. Then it starts a new session in the same worktree with `claude --bg -n "<role> · <MM-DD HH:MM>" --permission-mode <mode>` and the prompt to run `keel context` and `keel shift resume`. The new shift starts with a clean context, a new session id, and a name of its own: the role and the local time it started, so no two shifts share a name in `claude agents` or on claude.ai. The old session keeps the name it started with. It is not renamed, because renaming took a resume, and a session running with Remote Control writes its claude.ai title back over a rename (#399). The mode comes from `keel/config.yaml`, and is `auto` when nothing is declared:

```yaml
shift:
  permission_mode: auto   # default, acceptEdits, auto, plan or bypassPermissions
  keep_old_sessions: 0    # old shifts left listed per role; 0, the default, keeps none
```

Each shift change stops the old session. After a hand-over, the newest `keep_old_sessions` of the role's stopped sessions stay listed for `claude attach`, and each older one is removed with `claude rm` once Keel's store holds a copy of its transcript (#397). Nothing is kept when nothing is declared (#418): the shift just handed over is removed too, so it no longer appears in `claude agents` or on claude.ai beside the current one, where a stopped session read like a live one. `claude rm` of a session started in an existing worktree leaves the worktree in place. Only a session with a transcript, the host's or Keel's copy, counts: one that was never given a prompt has none, takes no slot, and stays (#401). A session is the role's when it ran in one of the role's worktrees, or when Keel keeps its transcript under the role, so a renamed or moved worktree does not strand its old sessions (#462). A takeover Keel did not carry out — a session you opened by hand that runs `keel shift resume` — removes them the same way: resuming a note a CLI session wrote, from a Claude Code session, removes the role's old sessions under the same rules and names them (#462). Nothing is lost: `claude rm` leaves the host's transcript, Keel keeps its own copy, and `keel shift history <role> --show <session id>` prints the whole conversation of any shift, listed or not.

`keel shift status` lists each hand-off as pending, delivered (with the new session's id) or failed (with the error), and how to reopen the old session: `claude attach <first 8 characters of its id>`, or, once it has been removed, `keel shift history <role> --show <id>`. It also names the older sessions the hand-over removed. A hand-off that failed, or is still pending after 15 minutes, is a patrol risk, so the coordinator hears of it. `keel tick` tries a failed start again, up to three attempts in all, and after the last one status names `keel chat wake now <role>`, which resumes the stopped old session. A worktree nobody trusted is one way to fail: the new session cannot start there.

On the CLI, `keel shift resume` asks for nothing to be restored: the new session already carries the role's name, and the desktop steps that `self-shift` and `shift-restore` authorize do not apply.

## Permissions

The tick runs outside every session and needs no session permission. The sessions themselves run `keel` and `git` commands through Bash. A session started by a hand-off runs in the declared `permission_mode`, and a resumed session keeps the mode it was started with. So start each role's first session in the mode you want it to keep, and give it the `permissions.allow` entries its work needs, as you would for an unattended desktop session. The desktop-only entries (`mcp__ccd_session_mgmt__*`, `mcp__scheduled-tasks__*`) and the `self-shift` and `shift-restore` declarations are not needed.
