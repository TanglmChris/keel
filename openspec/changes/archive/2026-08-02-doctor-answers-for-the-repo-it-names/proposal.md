## Why

`keel --doctor` prints `keel doctor for <repo>` and then answers about a different repository: it reads the OpenSpec pin from `PACKAGE_ROOT/package-lock.json`, which is Keel's own install location, not the repository named on the line above. Measured 2026-08-02 at 5.14.0 — a consumer repo pinning `9.9.9` was told `lockfile 1.6.0`, which is Keel's checkout's pin; a global install, which ships no lockfile, is told `lockfile unreadable` forever.

The cross-check exists (added 5.11.0, issue #36) to explain exactly this class of drift: a green pipeline and a red worktree that were the same command run against two different programs. Rooting it at `PACKAGE_ROOT` makes it correct only when Keel's install location happens to equal the repository under diagnosis — true in Keel's own source checkout, false for every real consumer. The diagnostic written to expose version drift is dead wherever version drift can occur, and its silence is indistinguishable from agreement.

## What Changes

- `keel --doctor` reads the OpenSpec pin from the repository it names, not from Keel's install location. `PACKAGE_ROOT` is no longer consulted for the pin.
- The doctor line states *whose* pin it read and *which* OpenSpec answered, so the two roots can never again be read as one.
- A repository that declares no OpenSpec pin is reported as declaring none, distinctly from a pin that could not be read. Absence is the normal case for a consumer and MUST NOT be reported as disagreement.
- **Not changing**: which `openspec` binary Keel runs. Resolution stays rooted at `PACKAGE_ROOT`, preserving the existing stance that Keel states which one answered and selects none (`bin/keel.js:689`, and `keel-target-surface-diagnostics`: "Keel MUST NOT install, select, or refuse an OpenSpec version"). Issue #57's candidate to reroot resolution as well is deliberately declined; see design D2.
- Coverage gains a scenario driven from a repository that is not Keel's checkout and that declares its own pin. Every existing scenario spawns `node <keel-checkout>/bin/keel.js`, so `PACKAGE_ROOT` is always Keel's checkout — the one condition under which this defect cannot appear.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-target-surface-diagnostics`: the requirement that doctor reports "the range the repository declares" is sharpened to name *which* repository — the one under diagnosis — and to require the reported pin and the answering binary be attributed to their roots. Adds a scenario exercised from outside Keel's own checkout.

## Impact

- `bin/keel.js`: `lockedOpenSpecVersion()` (`:702`) takes the diagnosed repository as its root; `runDoctor()` (`:1429`, `:1436-1447`) states attribution and distinguishes "declares none" from "unreadable".
- `bin/keel.js:639` `openspecCandidates()` and `:719` `findOpenSpecCommand()` are untouched, so `keel openspec …` (`:896`, `:1755`) runs exactly the binary it runs today.
- `scripts/validate_plugin.py`: one new scenario plus registry entry.
- Risk: the mismatch warning now fires in consumer repositories where it never fired before. This is the intended effect, but it means a repo pinning an OpenSpec version different from Keel's bundled one sees a new warning after upgrading. The warning is advisory and does not change doctor's exit status.
- Risk: reading a lockfile from a user-supplied path. Read-only, failure-tolerant, and already the behavior for Keel's own root; no new write surface.
