## Why

`keel gate task-complete` refuses a path written outside the selected task's `Touch` — but only when the caller supplies `--base`. Without it the whole comparison is skipped: the dirty paths are printed as a Warning and the gate returns `pass`. Measured 2026-08-02 at 5.15.0, on one tree and one task: `pass` with the offending path in a Warning, `fail` with `Changed path is outside Touch` once `--base HEAD` is added.

This was found by it happening. During the 5.15.0 release task a file was written that the task had not declared in `Touch`. The PreToolUse write guard never saw it, because the write went through a `python3` heredoc in Bash and the guard binds the host's file-writing tools rather than the shell. `task-complete` returned `pass`. A human reading `git status` during the semantic Scope check caught it.

Nobody reads `git status` in an unattended run. The repository's own design admits work into such runs through `triage:`, and the boundary that is supposed to hold there is the one that currently holds only when asked.

Refusing to attribute dirty paths without a trustworthy base is correct and stays: in a change that is half-finished, Git alone cannot say which task wrote a given path. But a trustworthy base for *this task* does not have to come from Git. `keel gate task-start` already writes the guard manifest at exactly the moment a task begins, and a manifest that also recorded what was dirty at that moment answers the question directly: dirty now, and not dirty then, means this task wrote it.

## What Changes

- The guard manifest records the working tree's dirty-path set at `task-start`, alongside the fingerprint and Touch it already records.
- `task-complete` derives its baseline from that record when no `--base` is given, and refuses a path that became dirty during the task and is outside `Touch`. **BREAKING**: a task that writes outside `Touch` now fails a gate that previously passed with a Warning.
- An explicit `--base` keeps precedence, so a caller who has a trustworthy Git ref still gets the Git comparison.
- A manifest carrying no recorded baseline — one written by 5.15.0 or earlier, or after `keel guard clear` — behaves exactly as today: dirty paths are reported and not attributed. Absence of a baseline is not evidence of a clean start.
- The unattributed-dirty Warning keeps its current shape. Shortening it (#53 item 6) is deliberately not bundled here — see design D5.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-core-gates`: `task-complete` gains a derived baseline and refuses out-of-Touch writes without requiring the caller to supply one. The existing prohibition on *automatic* attribution is narrowed to what it was protecting — inferring authorship from an untrustworthy base — rather than forbidding a baseline the gate recorded itself.
- `keel-touch-write-guard`: the manifest schema records the task-start dirty set, and the guard's relationship to writes it cannot intercept is stated: enforcement binds tool writes, and the completion gate is where a write the guard never saw is caught.

## Impact

- `src/core/guard.js`: `startGuard()` records the baseline; manifest shape validation accepts and checks it.
- `src/core/gates.js`: `attributionResult()` (`:565`) derives a baseline when `--base` is absent and a manifest baseline exists; the no-base Warning path narrows to the case where neither exists.
- `scripts/validate_plugin.py`: scenarios for the derived refusal, for `--base` precedence, and for the unchanged behavior of a baseline-less manifest.
- Risk: a path that becomes dirty during a task without the task writing it — a formatter, an `npm ci` rewriting `package-lock.json`, an editor autosave — now fails the gate. This is intended where the write is real and unauthorized; where it is not, the task's `Touch` is the wrong shape and the failure names the file. Build outputs are generally gitignored and never appear in `gitPaths`.
- Risk: a path already dirty at task start and further modified out of `Touch` by the task is not caught, because the baseline subtracts it. This is a known limit of a non-Git baseline and is recorded in design as A1 rather than hidden.
- No new dependency. The comparison stays local, offline, and deterministic.
