## ADDED Requirements

### Requirement: A role can be parked on purpose

`keel chat role --park <role> [--reason <text>]` MUST record that a bound role is parked, with the reason, the parking role, and the time, and MUST refuse a role no worktree is bound to. `keel chat role --unpark <role>` MUST remove the park and report how many addressed records wait for the role and since when. A park MUST stop being in effect once the role's presence records activity after it. While a role's park is in effect, a post, direct message, or todo that wakes it MUST be stored as usual, and the poster's output MUST say the role is parked, since when and why, in place of the offline report and the desktop wake step.

#### Scenario: A todo for a parked role says it is parked
- **WHEN** `rtl` runs `keel chat role --park verify --reason "until R040"` and then assigns `verify` a todo
- **THEN** the todo is stored and the output names `verify` as parked with `until R040`; `--park ghost` for an unbound role exits non-zero; after `keel chat role --unpark verify` the output reports the records waiting, and a new todo no longer says parked
