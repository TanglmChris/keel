## Context

`src/core/config.js`'s `readStandingAuthorization(repo)` (lines 154-166) already computes
`declared` and `unknown` from the `authorize:` block. `bin/keel.js`'s
`printStandingAuthorizationSurface` (lines 1631-1662) builds the doctor message inline from
`unknown` and `STANDING_AUTHORIZATION_ACTIONS` when `unknown.length > 0`, and is the only place
today that reports the failure. `src/core/context.js`'s `resolveContext` (lines 500-514) never
reads `authorize:` at all — `keel context`'s `warnings` array is populated only by
`gitWarnings(repo)`, uncommitted-path detection unrelated to this declaration.

`scripts/validate_plugin.py:15150` (`validate_standing_authorization_declaration_scenario`)
already exercises the unrecognized-action path with `deploy` as the offending entry (M3,
`STANDING_AUTHORIZATION_ACTIONS` mirrored locally as a tuple at line 15142), asserting the
offending name and all four accepted names appear in `keel --doctor`'s combined stdout+stderr,
that the exit code is non-zero, and that no action beside the bad one is granted. No test asserts
the message's exact text, so it can gain a sentence without breaking that scenario.

`scripts/validate_plugin.py:2510-2519` (inside `assert_target_overlays`'s caller, the
`sync-surface-overlay` scenario, `#54`) already asserts the opposite direction: that `keel/
config.yaml` in *this* repository never adds `sync` to its own `authorize:` list, with the
comment "Naming the gate that governs an action and deciding whether a repository may authorize
it once are separate." This is the existing precedent this change treats as settled — the fix is
diagnostic, not a vocabulary change.

## Goals / Non-Goals

**Goals:**

- Name the `sync`/`change-close --action` confusion inside the unrecognized-action message
  itself, exactly when `sync` is one of the unrecognized entries, so the message tells a reader
  what happened instead of leaving them to reverse-engineer it from `--help` and the CLI's own
  action list.
- Surface the same failure in `keel context`'s `warnings`, so a session that runs `keel context`
  first (per `AGENTS.md`) learns about a dead `authorize:` declaration without a separate,
  explicitly-invoked `--doctor` call.
- Compute the message once, in `src/core/config.js`, and have both `bin/keel.js` and
  `src/core/context.js` read it, so the two surfaces cannot drift apart the way `--doctor` and
  `keel context` already had (one reported this failure, the other did not).

**Non-Goals:**

- Adding `sync` to `STANDING_AUTHORIZATION_ACTIONS`. `#93` candidate 1 is a semantic widening of
  what `authorize:` accepts, and this repository's own `sync-surface-overlay` scenario (`#54`,
  M4) already asserts the opposite — that naming a gate action and authorizing it once are kept
  separate. Reopening that is an owner decision this change does not make.
- Changing what `keel --doctor` or `keel context` return as an exit code or `status`. Both
  already fail closed (`--doctor` exits non-zero via its overall doctor status; `keel context`'s
  `warnings` array is advisory and never changes `status`, exactly like the existing git dirty-
  path warning). This change adds text, not a new failure mode.
- Generalizing the "value borrowed from a flag, mistaken for a config name" detection beyond
  `sync`. The only place this repository's own CLI presents an action-shaped word (`sync`)
  alongside a name `authorize:` also accepts (`archive`) is `change-close --action`; no other
  flag shares a value with the `authorize:` vocabulary today, so a general mechanism would have
  no second case to prove itself against.

## Decisions

- D1 — Detect the confusion by simple membership: when `unknown.includes("sync")`, append one
  sentence naming `sync` as a `change-close --action` value and pointing at `archive`. Basis: the
  confusion is specific to this one word colliding with this one flag's vocabulary; a general
  "did you mean" mechanism (edit-distance suggestions, etc.) would solve a problem `#93` did not
  report and this repository does not currently have a second instance of.

- D2 — Move message construction into `src/core/config.js` as a new function,
  `standingAuthorizationUnknownMessage(unknown)`, and add a `message` field (string when
  `unknown.length > 0`, otherwise `null`) to `readStandingAuthorization`'s return value. Basis:
  `bin/keel.js` and `src/core/context.js` both need the identical text; computing it in one place
  that both read is what keeps them from re-diverging the way `--doctor` and `keel context`
  already had for this exact declaration. `readStandingAuthorization` is `require`d by both
  already for `declared`/`unknown`; adding one field to its existing return object needs no new
  export and no new call site.

- D3 — `keel context`'s new warning is the same string `--doctor` prints (whole sentence
  including the `sync` clarification when applicable), not a shortened pointer like "run `keel
  --doctor` for detail." Basis: `AGENTS.md`'s own precedent for this file (`#93`'s reasoning,
  point 3) is that a session reads `keel context`'s output and should not need a second command
  to learn what is broken — a pointer-only warning would just move the silence one hop rather
  than removing it.

- D4 — Spec delta is `MODIFIED Requirements` on `keel-standing-authorization`'s existing "An
  unrecognized action name is reported, not granted" Requirement, adding two Scenarios (the
  `sync` clarification, and `keel context` reporting the same failure) rather than a new
  Requirement. Basis: both scenarios refine what "reported" means for this Requirement — where
  and how completely — rather than introducing a new capability concern.

- F1 — Verified 2026-08-12 against the live tree: `grep -n "sync" src/core/config.js` returns
  nothing before this change, confirming `config.js` currently has no knowledge of the
  `change-close --action` vocabulary; this change is what introduces the one string literal
  `"sync"` there, scoped to message text only — `STANDING_AUTHORIZATION_ACTIONS` itself is
  untouched (still `["commit", "push", "release", "archive"]`).

- F2 — Verified 2026-08-12: `scripts/validate_plugin.py`'s `validate_standing_authorization_
  declaration_scenario` (M3, line ~15220) uses `deploy` as its unrecognized-entry fixture, not
  `sync`, so appending a `sync`-specific sentence to the message does not change that scenario's
  assertions (it checks substrings: the offending name, the four accepted names, non-zero exit,
  no leaked authorization — none of which the new sentence removes).

## Hidden Knowledge / Assumptions

- A1 — `configList(repo, "authorize")` (config.js:23-42) already lowercases nothing and reads
  entries verbatim, so `sync` in the declaration must be the literal lowercase token for this
  detection to fire; a repository that somehow wrote `Sync` or `SYNC` would still hit the generic
  unrecognized-action path without the clarification. This matches `#93`'s own repro, which
  wrote lowercase `sync`, and no existing test writes a differently-cased entry.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- The `keel context` warning duplicates text `--doctor` already prints when both are run in the
  same session. This is accepted: the point of D3 is that a session should not need to run both
  to learn the same fact, and `gitWarnings` already establishes the precedent of `keel context`
  carrying advisory text that `--doctor` does not otherwise surface (uncommitted paths).

## Open Questions

None.
