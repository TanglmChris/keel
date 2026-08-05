## ADDED Requirements

### Requirement: Every overlay summary names the managed action set

Keel reports the overlay from more than one direction — refreshing it during `--init`, `--install`, and `--check`, removing it during `--uninstall` and `--clear`, and reporting its health from `--doctor`. Each of those lines names the actions it covers, and every one of those names MUST be derived from the managed action set rather than written beside it. A summary MUST NOT state its action list as a literal, because a literal is correct only until the set changes and then becomes wrong silently, while still reporting a healthy count.

Two summaries produced by the same installed repository MUST name the same actions. They describe one surface list, and a reader comparing them is entitled to conclude that a difference between them means a difference in what was covered.

The derived label MUST continue to exclude the authoring action, which governs authoring rather than a state-changing command, so that the actions named are the ones whose command surfaces are counted.

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
