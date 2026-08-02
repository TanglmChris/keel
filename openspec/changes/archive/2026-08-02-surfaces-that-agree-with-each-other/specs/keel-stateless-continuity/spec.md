## ADDED Requirements

### Requirement: The context projection names the Keel that produced it

`keel context` MUST state the Keel version that produced its answer, on the surface the protocol already requires an agent to read. The resident protocol MUST ask the agent to report that version beside the protocol version the repository declares, so a disagreement reaches the human without depending on any runtime component being current.

This placement is required rather than incidental. A version check that lives only inside the plugin cannot report its own absence: when the installed plugin predates the check, its silence is indistinguishable from three versions agreeing. The repository is the only participant that cannot be stale, because the working tree is what every runtime reads.

Keel MUST NOT install, update, or select a version. It reports.

#### Scenario: The context answer carries its own version
- **WHEN** `keel context` reports a status
- **THEN** the output names the Keel version that produced it
- **AND THEN** the version appears for every status, including idle and failure results, because a result that omits it cannot be compared

#### Scenario: The protocol asks for the comparison
- **WHEN** an agent reports the context result at session start
- **THEN** the resident protocol requires it to state the Keel version that answered beside the protocol version the repository declares
- **AND THEN** the requirement does not depend on the SessionStart hook having run, so a runtime too old to carry the comparison does not suppress it
