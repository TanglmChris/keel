## Context

`bin/keel.js`'s `HELP` template literal (lines 90-150) hand-lists every top-level command the
`parseArgs` dispatcher recognizes, in its `Usage:` and `Examples:` sections. The dispatcher
recognizes eight: `context`, `capabilities`, `project`, `gate`, `guard`, `lenses`, `triage`,
`openspec` (grep of `arg === "<name>" && parsed.action === null` plus the `capabilities` branch).
Seven appear in `Usage:`. `triage` does not.

`README.md`'s `## Commands` block does list `keel triage [--labels <l1,l2>] [--issue <n>] [--json]`,
positioned after `keel lenses` and before the install/maintenance group — so the command is
documented in exactly one place, and it is not the one reachable from the terminal.

`keel-unattended-triage`'s originating proposal (`declare-what-may-run-unattended`, 5.7.0) already
named "the `triage` command, help, doctor surface" as its impact. The doctor half shipped a
requirement ("The triage surface reports every declared source") and an assertion. The help half
never got either — this is that gap.

## Goals / Non-Goals

**Goals:**

- `keel --help` lists `keel triage`, naming `--labels` and `--issue`, in the position README
  already uses.
- A check fails if this command (or, incidentally, any other dispatcher-recognized command) is
  ever absent from HELP's `Usage:` block again.

**Non-Goals:**

- Building a mechanism that generates `Usage:` from the dispatcher table. Every other line in
  `HELP` is a hand-maintained literal; there is no existing derivation to extend (unlike
  `overlayActionLabel()` in `overlay-refresh-names-the-managed-set`, which already existed for a
  different line). Introducing one for a single missing line would be a redesign disproportionate
  to the defect.
- Changing `keel triage`'s flags, behavior, admission logic, or exit codes. This is a
  discoverability fix only.
- Rewriting or reordering the rest of `HELP`.

## Decisions

- D1 — Add the missing `Usage:` and `Examples:` lines as literals, matching how every other HELP
  line is written, rather than deriving them. Basis: no derivation mechanism exists for `HELP` text
  today; adding one to close a single-line gap would trade a small, obvious fix for a new
  abstraction with one caller.

- D2 — House the new requirement inside `keel-unattended-triage` as a Modified Capability rather
  than opening a new capability for it. Basis: the capability's own originating proposal already
  claimed the help surface as impact; the doctor half of that claim has a requirement and this
  completes the pair rather than starting a new capability for one line in one command's own help.

- D3 — Verify by extending the existing `cli` scenario (`validate_cli_scenario` in
  `scripts/validate_plugin.py`) rather than adding a new scenario. Basis: that scenario already
  runs `keel --help` and asserts against its stdout (`"Usage:" not in help_result.stdout`); it is
  the scenario that already owns this surface.

- F1 — Verified 2026-08-05 by grep: of the eight dispatcher-recognized top-level commands
  (`context`, `gate`, `guard`, `lenses`, `triage`, `openspec`, `project`, `capabilities`), `triage`
  is the only one absent from `HELP`'s `Usage:` block. The fix is one missing line, not a pattern
  requiring a general mechanism.

- F2 — Reproduced 2026-08-05 at 5.29.0: `node bin/keel.js --help | grep -i triage` returns nothing
  (exit 1). `README.md:347` documents the same command as `keel triage [--labels <l1,l2>] [--issue
  <n>] [--json]`.

## Hidden Knowledge / Assumptions

- A1 — The `cli` scenario is read by `run_baseline`'s registered `SCENARIOS` tuple and runs under
  `npm test`; no separate wiring is needed for a new assertion inside it to be exercised.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- None beyond the output text of `keel --help` changing, which is the point of the change; nothing
  in the suite parses `HELP` for the absence of a `triage` line (F1/F2 measured the gap by grep of
  live CLI output, not by reading a pinned assertion).

## Open Questions

None.
