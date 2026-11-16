## Context

GitHub is meant to be the authority a session on any machine can pick up from. Aligned with the owner on 2026-11-16: all four directions of #526; Keel may push by itself under a named authorization limited to a few ref shapes; verification of a push uses the remote's real sha, optionally networked; **the sync points are task boundaries and hand-over, where a device finishes its work and then pushes, and the exclusion between devices is a lock**; an expired lock may be taken over automatically with a warning, a live one only by `--break`. Work not yet committed is deliberately not carried (the owner's "do the work, then push" rule); a mid-task switch goes through `keel shift ready`.

## Goals / Non-Goals

**Goals:**
- A device takes over by running one command and has the previous device's finished work and its hand-over note, with nothing needed from the other machine.
- Two devices cannot both believe they hold the same branch, though they are never online together.
- "Pushed" is confirmed against the remote's real sha.

**Non-Goals:**
- No snapshot of uncommitted work, no auto-commit by Keel.
- Keel never forces a push, creates a tag, or deletes a remote ref; it pushes a work branch only where `push` already allows it.
- No cross-machine inventory: each machine reports on its own repository.
- The lock enforces nothing on git by hand; it governs Keel's own flow and gates.
- `keel lock`'s local leases keep their behavior; the branch lock is a new resource kind in the same command.

## Facts

- F1 — `check()` in `src/core/shift.js` reports uncommitted paths and `git log HEAD --not --remotes` commits as items; it reads no stash, no other worktree or branch, no remote sha, and no lock (read 2026-11-16).
- F2 — `gitWarnings()` in `src/core/context.js` reports uncommitted paths of the current worktree only; `keel worktrees` is read-only and never fetches and lists neither branches without a worktree nor stashes.
- F3 — `openspec/specs/keel-core-gates` requires core gates to run "without network access or model calls", and `task-start` and `change-close` write nothing to the project except the `--record` anchor and the guard manifest.
- F4 — `authorize:` accepts `commit`, `push`, `push:<glob>[@role]` and other names; **`sync` is reserved**: `keel-standing-authorization` requires an `authorize:` entry `sync` to be reported with the hint that `sync` is a `change-close --action` value. The new name is therefore `device-sync`.
- F5 — `src/core/lock.js` keeps `keel lock` leases as files under `<git common dir>/keel-chat/locks/`, with a statement that they enforce nothing; they are invisible to other machines.
- F6 — The shift note lives at `keel-chat/shift/<role>.md` in the common dir and `roles.json` binds a role to a worktree path there; `keel chat archive` syncs only `groups`, `cursors`, `members` and `presence` to the orphan `keel-chat` branch (`SYNCED_ROOTS` in `src/core/chat/archive.js`). A takeover on another machine therefore has no shift note today.
- F12 — `keel lock` (`src/core/lock.js`, spec `keel-resource-lock`) already gives a holder identity (the worktree's role, else `worktree:<name>-<hash>`), exclusivity, renewal by the holder, waiters, and a direct chat message to waiters on release and expiry; its leases live in the local chat store.
- F13 — The chat archive merges two machines' `keel-chat` branches by the union of paths, so only files written once are safe to archive; `shift/<role>.md` is rewritten each shift and moved to history on resume (`src/core/shift.js`, `src/core/chat/archive.js`).
- F14 — The Claude write guard examines `git push` only while some `push:<glob>` is declared, determines the target branch from the refspec or the branch's push destination, and asks rather than refuses for `push-protected` branches (`keel-touch-write-guard`).
- F15 — `handOver()` in `src/core/shift.js`, run by `keel tick` and the hand-over waiter, starts a new CLI session in the role's worktree for each queued hand-off, recording `waiting_on` when it cannot act; the patrol already reports a hand-off pending over 15 minutes as a risk.
- F16 — `keel context` reports `nextAction` with a command (`nextActionCommand` in `src/core/context.js`); `keel-stateless-continuity` requires the command to be complete and never run by Keel.
- F17 — `keel shift resume` already marks each commit a note names as `already in origin/<default>`, `branch moved` or `branch gone` (`keel-shift-change`), and `keel worktrees` / `keel branches` already compute per-worktree upstream counts and remote containment (`src/core/worktrees.js`, `src/core/branches.js`).
- F18 — `keel --install --with-git-hooks` installs a `pre-push` hook running `fast_check`; any `git push` Keel makes runs it.

- F7 — The chat archive does not push a public repository unless `archive_public: "accept"` is set, deciding by `visibility(where)`, and treats an unconfirmed visibility as public (`pushDecision`, `src/core/chat/archive.js`).
- F8 — `tick()` in `src/core/tick.js` runs `git -C <worktree> fetch -q origin` before every due patrol and `keel patrol --repo <worktree> …` with the worktree as cwd; the launchd job runs from `/` (#524, 5.228.0), so nothing it starts may use the process cwd. The patrol's `result.standing` risks are sent once per distinct text by `sinceLast()` in `src/core/patrol.js` (#476).
- F9 — `src/core/worktrees.js` reads with `GIT_OPTIONAL_LOCKS=0`; `gitWarnings()` does not.
- F10 — A prompt-time hook already runs `keel chat hook user-prompt-submit` (`src/core/chat/notice.js`), on Claude only; Linux and a VPS have no `keel tick` (it only prints a launchd job).
- F11 — A push of a non-branch ref is atomic: `git push <remote> <sha>:refs/keel/lock/<b>` is accepted only when it creates the ref or fast-forwards it, and is otherwise rejected as non-fast-forward (git semantics, checked in task 2.1 against a bare repository). Whether GitHub accepts a custom `refs/keel/*` namespace is an assumption, A1.

## Decisions

Integration rule: every capability below extends the Keel mechanism that already owns its concern rather than adding a parallel one (owner, 2026-11-16).

- D1 — `src/core/sync.js` computes the local-only report and reuses `worktrees.js` (worktree listing and upstream counts) and the remote-containment test of `branches.js`; it is shared by `keel sync status`, `keel context`, `keel shift`, `keel patrol`. `src/core/lock.js` gains the branch lock. Every git call names its repository (`git -C` or `cwd`) and sets `GIT_OPTIONAL_LOCKS=0` (F8, F9).
- D2 — **Only on this machine**, offline: a branch whose tip no remote-tracking ref contains; a worktree with uncommitted or untracked paths, a detached head no remote ref contains, or such a branch; every stash entry.
- D3 — Offline by default, saying counts are as of the last fetch with its time (`FETCH_HEAD`'s mtime, or `never fetched`). `--verify` runs one `git ls-remote` per remote involved (upstream remote, else `origin`; `--remote` overrides), time-limited, never prompting, writing no ref, and classifies each branch `same`, `remote-behind`, `remote-ahead`, `diverged`, `unknown-to-local` or `not-on-remote`; a failed lookup is `cannot verify` and unverified.
- D4 — `keel sync status` exits 0 when nothing is local-only or unverified (`remote-ahead` counting as neither), 1 otherwise, 2 for an operational error.
- D5 — The report prints each fix and the `authorize:` entry covering it (`commit`; `push`/`push:<glob>` for a branch, whoever pushes it; `device-sync` for a lock ref), or the entry to declare. It runs nothing.
- D6 — **The branch lock is a `keel lock` resource.** `keel lock acquire --branch <b>`, `release --branch <b>` and `list` extend the existing command: the holder is `keel lock`'s identity (role, else worktree) with `@<device>` appended, `--for` defaults to the declared TTL and `--note` to `work on <b>`, and the lease is the ref `refs/keel/lock/<b>` on the branch's remote rather than a file. Each update is a commit whose parent is the lock commit observed after fetching that ref by explicit refspec, pushed without force, so of two devices acting on the same observed lock exactly one push is accepted. Message trailers: `keel-lock: held|released`, `Holder`, `Device`, `Seq`, `Expires`, `Head`, `Note` (the archived note path, D9), and `Took-over:` or `Broke: <holder> — <reason>`. Basis: F11, F12.
- D7 — State machine: no lock → create (Seq 1); `released` → acquire only if the local branch contains its `Head` and the remote branch tip; held by this device → renew (higher Seq, later Expires, as `keel lock` renews); held live by another device → refuse exit 1 naming holder, expiry, head; held but past `Expires` + grace → take over with `Took-over:`, printing the last `Head` beside the remote branch's sha. A live lock is taken only with `--break "<reason>"`. No force anywhere.
- D8 — TTL default 30 minutes (`sync: ttl:`), grace 5 minutes on the observer's clock; the holder judges its own lease by `Expires` with no grace (A2).
- D9 — **Release is the hand-over, and the note travels by the chat archive.** `keel lock release --branch <b>` requires the lock this device's and live, no uncommitted or untracked path, and one `ls-remote` showing the remote's branch sha equal to HEAD (or HEAD its ancestor locally), then pushes `released` with that `Head`. When a note is handed over (by `keel shift ready`), it is written once to `shift-notes/<role>/<UTC time>-<device>.md` in the chat store, `shift-notes` is added to the archive's synced roots, `keel chat archive sync` runs, and the lock's `Note` trailer names the path. Whether the archive pushes stays the archive's own rule (F7); when it does not, the release still succeeds and says the note stayed on this machine. Basis: F6, F7, F13.
- D10 — **Who pushes what.** `device-sync` authorizes Keel's commands to push the lock refs `refs/keel/lock/*` and nothing else. A work branch is pushed by Keel only where the existing `push` or a matching `push:<glob>` entry covers it and the branch is not `push-protected` (which needs a person's answer the tick cannot give, so it is skipped and reported once). Keel never forces, creates a tag, or deletes a ref. Every Keel push runs the repository's hooks (F18); a failing hook is reported once and the lease is left to lapse. Basis: F4, F14; owner decision 2026-11-16.
- D11 — `sync:` in `keel/config.yaml`: `lock` (boolean, default false) and `ttl` (`<n>m`/`<n>h`, 5 minutes to 24 hours, default 30m). Anything else is named by `keel context` and `keel --doctor` and the declaration behaves as absent. Without `lock: true` no gate, guard, check, hook, hand-over or next action changes; the commands still work when invoked.
- D12 — **Gates only read.** With `sync: lock: true`, `task-start` and `change-close` make one `git ls-remote` for the branch and its lock ref and fail unless the remote lock is the commit this device last pushed, `held` by it and unexpired by its own `Expires`, and the remote branch sha equals HEAD or has HEAD as an ancestor locally; `change-close` also fails on any uncommitted path and unless the remote sha equals HEAD. Failures name the fix (`keel lock acquire --branch <b>`, `git push`, `git fetch`). No remote passes with a warning. `task-complete` is unchanged. Gates never acquire, renew, release or push.
- D13 — **Renewal.** `keel lock acquire --branch <b>` by the holder renews; Keel calls it from `keel tick` for every branch lock this device holds whose worktree exists, followed by the branch push D10 allows, and from the prompt-time hook when more than a third of the TTL has passed since the last renewal, at most once per interval and silently on failure (F10). A device that cannot renew lets the lease lapse.
- D14 — **Takeover is `keel shift resume`.** With the lock declared, `resume` finds the branch lock whose last holder's role is this worktree's role and that is released or expired — or the lock of the worktree's own branch — refuses over uncommitted paths, switches the worktree to that branch fast-forwarded to the remote tip, acquires the lock, runs `keel chat archive pull` and prints the note the lock's `Note` names when the local store has none, then marks the note's commits as it already does (F17). A live lock held elsewhere is refused naming the holder. A fresh device runs `keel chat role --set <role>` then `keel shift resume`.
- D15 — **Context.** One offline warning when D2 finds anything, naming `keel sync status`. With the lock declared and context otherwise `ready` with `task-start` or `task-complete` next, a branch lock not held live by this device (by the last fetched ref) makes `nextAction` `lock-acquire` with the command `keel lock acquire --branch <b>`, or `shift-resume` with `keel shift resume` when the lock is released or expired for this role; the selection and `status` are unchanged, and the reason names the holder. Basis: owner decision 2026-11-16 (item 7), F16.
- D16 — **Shift.** `keel shift check`: a stash of this worktree's branch is an item; other local-only work is a note naming `keel sync status`; a held branch lock is a note that `ready` releases it. `keel shift ready` appends the remaining local-only list to the note under `## Not on the remote at hand-over` and, with the lock declared, releases as D9 and refuses, storing nothing, when release fails.
- D17 — **Hand-over waits for the lock.** With the lock declared, `handOver()` (tick and waiter) starts no new session for a role whose worktree's branch lock, by the last fetched ref, is held live by another device: it records `waiting_on: branch <b> is held by <holder>` on the entry, which `keel shift status` and the existing pending-hand-off patrol risk already surface. Basis: F15.
- D18 — **The write guard knows the lock.** With `sync: lock: true`, the Claude write guard denies a session's `git push` whose determinable target branch has a last-fetched lock held live by another device, naming the holder and `keel lock acquire --branch <b>`, whether or not any `push:<glob>` is declared; a target it cannot determine is left to the existing rules. Basis: F14.
- D19 — **Lock events reach the other roles through the chat.** Acquire, release, take-over and break post one record to the holder's and the previous holder's roles, and a refused acquisition records the requester as a waiter the way `keel lock` does and messages it on release; the records travel across machines only where the archive or Slack bridge already carries the chat. Basis: F12.
- D20 — **Patrol.** One standing risk per covered item holding work only on this machine for more than 24 hours (oldest commit no remote ref contains; stash by reflog time), text without count or age, sent once by `--since-last`; uncommitted paths excluded (A3).
- D21 — **Doctor.** `keel --doctor` prints a `sync` line: the declaration, this device's id, each branch lock it holds with expiry and last renewal, and whether the tick or the hook renews here.
- D22 — Device id: a random 8-hex id with the host name, written once to `<git common dir>/keel-chat/device.json`; it names a machine and is not a secret.

## Hidden Knowledge / Assumptions

- A1 — GitHub accepts pushes to `refs/keel/lock/*`. Basis: GitHub stores arbitrary refs (`refs/pull/*`); unverified for pushes. Resolve by: task 2.1, a diagnose-only probe with a throwaway ref the owner authorizes at that task's start; a refusal returns to authoring (fallback `refs/heads/keel-lock/<b>`).
- A2 — Non-material: device clocks agree within the 5-minute grace; a larger skew costs a takeover warning or a refusal, never a silent double hold, since every update must fast-forward.
- A3 — Non-material: 24 hours, fixed, for the patrol's local-only risk.
- A4 — Non-material: the upstream remote, else `origin`, is the lock's remote; `--remote` covers another name.

## Coupled Iteration Contract

Not required: no task declares `Coupling: required`.

## Risks / Trade-offs

- Keel's first unprompted pushes. Contained by a named authorization, three ref shapes, fast-forward only, and refusal rather than fallback when it is undeclared.
- A lock cannot stop `git push` by hand to the same branch; git's own non-fast-forward refusal and the audit chain are the remaining guards. Said in the documentation.
- A holder that sleeps past the TTL loses the lease while still working; its next gate fails by name and its next push is rejected if another device has moved the branch. The unrenewed window is bounded by the TTL.
- Network and credentials: a launchd tick has what its existing `fetch` has; a push credential missing there fails the renewal visibly, not silently.
- Uncommitted work is lost with a lost device. Stated in the proposal and in the takeover output.
- The shift note is published only as the chat archive already publishes (F7).

## Open Questions

None.

## Release validation supplement (owner approved 2026-11-16)

- F19 — The first complete run found that `bump_version.js` and the baseline marker scan descend into `.claude/worktrees/keel-maint-cli`. The bump changed eleven marker-only lines in that independent checkout; all other bytes match its HEAD. On this Linux host, orphan children are adopted by an ancestor subreaper (observed parent PID 1579), so the existing ancestor-parent keep-awake exclusion hides the orphan even though its original process-group leader has exited.
- D23 — Treat a nested directory containing `.git` as a different checkout in release marker writes and reads; still scan the outer checkout's own .claude/.codex surfaces. Restore the eleven proven accidental marker changes only. Do not exempt a keep-awake whose process-group leader is gone merely because a host subreaper adopted it. Prove the release boundary with a temporary real Git checkout and the actual bump/baseline, and the Linux behavior with the existing public shift-check regression.
