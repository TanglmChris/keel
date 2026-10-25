## ADDED Requirements

### Requirement: A standing risk reaches the coordinator once

Under `keel patrol --since-last`, each risk about a CLI hand-off and each risk about a session whose directory is gone MUST be recorded by its text in the patrolling role's snapshot, and MUST be counted among the run's risks — and so sent by `--notify` — only when that text is absent from the previous run's snapshot, a first run included. A standing risk whose text was recorded by the previous run MUST be printed as sent before and MUST NOT be sent or raise the exit status. Without `--since-last`, every such risk MUST be reported on every run.

#### Scenario: An unchanged moved-session risk is sent once
- **WHEN** verify's ended CLI session is recorded in a directory that no longer exists and the coordinator runs `keel patrol --since-last --notify` three times
- **THEN** the coordinator is sent exactly one `keel-patrol` message naming verify's session, the second and third runs print it as sent before and do not exit 2, and a plain `keel patrol` still reports it as a risk
