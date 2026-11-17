## ADDED Requirements

### Requirement: Work held only on this machine past 24 hours is a standing risk

Under `keel patrol`, for each covered role's bound worktree, and for the repository's branches without a worktree and its stashes where the patrol covers the repository, the patrol MUST add one standing risk per item that has held work only on this machine for more than 24 hours. A local-only branch or detached head is judged by the committer time of its oldest commit no remote-tracking ref contains, a stash entry by its reflog time. Uncommitted paths MUST NOT be reported under this requirement.

#### Scenario: An old unpushed branch is sent once
- **WHEN** verify's bound worktree is on `feat` whose oldest unpushed commit is 30 hours old, and the coordinator runs `keel patrol --since-last --notify` three times
- **THEN** the coordinator is sent exactly one `keel-patrol` message naming verify and `feat`, and the second and third runs print it as sent before

#### Scenario: A recent unpushed commit is not a risk
- **WHEN** the same branch's oldest unpushed commit is 2 hours old
- **THEN** the patrol adds no such risk

#### Scenario: A stash older than a day is named
- **WHEN** the repository has a stash entry made 3 days ago and the patrol covers the repository
- **THEN** the patrol names the stash as a standing risk once

#### Scenario: Uncommitted paths are not reported by this rule
- **WHEN** a covered worktree has twenty uncommitted paths and no unpushed commit
- **THEN** this rule adds no risk

### Requirement: A work-held risk reads the same on every run and from local refs only

Each such risk text MUST name the role or kind and the branch or stash, MUST carry no count or age, and so MUST be the same on every run until the item is resolved, which lets `--since-last --notify` send it once. The patrol MUST read only local refs and MUST NOT fetch or contact the remote itself.

#### Scenario: The text stays the same as the branch grows
- **WHEN** a covered worktree's old unpushed branch gains a commit between two `--since-last --notify` runs
- **THEN** the second run sends nothing new, since the risk text is unchanged
