## MODIFIED Requirements

### Requirement: Keel ships no scheduler

Keel MUST NOT provide, imply, or claim a scheduling capability, with one exception: `keel shift ready --wake` MAY leave a one-shot waiter that writes a single wake record once its role's next session has started, and then exits. That waiter MUST NOT recur, and the protocol's statement that Keel schedules nothing MUST name it. Documentation and command output MUST attribute the loop to the host runtime rather than to Keel.

#### Scenario: Scheduling is attributed to the host
- **WHEN** the unattended-run documentation is inspected
- **THEN** it states that scheduling is a host capability such as `/loop` or cron
- **AND THEN** no Keel command starts, stops, or registers a recurring run

#### Scenario: The shift wake is the one named exception
- **WHEN** the protocol's statement that Keel schedules nothing is inspected
- **THEN** it names `keel shift ready --wake` as the one exception, a waiter that writes one wake record and exits
