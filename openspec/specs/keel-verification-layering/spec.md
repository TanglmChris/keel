# keel-verification-layering Specification

## Purpose
Define Keel's verification-layering convention — the fast inner-loop check (local pre-push, seconds) versus the full gate (CI or `keel gate change-close`) — together with its surfaces: the `keel/config.yaml` `fast_check` declaration, the opt-in `keel --install --with-git-hooks` pre-push scaffold and its symmetric revert, and the `keel --doctor` fast pre-push report. The optional `(fast)`/`(full)` task-capsule Verify layer tag that records which checks the fast inner loop runs lives in `keel-task-capsule`.
## Requirements
### Requirement: Keel documents the fast and full verification split

Keel MUST document a verification-layering convention that distinguishes a fast
inner-loop check — seconds, suitable for a local pre-push and iteration — from the
full gate that runs the complete or slow suite at CI or `keel gate change-close`.
The convention MUST keep task `Verify` checks runnable fast and direct the slow or
exhaustive layer to the full gate, and it MUST be stated where Keel projects read
their protocol guidance.

#### Scenario: The split is documented for projects
- **WHEN** a Keel project consults the shipped documentation for how to verify work
- **THEN** it finds the fast inner-loop (local pre-push, seconds) versus full gate (CI or `change-close`) split stated
- **AND THEN** the guidance directs the slow or exhaustive suite to the full gate rather than the local pre-push

### Requirement: Keel projects declare a fast inner-loop check

Keel MUST let a project declare its fast inner-loop command in a `keel/config.yaml`
`fast_check` field, read through Keel's existing minimal flat-key parsing without a
new dependency. `keel --install` MUST scaffold a commented `keel/config.yaml`
template when none exists, and MUST NOT overwrite a project's existing
`keel/config.yaml`.

#### Scenario: Declared fast check is read
- **WHEN** a repo defines `fast_check: <command>` in `keel/config.yaml`
- **THEN** Keel reads that command as the project's fast inner-loop check
- **AND THEN** a repo with no `keel/config.yaml` or no `fast_check` reports the fast check as undeclared without failing

#### Scenario: Install scaffolds the config template once
- **WHEN** `keel --install` runs against a repo with no `keel/config.yaml`
- **THEN** it writes a commented `keel/config.yaml` template describing `fast_check`
- **AND THEN** a later `keel --install` leaves an existing `keel/config.yaml` untouched

### Requirement: keel --install --with-git-hooks scaffolds a fast local pre-push

`keel --install` MUST accept an explicit `--with-git-hooks` flag that generates a
`.githooks/pre-push` `#!/bin/sh` script running the declared `fast_check` and sets
`git config core.hooksPath .githooks` for that repo. Without the flag, `keel
--install` MUST NOT touch git config or git hooks. The flag MUST refuse when
`fast_check` is undeclared. `keel --uninstall` and `keel --clear` MUST unset
`core.hooksPath` when and only when it equals `.githooks`, leaving the committed
`.githooks/pre-push` file in place.

#### Scenario: Flag generates the hook and sets hooksPath
- **WHEN** `keel --install --with-git-hooks` runs in a repo that declares `fast_check`
- **THEN** it writes `.githooks/pre-push` as a `#!/bin/sh` script that runs the declared `fast_check`
- **AND THEN** it sets `core.hooksPath` to `.githooks` and reports both actions

#### Scenario: Plain install never touches git config
- **WHEN** `keel --install` runs without `--with-git-hooks`
- **THEN** it does not write `.githooks/pre-push` and does not change `core.hooksPath`
- **AND THEN** the repo's git hook configuration is left exactly as it was

#### Scenario: Flag refuses without a declared fast check
- **WHEN** `keel --install --with-git-hooks` runs in a repo with no declared `fast_check`
- **THEN** it refuses and reports that a `fast_check` must be declared in `keel/config.yaml`
- **AND THEN** it does not write a hook or change `core.hooksPath`

#### Scenario: Uninstall reverts only a keel-set hooksPath
- **WHEN** `keel --uninstall` or `keel --clear` runs where `core.hooksPath` equals `.githooks`
- **THEN** it unsets `core.hooksPath`, restoring the default hook path
- **AND THEN** a `core.hooksPath` pointing anywhere other than `.githooks` is left untouched

### Requirement: Keel diagnoses the fast pre-push surface

`keel --doctor` MUST report the fast pre-push surface without mutating it: whether
`fast_check` is declared in `keel/config.yaml`, whether `.githooks/pre-push`
exists, and the repo's current `core.hooksPath`.

#### Scenario: Doctor reports the fast pre-push surface
- **WHEN** `keel --doctor` inspects a repo
- **THEN** it reports whether `fast_check` is declared, whether `.githooks/pre-push` is present, and the current `core.hooksPath`
- **AND THEN** doctor makes no change to git config, the hook file, or the config

