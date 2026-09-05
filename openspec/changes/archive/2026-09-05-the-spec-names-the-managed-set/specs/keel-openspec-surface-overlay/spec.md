## RENAMED Requirements

- FROM: `### Requirement: Keel overlays apply and archive surfaces`
- TO: `### Requirement: Keel overlays every action in the managed set`

## MODIFIED Requirements

### Requirement: Keel overlays every action in the managed set

Keel MUST maintain a managed overlay on the OpenSpec-generated skills and command entries of every action in the managed set — `propose`, `apply`, `archive`, and `sync` — for each supported target, except where a target has no surface for an action. The overlay MUST state that Keel rules take precedence over conflicting generic OpenSpec instructions.

The requirement MUST name the set rather than a subset of it. Each action's overlay content is stated by its own requirement below; this one states which actions have an overlay at all, and a statement that names two of four leaves the file disagreeing with itself.

#### Scenario: Claude surfaces receive the overlay for every managed action

- **WHEN** `keel --init --target claude` runs in a repository
- **THEN** the `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, and `openspec-sync-specs` skills under `.claude/skills/` each contain the Keel overlay marker
- **AND THEN** `.claude/commands/opsx/propose.md`, `apply.md`, `archive.md`, and `sync.md` each contain the Keel overlay marker

#### Scenario: Codex surfaces receive the overlay for every managed action

- **WHEN** `keel --init --target codex` runs with `CODEX_HOME` set
- **THEN** the same four skills under `.codex/skills/` each contain the Keel overlay marker
- **AND THEN** `<CODEX_HOME>/prompts/opsx-propose.md`, `opsx-apply.md`, `opsx-archive.md`, and `opsx-sync.md` each contain the Keel overlay marker
- **AND THEN** the user's real `.codex/prompts` directory is not required for verification

#### Scenario: OpenCode surfaces receive the overlay for the actions it has

- **WHEN** `keel --init --target opencode` runs in a repository
- **THEN** the `openspec-apply-change`, `openspec-archive-change`, and `openspec-sync-specs` skills under `.opencode/skills/` each contain the Keel overlay marker
- **AND THEN** `.opencode/commands/opsx-apply.md`, `opsx-archive.md`, and `opsx-sync.md` each contain the Keel overlay marker
- **AND THEN** no authoring overlay is written for `propose`, which this target does not receive

### Requirement: Keel refreshes existing overlays idempotently

Keel MUST replace an existing managed overlay block instead of duplicating it, and MUST skip missing OpenSpec files during `keel --install` instead of creating incomplete generated surfaces.

#### Scenario: Install refreshes an existing overlay

- **WHEN** an initialized target has an OpenSpec file for a managed action with an outdated Keel overlay block
- **AND WHEN** `keel --install --target <target>` runs
- **THEN** the file contains exactly one current Keel overlay block
- **AND THEN** other OpenSpec-generated content remains present

#### Scenario: Install skips missing OpenSpec files

- **WHEN** `keel --install --target <target>` runs before OpenSpec has generated the files for a managed action
- **THEN** Keel does not create placeholder OpenSpec files for that action
- **AND THEN** `keel --doctor --target <target>` reports the missing overlay or missing surface with remediation

### Requirement: Every overlay summary names the managed action set

Keel reports the overlay from more than one direction — refreshing it during `--init`, `--install`, and `--check`, removing it during `--uninstall` and `--clear`, and reporting its health from `--doctor`. Each of those lines names the actions it covers, and every one of those names MUST be derived from the managed action set rather than written beside it. A summary MUST NOT state its action list as a literal, because a literal is correct only until the set changes and then becomes wrong silently, while still reporting a healthy count.

Two summaries produced by the same installed repository MUST name the same actions. They describe one surface list, and a reader comparing them is entitled to conclude that a difference between them means a difference in what was covered.

The derived label MUST continue to exclude the authoring action, which governs authoring rather than a state-changing command, so that the actions named are the ones whose command surfaces are counted.

This capability's own specification is a summary of the managed set in the same sense, and MUST be checked against it. The `## Purpose` line and the requirement that states which actions carry an overlay MUST each name every action in the managed set, and a verification check MUST fail and name the location when either stops doing so. The check MUST read the managed set from the code that owns it rather than restating it, and MUST assert those two named locations rather than scanning the file: three statements in the published specs name a proper subset of the set correctly — the doctor's command-surface label, the archive requirement's description of what the current agent owns, and a spelling of the full set that writes `propose` as authoring — and a check that refused them would cost more than the drift it catches.

A capability's `## Purpose` MUST be maintained by direct edit to the published spec. OpenSpec's delta operations are Requirement-scoped, so no change can carry a Purpose edit, and the line is written once when the capability is created. This is why a drifted Purpose survives a sweep of the requirements around it, and why the check above covers it explicitly.

#### Scenario: The refresh summary names the derived set

- **WHEN** `keel --init`, `keel --install`, or `keel --check` refreshes the overlay and reports its summary
- **THEN** the actions named in that line are the managed set the overlay covers
- **AND THEN** an action added to that set appears in the line without the line being edited

#### Scenario: Refresh and removal agree on one repository

- **WHEN** one repository is installed and then uninstalled
- **THEN** the refresh summary and the removal summary name the same actions
- **AND THEN** the health line from `--doctor` on that repository names those same actions

#### Scenario: A drifting summary is a failing check

- **WHEN** a summary line stops naming the managed set, whether by being written as a literal or by an action joining the set without reaching it
- **THEN** a verification check fails and names the line that drifted
- **AND THEN** the check distinguishes a summary that disagrees from a summary that is absent, so a line that was never printed is not reported as a line that printed the wrong thing

#### Scenario: The capability's own Purpose names the managed set

- **WHEN** the `## Purpose` line of this capability's published spec names a proper subset of the managed set
- **THEN** a verification check fails and names the Purpose line
- **AND THEN** the check reads the managed set from the code rather than from a literal of its own

#### Scenario: The requirement that states the set names all of it

- **WHEN** the requirement stating which actions carry an overlay names a proper subset of the managed set
- **THEN** a verification check fails and names that requirement
- **AND THEN** the check fails rather than passing silently when it cannot find that requirement at all
