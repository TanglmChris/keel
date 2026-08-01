## Context

Keel's answers are worth reading because its checks are local, deterministic, and reproducible. Determinism is not the same as correctness: a check can be perfectly reproducible and reproducibly wrong, and a check that compares two names is reproducibly wrong exactly when the two names describe one thing.

Five such checks shipped. The write guard is the one that matters most, because it is the only mechanism that enforces anything at write time; the rest of the protocol's write discipline is convention that the guard is supposed to make real.

## Goals / Non-Goals

**Goals:**
- One file has one answer to "is this inside the repository", however it is spelled.
- A path Touch declares is attributed to Touch whatever bytes it contains.
- An environment component that is not the one the repository declares says so, rather than producing an answer about a different program.

**Non-Goals:**
- No new hook, no new gate, no new command. Every fix lands inside a check that already exists.
- Keel does not install or select an interpreter or an OpenSpec version. It reports, as 5.9.0 established for the plugin and CLI.
- Non-UTF-8 filenames are out of scope. Git stores bytes and Node hands back a string; `-z` removes the escaping problem, not the encoding one.

## Decisions

**F1** — `plugins/keel/scripts/pretooluse-guard.js:133` decides repository containment as `path.relative(repo, path.resolve(repo, target))`, where `repo` comes from `event.cwd` and `path.resolve` does not follow symlinks. Measured 2026-08-02 against a repository reached through a symlink, manifest active, Touch `src/allowed.js`: `<real>/src/denied.js` is denied and `<symlink>/src/denied.js` is allowed. The deny on the real path is the positive control — the guard is working, and only the symlinked route escapes. *Basis:* direct probe of the shipped hook.

**F2** — `src/core/helper.js:60` gets the same comparison wrong in the opposite direction. `process.cwd()` returns a realpath-resolved directory while `path.resolve(candidate)` does not, so on macOS `path.relative("/private/tmp/x/repo", "/tmp/x/repo/baseline.json")` is `"../../../../tmp/x/repo/baseline.json"` and `isExternal` answers true for a path inside the worktree. This is why `native-helper-read-only` is red locally and green on Linux CI. *Basis:* measured both sides; with `realpath` applied to both, the same inputs produce `"baseline.json"` and the correct answer.

**F3** — Measured git quoting, 2026-08-02. `git status --short` escapes a non-ASCII path to octal *and* wraps it in quotes; `-c core.quotepath=false` removes the octal but still quotes a path containing a space, a quote, or a backslash. `git diff --name-only` escapes non-ASCII but does **not** quote a space. The two commands the gate reads therefore disagree about when a path is quoted. `--porcelain=v1 -z` and `--name-only -z` emit raw bytes with no quoting or escaping in every one of those cases. *Basis:* fixture repository with four adversarial filenames plus a rename.

**F4** — `gitPaths` then runs `line.slice(3).trim().replace(/\\/g, "/")`. The `slice(3)` leaves the surrounding quotes and the `replace` turns `\346` into `/346`, which is the corruption issue #40 reports. Git emits forward slashes on every platform, so the replace normalizes a separator git never produces. *Basis:* source read plus the reproduction in #40.

**F5** — `bin/keel.js:647` prefers `node_modules/.bin/openspec` and otherwise falls back to PATH with no report. This repository has no `node_modules`, PATH holds openspec **1.4.1**, and `package-lock.json` resolves `@fission-ai/openspec` to **1.6.0**. `spec-template-validates` fails locally because 1.4.1 rejects a requirement the shipped template writes and 1.6.0 accepts it. *Basis:* measured `openspec --version`, read the lock.

**F6** — `scripts/run_python.js` accepts any candidate whose `--version` exits zero. The suite calls `tempfile.TemporaryDirectory(ignore_cleanup_errors=…)`, added in Python 3.10; macOS system `python3` is 3.9.6. Ten scenarios fail with messages naming ten unrelated features. *Basis:* issue #36's measurement, reconfirmed.

**F7** — In `-z` mode `git status --porcelain=v1` emits a rename as two NUL-terminated fields, `XY <new>` then a bare `<old>`. The order differs from the `R old -> new` line format. It is neutral here, because `gitPaths` attributes both endpoints independently. *Basis:* measured on a fixture rename whose new name contains both a space and non-ASCII characters.

**D1** — **Containment is decided on resolved paths, in one shared answer.** *Basis:* F1 and F2 are one defect reached from two call sites; fixing them separately would leave two implementations of a question that must not have two answers. The hook cannot import from `src/core` — it is a standalone script the host executes — so the shared thing is the rule and its tests, not a module. That is stated here so a later reader does not "unify" them into an import that would break the hook's independence.

**D2** — **Resolve the nearest existing ancestor, not the target.** *Basis:* the guarded target is usually a file about to be created, so `realpathSync` on it throws. Resolving the deepest existing ancestor and re-appending the remainder answers the same question and works for a path that does not exist yet. Getting this wrong denies legitimate writes, so it is checked in both directions.

**D3** — **A path that cannot be resolved at all falls back to the unresolved comparison.** *Basis:* the guard must not fail open on a symlink and must not fail closed on an unreadable directory. When no ancestor resolves, the old comparison is what remains, and the outcome is the behavior that shipped — no worse than today, and today is the floor.

**D4** — **Git is read with `-z`, not with `core.quotepath=false`.** *Basis:* F3. The flag suppresses octal escaping and leaves quoting, so a decoder would still be needed for spaces, quotes and backslashes, and the two commands do not quote the same cases. `-z` deletes the problem class instead of handling it. Issue #40 proposed the flag; this goes further for the reason its own "space in filename" suggestion implies.

**D5** — **`replace(/\\/g, "/")` is deleted from the git path readers.** *Basis:* F4. It defends against a Windows separator git does not emit and corrupts escapes that `-z` no longer produces. Leaving it would be harmless with `-z` and is still removed, because a line that cannot do anything but damage is a trap for the next reader.

**D6** — **`run_python.js` requires 3.10 and reports what it found.** *Basis:* F6. The minimum is the one the suite actually uses, not a guess; the message names each interpreter tried and the version it reported, so the reader's next action is installing one rather than debugging ten scenarios.

**D7** — **The OpenSpec binary is reported, not enforced.** `keel doctor` states the resolved command, its version, and the range the repository declares. Nothing refuses to run. *Basis:* 5.8.0's scope rule — Keel does not manage installs — and 5.9.0's precedent that a runtime mismatch is stated on the channel the person reads. Refusing would strand anyone deliberately testing against another version.

**D8** — **The validator asserts the OpenSpec version it is testing against.** *Basis:* F5. `keel doctor` helps a person who thinks to look; the suite is what runs unattended, and a suite that silently changes which program it exercises reports facts about something else. This converts one misleading spec-validation failure into one accurate version failure.

## Hidden Knowledge / Assumptions

**A1** — `event.cwd` is whatever the host supplies and may be either the resolved or the unresolved form. *Basis:* the hook has no control over it. *Owner:* the containment rule resolves both sides, so the answer no longer depends on which form arrives — asserted by driving the hook with the resolved cwd and the symlinked target and with the pair reversed.

**A2** — Node returns git's NUL-separated output as a UTF-8 string. *Basis:* `spawnSync(…, { encoding: "utf8" })`, and every path in the measured fixtures round-tripped exactly. *Owner:* the scenario asserts the Chinese filename from #40 byte for byte rather than by substring.

## Coupled Iteration Contract

Not required. No task in this change declares `Coupling: required`.

## Risks / Trade-offs

- **The containment fix changes what the guard denies.** A write allowed yesterday through a symlinked path is denied today. That is the point, but it lands without warning in a session whose repository is at such a path — and on macOS the default temp directory is one.
- **`realpath` on every guarded write costs a syscall** on a path the hook already touches. Measured cost is not the concern; a `realpath` that throws where the old code silently continued is, which is what D3 exists for.
- **Reading `-z` changes three parsers at once.** Each is small, but a mistake in the rename branch would silently drop an endpoint and turn a scope failure into a pass — the same shape as the defect this repository just spent a release fixing. The rename case is therefore asserted with both endpoints named and with characters that the old format would have escaped.
