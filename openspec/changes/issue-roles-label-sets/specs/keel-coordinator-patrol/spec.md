## MODIFIED Requirements

### Requirement: Issue labels route issue updates to roles

`keel/config.yaml` MAY declare `issue_roles:`, one `<label>: <role>` per line, where the key MAY instead name a set of labels joined by ` + ` (a `+` with whitespace on both sides); a quoted key is one label and is not split. A route matches an issue that carries every label of its key. When `keel patrol` receives `--issues` (the JSON `gh issue list --json number,title,state,labels,updatedAt` prints), it MUST drop each matching route whose label set is a strict subset of another matching route's set, and MUST send each role of the remaining routes one direct message for that issue's `updatedAt`, recorded with ref `issue:#<n>@<updatedAt>`, and MUST NOT send it again while that ref exists in the direct group. A line it cannot read, including a set with an empty or repeated label, MUST be reported and route nothing.

#### Scenario: A labelled issue reaches its role once per update
- **WHEN** `issue_roles:` maps `role:verify` to `verify` and `--issues` lists issue 157 with that label
- **THEN** patrol sends `verify` one direct message naming #157 and exits 3; a second run with the same `updatedAt` exits 0; a run with a later `updatedAt` sends one more

#### Scenario: A set of labels routes to the team that carries them all
- **WHEN** `issue_roles:` maps `design` to `design-iecc`, `design + dmc_rmw` to `design-rmw`, and `flow` to `flow`, and `--issues` lists issue 160 labelled `design`, `dmc_rmw`, and `flow`, and issue 161 labelled `design` alone
- **THEN** `design-rmw` and `flow` each get one direct message naming #160 and `design-iecc` gets none naming it, and `design-iecc` gets one naming #161 that `design-rmw` does not

#### Scenario: A set that cannot be read routes nothing
- **WHEN** `issue_roles:` holds `design + : design-rmw` and `design + design: design-rmw`, and `--issues` lists an issue labelled `design`
- **THEN** both lines are reported and `design-rmw` gets no message
