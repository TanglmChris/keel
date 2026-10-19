## ADDED Requirements

### Requirement: A patrol recommends its next run

`keel patrol` MUST print `next: <duration> (<rule>)` and, with `--json`, carry `next_after_s`, `next_rule` and `next_at`. With `cadence: adaptive` declared under `patrol:`, the first matching rule MUST choose it: `risk` when the run found a risk (default 30m), `quota` when `--quota` is 90 or more (4h), `night` when the local time is inside `quiet: HH:MM-HH:MM` and there is no risk (until the window ends), `busy` when a role other than the patrolling one is not idle or an open wait or todo is assigned to a role that is not idle (60m), and `idle` otherwise (3h); `risk:`, `quota:`, `busy:`, `idle:` and `quiet:` MUST override those defaults, and `min:` and `max:` MUST clamp the result. Without `cadence: adaptive` it MUST recommend `every:` with rule `fixed`.

#### Scenario: Each rule is chosen by its own condition
- **WHEN** the coordinator patrols with `cadence: adaptive`: with every other role idle, after another role's session starts, with `--quota 92` reported once already, after its primary checkout gains an uncommitted file under `--since-last`, and inside a `quiet:` window
- **THEN** the rules are `idle` (3h), `busy` (1h), `quota` (4h), `risk` (30m) and `night` (until the window ends)
- **AND THEN** without `cadence: adaptive` the rule is `fixed` at `every:`, and `min: 50m` raises a 45m `busy` to 50m, printed as `next: 50m (busy)`
