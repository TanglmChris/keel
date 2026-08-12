## Why

`#93` measured that `keel/config.yaml`'s `authorize:` vocabulary (`commit`, `push`, `release`,
`archive`) does not include `sync`, while `keel gate change-close --action sync|archive` accepts
it as a value beside `archive`. A reader who writes an `authorize:` declaration after reading
`--help` sees `sync` and `archive` presented as two options of the same flag and, reasonably,
copies both into the list — but only `archive` is a name `authorize:` accepts. The result is a
declaration that fails closed exactly as designed (`keel --doctor` reports `authorize: failed`
and the whole block authorizes nothing), except the failure is silent everywhere except
`--doctor`, an explicitly-invoked diagnostic. `#93`'s own repro shows the same broken declaration
sitting uncaught for eight days: `keel context`, the command `AGENTS.md` requires at the start of
every session, said nothing about it.

`#93` names three candidate directions and takes no position among them, leaving the choice to
the owner. This repository already has a standing answer to the first: `scripts/
validate_plugin.py`'s `sync-surface-overlay` scenario (M4, `#54`) asserts that `keel/
config.yaml` itself never adds `sync` to its own `authorize:` list, with the rationale "naming
the gate that governs an action and deciding whether a repository may authorize it once are
separate." Widening the vocabulary to accept `sync` is therefore not this change's decision to
make — it would reopen a question this codebase has already answered once, in the direction of
keeping the two lists distinct. What is left, and squarely in `#93`'s other two candidates, is a
diagnostic-clarity fix: name the confusion where it happens, and say it in the surface a session
actually reads first.

## What Changes

- The `authorize:` unrecognized-action message — printed by `keel --doctor` and, new in this
  change, by `keel context` — gains one additional sentence exactly when `sync` is among the
  unrecognized entries: it names `sync` as a `change-close --action` value rather than an
  `authorize:` name, and points at `archive` as the name to declare if the intent was to
  authorize that gate. Every other unrecognized-action message (a genuine typo like `deploy`) is
  unchanged.
- `keel context` — the command a session runs first, per `AGENTS.md` — now reports a broken
  `authorize:` declaration as a `Warning:` line, carrying the same message `--doctor` already
  prints. Today `keel context` says nothing about it at all; the only way to learn the
  declaration is dead is to separately run `keel --doctor`.
- The accepted `authorize:` vocabulary itself does not change. `sync` is not added. This is a
  message and a surface change only.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-standing-authorization`: the existing "An unrecognized action name is reported, not
  granted" Requirement gains a scenario naming the `sync`/`change-close --action` confusion
  specifically, and a second scenario establishing that `keel context` reports the same failure
  a session would otherwise only see by separately running `--doctor`.

## Impact

- `src/core/config.js` — `readStandingAuthorization` gains a `message` field (null when the
  declaration is clean), computed by one new helper function. No change to `declared` or
  `unknown`, and no change to `STANDING_AUTHORIZATION_ACTIONS`.
- `bin/keel.js` — `printStandingAuthorizationSurface` uses the new `message` field instead of
  building its own string inline. The doctor output for a genuine typo (e.g. `deploy`) is
  unchanged text; only the `sync` case gains a sentence.
- `src/core/context.js` — `resolveContext` reads the same declaration and pushes a `Warning:`
  line when it is broken. No change to `status`, `nextAction`, or `selection` — a broken
  `authorize:` declaration is orthogonal to which OpenSpec task is selected next, exactly as an
  uncommitted git path is today.
