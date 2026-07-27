## Why

**The guard denies what the completion gate already forgives.**

`keel-core-gates` states the rule plainly: `keel/guard.json` and changed paths under the selected change's own `openspec/changes/<change>/` directory "MUST NOT be attributed as outside-Touch scope failures" — they are the authoring artifacts the gate is completing against. `task-complete` implements exactly that.

The write guard does not. It denies any file-edit outside the declared Touch list, and it denies any edit at all once the byte hash of a recorded authority file moves — and its authority list always includes `openspec/changes/<change>/tasks.md`. So a task that writes its own Evidence, or ticks its own checkbox, is stopped by the guard for doing the one thing the completion gate is waiting for it to do.

Issue #8 reports both halves:

- Ticking `- [ ]` to `- [x]` — inside Touch, when the author declared `tasks.md` — trips `authority drift detected`, and the rest of the task's Evidence cannot be written. The two offered exits are reauthorizing a task that is already finished, or clearing the guard. Only the second works.
- Not declaring `tasks.md` is *easier*, because then the author clears the guard from the start. Declaring it — the more careful act — produces the worse experience.

The 2026-07-27 dogfood comment on that issue widened it: **five** full reauthorization cycles in nine tasks, all triggered by paths that could not have been known in advance, because they are records the work produces rather than product the work changes.

Issue #8's second example is separate: a task whose whole effect is a repository-level action — the repository's first commit — has no legitimate `Touch`. It writes no worktree file, so there is no concrete path; it is not `diagnose-only`, because it has real side effects that need evidence; and `Touch: none` is rejected for any other mode.

## What Changes

- Give the write guard the same record-write rule the completion gate already has: the guarded change's own `openspec/changes/<change>/` directory is writable without being declared, and changes under it do not count as authority drift.
- Keep contract drift fully enforced. The capsule fingerprint excludes Evidence values and the checkbox by construction, so `keel guard status` and `keel gate task-complete` still hard-stop on a real contract change — a moved Touch, Verify, Covers, or boundary — recorded in the same file.
- Add `Mode: repo-action` for a task whose effect is an authorized repository-level action rather than a worktree write. It requires `Touch: none`, prohibits product writes like `diagnose-only`, and unlike every other mode is not prohibited from committing.

Out of scope: `keel/archive/**` stays a declared path. Issue #8's comment proposed making it a record write too, but the reason it kept appearing undeclared was that `finding-owner` refused an issue URL and forced a local proxy note. That was issue #12, fixed in 5.2.4 — a finding now cites its issue directly, so nothing forces an undeclarable archive write. The archive tree is durable evidence, and `keel-core-gates` deliberately keeps it attributable. Recorded as a revisit trigger in design.md.

Also out of scope: issue #13 item 2, `task-complete --base HEAD` attributing the previous task's uncommitted work. It stays on #13.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-touch-write-guard`: the guarded change's own authoring directory becomes a record-write layer the guard permits and excludes from drift, matching the completion gate.
- `keel-task-capsule`: task modes gain `repo-action` for authorized repository-level actions with no worktree writes.

## Impact

- A task can write its own Evidence, Review, and checkbox under an active guard. The bookkeeping half of the five reauthorization cycles disappears.
- Declaring `tasks.md` in Touch stops being a trap; it becomes unnecessary.
- A task whose effect is a commit or a tag has a legal contract instead of a Touch entry chosen to satisfy the validator.
- No loss of enforcement: product writes outside Touch are still denied, real authority edits outside the change directory still deny, and contract drift still hard-stops through the fingerprint.
- No manifest schema change, so a session running an older plugin hook against a newer CLI behaves exactly as it does today rather than failing closed.
