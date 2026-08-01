## Why

Keel checks names instead of things, in five places, and each one fails silently while looking exactly like a check that works.

The write guard is the sharpest. It decides whether a path is inside the repository by comparing two strings, one of which the operating system has already resolved and one of which it has not. Measured on 2026-08-02 against a repository reached through a symlink, with a live manifest whose Touch allowed `src/allowed.js`:

| write | guard |
|---|---|
| `<real>/src/denied.js` | **DENY** |
| `<symlink>/src/denied.js` | **ALLOW** |

The same file. One textual route escapes the only mechanism Keel has for enforcing a write boundary, and the manifest, the projection, and every gate look identical either way. `src/core/helper.js` gets the same answer wrong in the other direction, declaring a path inside the worktree to be outside it, so the helper writes a baseline into the repository it promised not to touch. On macOS `/tmp` is such a symlink by default, which is why the shipping `native-helper-read-only` scenario has been red locally and green in CI.

The other three are the same mistake on other kinds of name. Git escapes any path containing a non-ASCII byte, and the gate then runs `replace(/\\/g, "/")` over the escape sequences, so a task whose Touch names a Chinese filename cannot complete — reported as `outside-touch` for a path that is listed on the first line of Touch. `keel` resolves the `openspec` binary by asking PATH and silently accepts whatever answers, so this repository has been validating changes against openspec 1.4.1 while its lockfile pins 1.6.0. `run_python.js` accepts any interpreter whose `--version` exits zero, so a macOS system Python 3.9 runs a suite that needs 3.10 and fails ten scenarios with messages naming ten unrelated features.

None of these is a subtle bug. Each is a check that verified the form of a name and never the thing it names.

## What Changes

- **Repository containment resolves symlinks on both sides.** One shared answer to "is this path inside this repository", used by the write-guard hook and by the helper baseline check, comparing real paths rather than the two different strings that can name one file.
- **Git path output is read with `-z`.** Measured: `--porcelain=v1 -z` emits raw bytes with no quoting and no escaping, for non-ASCII, spaces, quotes and backslashes alike, while every other format C-quotes some of them and `--short` and `--name-only` do not even agree on which. Reading `-z` removes the decoding problem rather than adding a decoder, and it lets the `replace(/\\/g, "/")` that corrupts every escape be deleted — git emits forward slashes on every platform, so that line was defending against nothing while breaking something real.
- **The interpreter is checked, not assumed.** `run_python.js` requires the minimum version the suite actually needs and, when nothing meets it, says which interpreters it found and what each reported — one accurate failure instead of ten misleading ones.
- **The openspec binary names itself.** When the resolved `openspec` is not the one the repository declares, that is reported rather than absorbed. A change validating against a different tool version than the lockfile pins is a result about a different program.
- **Nothing new is silent.** Each of these replaces a silent wrong answer with a stated one, which is the same standard 5.9.0 applied to the plugin, the CLI, and the protocol version.

## Capabilities

### New Capabilities
<!-- None. Five shipped guarantees are made to hold. -->

### Modified Capabilities
- `keel-touch-write-guard`: repository containment is decided on resolved paths, so one file cannot be both inside and outside the guard depending on how it is spelled.
- `keel-core-gates`: git path output is read in a form that carries no escaping, so a path Touch declares is attributed to Touch whatever characters it contains.
- `keel-target-surface-diagnostics`: the interpreter and the OpenSpec binary that actually run are reported against what the repository requires.

## Impact

- **Code**: `plugins/keel/scripts/pretooluse-guard.js`, `src/core/helper.js`, `src/core/gates.js`, `src/core/context.js`, `scripts/run_python.js`, `bin/keel.js`, and the validator scenarios covering each.
- **Closes**: #40 entirely, #36 entirely, and the L2 cross-platform half of #38.
- **Behavior change**: a write the guard previously allowed through a symlinked path is now denied. That is the fix, and it can surprise a session already running against such a path.
- **Risk**: `realpath` fails on a path that does not exist yet, which is the normal case for a file about to be written. The containment check must resolve the nearest existing ancestor rather than the target, and getting that wrong would deny legitimate writes. This is the single thing here most worth testing hard, in both directions.
- **Cost**: `realpathSync` per guarded write, on a path the hook is already stat-ing. `-z` parsing replaces line splitting at the same three call sites.
- **Dependencies**: none added.
