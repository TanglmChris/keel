## ADDED Requirements

### Requirement: Quota thresholds are reported once each, and nudging pauses near the limit

`keel patrol --quota <percent>` MUST treat each threshold in `--quota-alerts` (default 90, 95, 99) that the figure has reached as a risk once per quota period, reporting the highest newly reached threshold, and MUST start a new period when the figure drops below the previous run's. At or above `--quota-quiet-at` (default 90), `--nudge` MUST send nothing and say so.

#### Scenario: Each threshold is reported once, and a new period starts over
- **WHEN** the coordinator runs `keel patrol --since-last --notify --nudge` with `--quota` 50, 91, 93, 96, then 10, then 92, while `verify` has an addressed message waiting
- **THEN** 50 reports nothing and nudges `verify`, 91 reports `past 90%` and nudges nobody, 93 reports nothing, 96 reports `past 95%`, 10 reports nothing, and 92 reports `past 90%` again
