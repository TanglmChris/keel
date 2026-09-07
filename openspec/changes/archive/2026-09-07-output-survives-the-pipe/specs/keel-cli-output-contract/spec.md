## ADDED Requirements

### Requirement: Output written for a program arrives complete

Keel MUST deliver everything it writes to standard output to the consumer reading it,
whatever the size of the payload and whatever the capacity of the channel. Keel MUST NOT
end the process in a way that discards output the operating system has not yet accepted.

A truncated payload MUST NOT be indistinguishable from a complete one: because Keel cannot
report a loss it did not observe, the guarantee is that no loss occurs, not that a loss is
announced.

Keel MUST continue to report its result through the process exit code, and the exit codes a
command returns MUST NOT change.

#### Scenario: A payload larger than the channel still arrives

- **WHEN** a Keel command writing a payload larger than the receiving pipe's buffer is read by a consumer that begins reading only after the command has finished
- **THEN** the consumer receives the whole payload
- **AND THEN** the payload parses as the document its `--json` contract describes

#### Scenario: The exit code survives the change

- **WHEN** a command succeeds, fails a gate, or is given an invalid argument
- **THEN** Keel returns its documented exit code in each case
- **AND THEN** the process terminates rather than remaining alive
