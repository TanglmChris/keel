---
description: Change this session's own shift — check for loose ends, write the hand-off note, arm the wake
---

Change this session's shift: leave a note for the next one and let Keel start it. The mechanism is `keel shift`; this command only orders the steps. `docs/shift-change.md` in the Keel package says more when a step below is not enough.

## 1. Check for loose ends

```bash
keel shift check
```

Exit 0 means ready. Exit 1 lists items. Deal with each before going on, or stop and ask the owner when one is not yours to settle:

- Uncommitted changes, unpushed commits, a write guard, a lock lease, a linked worktree: commit and push, run `keel guard clear`, release the lease, or remove the worktree you made. Do not discard work to make the list empty.
- A process: tell the host's from yours. A keep-awake the host started under this session, such as `caffeinate -i -t 300`, ends by itself, so it may stay. A server, watcher or job you started is yours: stop it, or ask the owner before leaving it running.

Then act on the `memory:` note: recheck what this session wrote to memory, and remove what this shift made untrue or what the repository can answer. It never blocks the shift.

A shift in the middle of a task throws away working state that compaction would have kept. If the task is not at a boundary, say so to the owner before going on.

## 2. Write the hand-off note

The note is all the next shift has. Put in it:

- what you did, and where it lives: branch, worktree, PR, issue, file;
- the next step, concrete enough to start from;
- what you are waiting on, and what it unblocks;
- what you left running or uncommitted on purpose, and why.

Name commits and branches by id; `keel shift resume` checks them against the remote. Carry over what the owner already approved, because the next shift cannot ask this one.

## 3. Hand over

Use a quoted heredoc, so backticks in the note are not run. When step 1 listed only the host's own processes, add `--force-reason "<which process, and that the host owns it>"`.

```bash
keel shift ready --wake --file - <<'EOF'
<the note>
EOF
```

Read what it prints and do what it says for this host:

- Claude CLI background session: end your turn at once with one short line. A waiter replaces this session when it has finished, so do not start other work or ask the owner anything after `ready`: a session waiting on an answer is not replaced.
- Claude desktop app: it prints four steps. Take them without pausing when `keel/config.yaml` declares `self-shift` under `authorize:`, and ask the owner first when it does not.
- No chat role: `ready` is refused and names `keel chat role --set`. Bind a role first, or ask the owner who starts the new session.

The one line you end on names the note's path and where the next session starts.
