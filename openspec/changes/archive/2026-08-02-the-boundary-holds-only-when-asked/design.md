## Context

Two mechanisms are supposed to keep a task inside its declared `Touch`. The PreToolUse write guard refuses a write before it lands; `keel gate task-complete` refuses a change that landed anyway. The first binds the host's file-writing tools and cannot bind a shell, which is not a bug and is not fixable — what a `python3` heredoc will write cannot be decided before it runs. The second is therefore the boundary that has to hold, and it currently holds only when the caller passes `--base`.

`keel-core-gates` states the conservatism deliberately: "Keel MUST NOT attribute dirty paths to a selected task unless the caller supplies a trustworthy comparison base." The reasoning behind it is sound and is not what this change disputes. What it disputes is the assumption that a trustworthy base can only come from the caller.

## Goals / Non-Goals

**Goals:**
- A write that lands outside `Touch` fails the completion gate without the caller having to ask for the check.
- The baseline is derived from a record Keel made itself, at a moment whose meaning is unambiguous.
- The existing conservatism is preserved where it applies: with no record and no `--base`, nothing is attributed.
- A caller who supplies `--base` keeps the Git comparison unchanged.

**Non-Goals:**
- Preventing the write. The guard binds tool writes; a shell writes underneath it, and no hook can decide in advance what a command will touch.
- Inferring authorship between tasks. The baseline answers "did this task write it", not "which task wrote it"; the existing completed-sibling exclusion and its warning stay exactly as they are.
- Making `keel/guard.json` durable authority. It stays disposable local state; a lost manifest degrades to today's behavior rather than blocking.

## Decisions

- **F1** — the out-of-Touch refusal already exists in full and is skipped wholesale without a base. `attributionResult()` opens with `if (!base) { return { problems: [], warnings: [dirty paths listed] } }`; everything below it — the diff, the union with `gitPaths()`, the `pathAllowed` filter, the `problem("outside-touch", …)` construction — is unreachable in the default call. *Basis: `src/core/gates.js:565-645`.*
- **F2** — measured 2026-08-02 at 5.15.0 on one tree, one task, one deliberate out-of-Touch write: `task-complete` returned `Status: pass` with `Warning: Working-tree paths are dirty but not attributed without an explicit base: README.md`, and `task-complete --base HEAD` returned `Status: fail` with `Problem: Changed path is outside Touch: README.md`. *Basis: direct execution in a scratch checkout with the change restored live.*
- **F3** — `startGuard()` writes the manifest at the moment a task is authorized, and already records `change`, `task`, `fingerprint`, `touch`, and an `authority` hash list. Adding a recorded dirty set costs one field in a file that is already written at the right instant. *Basis: `src/core/guard.js:184-199`.*
- **F4** — `gitPaths(repo)` already produces the dirty set the baseline needs, with `-z` handling and both endpoints of a rename attributed. The baseline and the comparison therefore read the same function, and cannot disagree about what "dirty" means. *Basis: `src/core/gates.js:490-510`.*
- **F5** — the write that motivated this change was invisible to the guard because it came from Bash. The guard's own status output already says it cannot observe enforcement; what was missing is that the completion gate did not compensate. *Basis: the 5.15.0 release task's Review, archived at `openspec/changes/archive/2026-08-02-doctor-answers-for-the-repo-it-names/tasks.md`.*
- **D1** — the baseline is the dirty-path set recorded at `task-start`, and a path is attributed to the task when it is dirty now and was not dirty then. Not a Git ref: the case that needs covering is a half-finished change whose worktree is already dirty, which is exactly where a Git ref stops being trustworthy. *Basis: F3, F4, and the reasoning `keel-core-gates` gives for refusing untrustworthy bases.*
- **D2** — an attributed out-of-Touch path is a `fail`, matching what `--base` produces today. A warning would leave the gap this change exists to close: in an unattended run nobody reads warnings, and that is how the motivating write survived a passing gate. *Basis: F5; user decision 2026-08-02, taken with the upgrade cost stated.*
- **D3** — an explicit `--base` keeps precedence over the recorded baseline. A caller who has a trustworthy ref is asking a broader question — everything since that commit, not only since this task started — and the gate should answer the question asked. *Basis: the two baselines answer different questions, and silently substituting one would make `--base` mean something other than what it says.*
- **D4** — a manifest with no recorded baseline behaves exactly as today. Manifests written by 5.15.0 and earlier have no such field, and `keel guard clear` removes the manifest entirely. Treating a missing record as "nothing was dirty at start" would attribute the whole worktree to the task and fail every completion in a dirty repository. Absence of a record is not a record of absence. *Basis: D1 — the baseline is only meaningful when it was actually taken.*
- **D5** — the unattributed-dirty warning keeps enumerating every path. Shortening it to a count was considered and dropped: it comes from #53 item 6, which is a token-cost concern rather than a boundary one, and the full list is currently load-bearing as an observation channel — `git-paths-carry-no-escaping` reads a rename's two endpoints out of that warning precisely because a base comparison would report them itself and hide a dropped endpoint. Changing the warning's shape inside a change about authority would couple an output-size question to a correctness one. *Basis: `scripts/validate_plugin.py:6219`; the concern stays open on https://github.com/TanglmChris/keel/issues/53.*

## Hidden Knowledge / Assumptions

- **A1** — a path that was already dirty when the task started, and is then modified again outside `Touch` by the task, is not attributed. Subtracting the start set is what removes the false-positive class that made automatic attribution unsafe, and it necessarily removes this true positive with it. The alternative — recording content hashes of every dirty path at start — makes `task-start` cost proportional to the worktree and turns a disposable pointer into a snapshot store. *Basis: D1. Owner: this change records the limit in the `keel-core-gates` requirement text, so a reader learns it from the spec rather than from a missed write; `--base` remains available for the caller who needs the stronger comparison.*
- **A2** — the paths Keel itself writes between `task-start` and `task-complete` must not be attributed to the task. `keel/guard.json`, the change's own authoring directory, and completed siblings' Touch entries are already excluded by name in `attributionResult()`, and the recorded baseline is taken before the manifest is written, so the manifest cannot appear as a task-authored path. *Basis: `src/core/gates.js:612-620`; verified by the scenarios this change adds.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- A legitimate but undeclared write now fails where it previously passed. That is the intent, and the failure names the file, so the fix is either adding it to `Touch` and reauthorizing or reporting an Out-of-scope Need — both of which the protocol already defines. The upgrade cost was stated and accepted before implementation.
- A tool outside the task's control that dirties a tracked path mid-task — a formatter on save, `npm ci` rewriting `package-lock.json` — produces a failure naming that path. Build outputs are generally gitignored and never reach `gitPaths`. Where the write is real, failing is correct; the gate is reporting what the worktree says.
- The manifest grows by one array. It stays disposable, stays gitignored, and a lost or cleared manifest degrades to today's behavior (D4) rather than to a failure.

## Open Questions

None.
