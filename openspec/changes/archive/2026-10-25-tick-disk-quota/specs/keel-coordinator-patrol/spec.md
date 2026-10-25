## ADDED Requirements

### Requirement: The tick passes free disk and a declared quota to the patrol

Before each patrol run, `keel tick` MUST measure free space on that patrol's worktree filesystem and pass it as `--disk-free-gb`, with `--disk-min-gb` from the first `patrol:` item declaring `disk_min_gb:`, and patrol's default otherwise. When a `patrol:` item declares `quota_file:`, the tick MUST read the first number in that file and pass it as `--quota` only when the file was modified within the last 6 hours, and it MUST run no command to obtain it. The tick MUST print a quota line when the quota state — read, stale, unreadable, or unchecked when no `quota_file:` is declared — differs from its previous run's, and not otherwise.

#### Scenario: Low disk reaches the owning coordinator once
- **WHEN** `patrol:` lists scoped `pm-a` and `pm-b` with `runner: tick` and `disk_min_gb` far above the machine's free space, and `keel tick` runs the patrols twice
- **THEN** pm-a, the first listed, is sent one `keel-patrol` message naming free disk below the floor, and pm-b none

#### Scenario: A quota file drives the quota risk, and its absence is said once
- **WHEN** `quota_file:` names a file reading `91`, then `96`, between due ticks, and later the file is made 7 hours old; and separately no `quota_file:` is declared
- **THEN** the owning coordinator is sent `past 90%` and then `past 95%` once each, the old file makes the tick print that quota is stale, and with none declared the first tick prints that quota is not checked and the next one prints no quota line
