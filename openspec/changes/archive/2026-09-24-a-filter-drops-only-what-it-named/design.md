## Context

Two scenarios construct "a PATH with no `openspec` on it" and both do it by dropping whole
directories. The construction predates the layout that breaks it; the hazard it guards
against — losing `node` along with `openspec` — is named in the scenario's own comment,
guarded at the "empty the PATH" granularity, and reintroduced at the directory
granularity.

The fix is small. What needs deciding is how the sanitized PATH is built so that it
removes exactly the file it names, and how a scenario that ends up without its interpreter
reports that fact.

## Goals / Non-Goals

**Goals:**

- `npm test` passes on a host where `node` and a global `openspec` share a bin directory,
  and keeps passing where they do not.
- A scenario that cannot run because its own fixture removed the interpreter says so,
  naming `node`, through the existing skip contract.
- The defect is provable on any host, including one where the two binaries never shared a
  directory.

**Non-Goals:**

- Changing what the two scenarios assert about OpenSpec resolution. Their subject is
  unchanged; only the environment they build is.
- Making `resolve_openspec` / `run_openspec` PATH-aware in some new way. `resolve_openspec`
  deliberately prefers `node_modules/.bin` over PATH and that ordering is the behavior
  under test in `a-declared-dependency-is-resolved`.
- A general PATH-sanitization facility for arbitrary tools. One helper, one tool name, two
  call sites.

## Decisions

- **F1** — Both call sites carry the same predicate, written twice:
  `scripts/validate_plugin.py:5524-5533` (`a-declared-dependency-is-resolved`) and
  `:24664-24672` (`the-dependency-resolves-where-npm-put-it`, as `clean_env`). Basis: read
  at 955c0ea, 2026-09-24; `grep -n '"openspec").exists()'` returns exactly those two.
- **F2** — On this host `/opt/homebrew/bin` holds both `node` and `openspec`, and it is the
  only one of 17 PATH entries the predicate drops. Basis: measured 2026-09-24.
- **F3** — The observed failures are the two the issue names and no others; every other
  scenario in `--all` is green. Basis: `npm test` at 955c0ea, 2026-09-24 —
  `validation --all failed for: the-dependency-resolves-where-npm-put-it,
  a-declared-dependency-is-resolved`.
- **F4** — `a-declared-dependency-is-resolved` fails at the *version* assertion with
  `exit=127 out=''`: `resolve_openspec` returns `node_modules/.bin/openspec` (a file, so
  PATH is never consulted), and that shim's `#!/usr/bin/env node` cannot find an
  interpreter. So the failing subject is `node`, and the sentence printed names `openspec`.
  Basis: read `resolve_openspec` at `:14046`; reproduced 2026-09-24.
- **F5** — `the-dependency-resolves-where-npm-put-it` does not fail through `report()` at
  all; it raises `FileNotFoundError: [Errno 2] No such file or directory: 'node'` out of
  `subprocess.run`, because `subprocess` resolves the program from the *passed* env's PATH.
  Basis: reproduced 2026-09-24, traceback at `:24678`.
- **F6** — The skip contract already exists and is enforced: `skip_scenario(label, reason)`
  returns `SKIPPED` (3) at `:27904`, and `runner-skip-accounting` asserts that a skip is
  named, counted separately, and does not fail the run. `a-declared-dependency-is-resolved`
  already uses `return 3` for an absent `node_modules/.bin/openspec`. Basis: read at
  955c0ea.
- **D1** — Replace the directory in place with a symlink mirror, rather than dropping it.
  For each PATH entry that contains an `openspec`, create a temporary directory that
  symlinks every entry of the original except the `openspec` ones, and substitute it at the
  same index. Order and position are preserved, so a scenario that depends on "nearest
  wins" is unaffected. Basis: it is the only option that removes one file without removing
  its neighbours. Cost measured on the affected directory: 131 symlinks in 6 ms (F2), so
  the mirror is not worth narrowing to a hand-listed set of tools — a hand-listed set is
  also wrong the first time a scenario needs a tool nobody listed.
- **D2** — The alternative, a shim directory whose `openspec` exits 127, is rejected. Both
  scenarios assert that `openspec` does **not resolve**; a shim resolves. In
  `a-declared-dependency-is-resolved` the shim would additionally be a *candidate* the
  scenario could pick up instead of the declared dependency, which inverts the property
  under test. Basis: the scenario's own precondition check,
  `shutil.which("openspec", path=...) is not None -> fail`.
- **D3** — Exclude by stem, not by exact name. The mirror omits any entry whose stem is
  `openspec` (`openspec`, `openspec.cmd`, `openspec.ps1`, `openspec.exe`). Directory
  dropping removed the siblings for free; a mirror that copied `openspec.cmd` through would
  leave the tool resolvable on Windows, where `shutil.which` consults `PATHEXT`. Basis: the
  predicate under replacement tests only `openspec`, so this is a property the old
  mechanism had implicitly and the new one must state.
- **D4** — Assert the precondition, and report it as a skip naming the missing runtime.
  After building the PATH, each scenario checks that `node` resolves on it. If it does not,
  the fixture is broken and the scenario returns the skip contract with a reason naming
  `node` — never a failure attributed to `openspec`. Basis: F4/F5 show both failure texts
  point at the wrong subject; F6 shows the contract already exists and is accounted for.
  This is a net, not the fix: on an affected host the expected post-change outcome is
  **pass**.
- **D5** — The regression is proven on a synthetic shared-bin fixture, not on this host.
  The new scenario builds a directory holding both a fake `node` and a fake `openspec`,
  puts it on a PATH, and asserts against the helper's output. The defect is a layout, so
  the assertion builds the layout — the same reasoning the `#129` comment at `:24626`
  records for the hoisted-dependency fixture. A scenario that could only fail on a Homebrew
  host is a scenario CI never runs.
- **D6** — The new scenario asserts both sides. That `node` survives is the regression
  guard; that `openspec` no longer resolves is the positive control. A check whose passing
  condition is that something is *absent* is also satisfied by the mechanism being broken —
  a mirror that produced an empty directory would pass an `openspec`-is-gone assertion
  perfectly. Basis: precedent `an-assertion-that-never-failed-proves-nothing`
  (`../decision-precedents`, status `recorded`) names absence and agreement as the two
  passing conditions that need a positive control; and
  `keel-validation-runner / A narrowed refusal is asserted from both sides` already requires
  the same shape of the suite.

## Hidden Knowledge / Assumptions

- **A1** — Symlink creation can be refused on Windows without the developer-mode/privilege
  bit. The mirror falls back to omitting the directory, which is today's behavior, and D4's
  precondition check then turns the consequence into a named skip instead of a
  misattributed failure. Basis: `os.symlink` raises `OSError` there; Keel's suite already
  branches on `os.name == "nt"` for the same tool's shim shape at `:24640`. Not verified on
  a Windows host in this change — CI runs the suite on POSIX. **Durable owner:** the
  fallback plus D4's skip means the worst case on Windows is the status quo plus an honest
  message, so no separate owner is needed; if a Windows runner is ever added, the mirror
  path is the thing to re-measure.
- **A2** — The layout that triggers this is not Windows-shaped: `npm install -g` writes its
  shims to `%APPDATA%\npm` while `node.exe` lives in `C:\Program Files\nodejs`, so the two
  do not share a directory there. Basis: npm's documented global prefix on Windows; not
  measured on a Windows host. Consequence if wrong: A1's fallback applies, which is the
  current behavior plus a named skip — strictly better than today, never worse.

## Risks / Trade-offs

- **The mirror is a temporary directory with a lifetime.** Both scenarios must keep it
  alive for as long as the sanitized PATH is used. `the-dependency-resolves-where-npm-put-it`
  calls `clean_env()` repeatedly inside one `TemporaryDirectory` block and then runs
  children against it, so the mirror's cleanup has to outlive the last child, not the call
  that built the env. Mitigation: the helper returns a context manager, and each scenario
  holds it open across all of its child processes.
- **A mirror hides a pathological PATH entry.** A directory that is unreadable, or that
  contains an entry whose name cannot be symlinked, would previously have been carried
  through untouched; now it is only mirrored if it contains an `openspec`, and a failure
  there falls back to omitting it (A1). The blast radius is unchanged from today for every
  directory that does not contain the tool.
- **Two scenarios now share a helper**, so a defect in it fails both. That is the point —
  the duplicated predicate is why the same bug exists twice — but it means the helper's own
  scenario (D5) is the thing standing between a helper regression and two misattributed
  failures.

## Open Questions

None.
