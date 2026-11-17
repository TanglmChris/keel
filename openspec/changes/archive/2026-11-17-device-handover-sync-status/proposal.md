## Why

Issue #526 (filed from Keel 5.228.0, 2026-11-16; one repository on a Linux box, a Mac and a VPS): work that exists only on one machine is invisible to whoever takes over. Three unpushed commits sat on the VPS, a Mac worktree held finished-task changes plus an unrelated twin copy that would fork if both were continued, a push the remote hung up on mid-way was taken for done and a PR went out with part of its commits, and dozens of branches, nine worktrees and a stash had to be checked one by one. The owner's requirement, restated on 2026-11-16: switching devices must be seamless — GitHub is the only authority, and a device that takes over needs nothing from another machine.

Keel today reports part of this in one place only (`keel shift check`, for the current worktree), never confirms the remote's sha, has no cross-device notion of who is working on what, and keeps the shift note and role state in `<git common dir>/keel-chat/`, which exists on one machine only (the chat archive syncs `groups`, `cursors`, `members` and `presence`, not shift notes). `keel lock` is a local, cooperative file and cannot arbitrate between machines that are never online together.

## What Changes

Every part extends the Keel mechanism that already owns its concern (owner, 2026-11-16).

- **`keel lock` gains a branch lock that lives on GitHub.** `keel lock acquire --branch <b>` / `release --branch <b>` keep `keel lock`'s holder, renewal, waiters and chat messages, but the lease is the ref `refs/keel/lock/<b>`, updated only by a push without force, so git's fast-forward rule makes acquisition atomic across devices that are never online together. An expired lock is taken over with a warning of what the last holder recorded; a live one only with `--break` and a reason. Release requires the branch committed, pushed, and confirmed by the remote's real sha.
- **The hand-over note travels by the chat archive.** `keel shift ready` writes the note once under `shift-notes/`, which the archive now syncs, and releases the lock naming it. **`keel shift resume` is the takeover**: it switches the worktree to the branch at the previous holder's head, acquires the lock, pulls the archive and prints the note.
- **The sync points are enforced.** With `sync: lock: true`: `task-start` and `change-close` check the lock and the pushed state; `keel context` points `nextAction` at `keel lock acquire --branch` or `keel shift resume` when the lock is not this device's; the write guard refuses a session's push to a branch another device holds; the tick's hand-over does not start a session while another device holds the branch.
- **Pushing:** a new `device-sync` authorization lets Keel push lock refs only; work branches are pushed by Keel only where the existing `push` / `push:<glob>` allows, never `push-protected`, never forced, with the repository's hooks.
- **The Mac's tick and the prompt hook renew this device's leases**, and the tick pushes the held branch as `push` allows.
- **`keel sync status [--verify] [--json]`** lists every worktree, local branch and stash only on this machine, and each branch's lock, reusing `keel worktrees` and `keel branches` logic; `--verify` confirms the remote's real sha. `keel context` warns about local-only work, `keel shift check` treats this branch's stash as loose, `keel patrol` reports local-only work older than 24 hours once, and `keel --doctor` reports the locks.
- **Unchanged and said so:** work not yet committed is not carried across devices; a mid-task switch goes through `keel shift ready`.

## Capabilities

### New Capabilities
- `keel-sync-status`: the repository-wide local-only report, `--verify`, and the push guidance.

### Modified Capabilities
- `keel-resource-lock`: the branch lock, `sync:`, `device-sync` pushes, renewal, chat events, doctor.
- `keel-standing-authorization`: the closed vocabulary gains `device-sync`.
- `keel-core-gates`: one declared read; `task-start` and `change-close` check the lock and pushed state.
- `keel-stateless-continuity`: local-only warning and the lock next action.
- `keel-shift-change`: stash in the check, release in `ready`, takeover in `resume`, hand-over waits for the lock.
- `keel-chat-slack-bridge`: the archive carries `shift-notes/`.
- `keel-touch-write-guard`: a push to a branch another device holds is refused.
- `keel-coordinator-patrol`: old local-only work is a standing risk.

## Impact

`src/core/sync.js` (new), `src/core/lock.js`, `src/core/chat/archive.js`, `src/core/guard.js` or the guard script, `src/core/config.js`, `src/core/gates.js`, `src/core/context.js`, `src/core/shift.js`, `src/core/patrol.js`, `src/core/tick.js`, `src/core/chat/notice.js`, `bin/keel.js`, `scripts/validation/` (a new `sync.py` module and registry entries), the README and docs in both languages, `keel/config.yaml`, `AGENTS.md`, the nine published specs above, and the changelog. Risks: Keel gains its first unprompted pushes, which is why they sit behind a named authorization limited to three ref shapes; a lock is cooperative and cannot stop someone using git by hand, so git's own non-fast-forward refusal remains the last guard; GitHub's acceptance of `refs/keel/*` and device clocks are assumptions the tasks verify.
