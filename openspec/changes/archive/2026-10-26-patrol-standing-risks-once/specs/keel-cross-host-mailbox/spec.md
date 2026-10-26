## ADDED Requirements

### Requirement: A parked role's gone session is not reported, and a binding can be removed

`keel patrol` and `keel shift status` MUST NOT report a role whose park is in effect for a session whose directory is gone. `keel chat role --unset` MUST remove the binding of the worktree it runs in, or of the worktree `--repo` names, MUST print the role it unbound, and MUST leave the role's other state in place; with no role bound there it MUST say so and exit 0.

#### Scenario: Parking quiets the risk, and unset removes the binding
- **WHEN** verify's ended CLI session is recorded in a directory that no longer exists, `rtl` runs `keel chat role --park verify`, and then `keel chat role --unset` runs in verify's worktree
- **THEN** `keel patrol` reports no risk naming verify after the park, `--unset` prints `Unbound verify`, and `keel chat role` in verify's worktree then reports no chat role
