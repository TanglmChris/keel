## Why

`keel --help`'s Usage block lists every top-level command the CLI dispatcher recognizes —
`context`, `capabilities`, `project`, `gate`, `guard`, `lenses`, `openspec` — except one.
`triage` is recognized at `bin/keel.js:234`, has been since the capability that introduced it
(`declare-what-may-run-unattended`, 5.7.0, whose own proposal listed "the `triage` command, help,
doctor surface" as impact), and is documented in `README.md`'s `## Commands` block. It never
reached the `--help` output.

`node bin/keel.js --help | grep -i triage` returns nothing at 5.29.0. A second flag (`--issue`,
added by #62) has since joined `--labels` on that command, so there are now two things about
`keel triage` a user can only learn by reading the repository rather than by asking the CLI.

Confirmed by grep against every top-level condition in `parseArgs` (`context`, `gate`, `guard`,
`lenses`, `triage`, `openspec`, `project`, plus `capabilities`): `triage` is the only one absent
from HELP's Usage block. This is one missing line, not a pattern of drift across commands.

## What Changes

- `keel --help` gains a `keel triage` line in its Usage block, in the position `README.md` uses
  (after `lenses`, before the install/maintenance commands), naming both `--labels` and `--issue`.
- An `Examples` entry is added alongside it.
- A check is added so the next command the dispatcher recognizes but HELP omits fails a scenario
  instead of waiting for a user to notice.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-unattended-triage`: the triage command's CLI surface is discoverable from `keel --help`,
  completing the help half of the surface the capability's own originating proposal already
  claimed as impact (the doctor half is covered by the existing "triage surface reports every
  declared source" requirement).

## Impact

- `bin/keel.js` — two lines inside the `HELP` template literal (Usage, Examples).
- `scripts/validate_plugin.py` — an assertion added to the existing `cli` scenario.
- Output text of `keel --help`. Nothing in the suite parses this block for its absence of a
  `triage` line, so no existing check is pinned to the gap.
- No change to `keel triage`'s behavior, flags, or exit codes — this is discoverability only.
