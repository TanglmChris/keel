## Why

Two scenarios need an environment with "no `openspec` on PATH". Both build it the same
way — drop every PATH **directory** that contains an `openspec` entry:

```python
without["PATH"] = os.pathsep.join(
    entry
    for entry in os.environ.get("PATH", "").split(os.pathsep)
    if entry and not (Path(entry) / "openspec").exists()
)
```

On the default macOS layout — `node` from Homebrew, `openspec` from `npm install -g` —
that directory is one directory, and it holds both:

```
/opt/homebrew/bin/node     -> ../Cellar/node/26.0.0/bin/node
/opt/homebrew/bin/openspec -> ../lib/node_modules/@fission-ai/openspec/bin/openspec.js
```

So the filter takes `node` with it, and `npm test` fails two scenarios on an unmodified
checkout. Measured here on 5.60.0: 1 of 17 PATH entries is dropped, it is the one holding
the interpreter, and the run ends `validation --all failed for:
the-dependency-resolves-where-npm-put-it, a-declared-dependency-is-resolved` with every
other scenario green.

**The diagnostic names the wrong subject.** `a-declared-dependency-is-resolved` reports
`the resolved openspec did not report a version. exit=127 out=''` — 127 is the shim's
`#!/usr/bin/env node` failing to find an interpreter, but the sentence points at
`openspec`, which is installed, resolvable, and working. A reader who trusts it reinstalls
the thing that was never broken. The scenario that carries the real cause
(`FileNotFoundError: [Errno 2] No such file or directory: 'node'`) emits it as an
unhandled Python traceback rather than a scenario diagnostic, and its name is not the one
printed first.

The scenario's own comment shows the hazard was seen and guarded in its global form only:

```python
# `no openspec on PATH`, and nothing else removed. Emptying PATH outright
# would also remove `node`, and the openspec shim needs it — the scenario
# would then be asserting that a shell without an interpreter fails.
```

Directory granularity reintroduces exactly that. "Nothing else removed" is true of the
intent and false of the filter.

Why it is worth a change rather than a host workaround: this makes `npm test` unusable as
a completion check on an affected host. Every task whose `M<n>` is "`npm test` passes"
has to record an exception and a differential against `origin/main`, and a suite that is
known to be red stops being read — which is the same failure the two scenarios exist to
prevent, one level up.

## What Changes

- The sanitized PATH is built by **file, not by directory**. A directory holding an
  `openspec` is replaced in place — same position, same order — by a mirror directory
  that symlinks every entry except the `openspec` ones. `node` and everything else stay
  exactly where the scenario found them. Measured cost on the affected directory: 131
  symlinks, 6 ms.
- One helper serves both call sites (`validate_plugin.py:5524` and `:24664`), which today
  carry the same predicate written twice.
- The mirror excludes `openspec` **by stem**, so `openspec.cmd` / `openspec.ps1` / an
  extensioned sibling cannot survive a filter whose whole purpose is that the name does
  not resolve. Directory-dropping hid this; a mirror does not.
- Each scenario **asserts its own precondition before asserting the behavior**: if `node`
  is not resolvable on the PATH it just built, that is a broken fixture, and it reports
  the skip contract naming `node` — not a failure naming `openspec`. This is the split
  `a-declared-dependency-is-resolved` already enforces on `compact-task-authoring` (a tool
  never found and a tool that ran and refused are different facts), applied to its own
  fixture. It is a safety net, not the fix: on this host the expected outcome after the
  change is **pass**, not skip.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-validation-runner`: a scenario that constructs an environment removes only what it
  named, and verifies the precondition it depends on before asserting behavior — reporting
  a broken fixture as a skip that names the missing runtime.

## Impact

- `scripts/validate_plugin.py` — the shared helper, the two call sites, one new scenario.
- Fixes #137. Expected observable effect: `npm test` goes fully green on a host where
  `command -v node` and `command -v openspec` share a directory, and stays green where
  they do not.
- Symlink creation can be refused on Windows without the privilege. The mirror falls back
  to omitting the directory — today's behavior — and the precondition check then reports a
  skip naming `node` instead of the misattributed failure. Windows is not in fact the
  affected layout (`npm i -g` shims land in `%APPDATA%\npm`, `node.exe` in
  `C:\Program Files\nodejs`), so this path is the degradation, not the case.
