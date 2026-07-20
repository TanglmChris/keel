## ADDED Requirements

### Requirement: Keel makes openspec invocable for skill-driven agents

Keel MUST provide a `keel openspec` passthrough that forwards its arguments to
Keel's resolved openspec command, and Keel's overlays MUST direct skill-driven
agents to use it in place of a bare `openspec` command that may not be on PATH.

#### Scenario: Passthrough invokes the resolved openspec

- **WHEN** `keel openspec` runs with arguments
- **THEN** Keel forwards the arguments to its resolved openspec command
- **AND THEN** the passthrough works even when bare `openspec` is not on PATH

#### Scenario: Overlays direct agents to the passthrough

- **WHEN** an apply or archive overlay references invoking openspec directly
- **THEN** it directs the agent to `keel openspec` rather than a bare `openspec` that may be unavailable

### Requirement: Archive overlay skips already-promoted specs and reminds to clear the guard

The archive overlay MUST sequence `/opsx:sync` before archive and direct the
archive to pass `--skip-specs` so a delta already promoted by sync is not
re-applied, and MUST remind the current agent to run `keel guard clear` after
archiving. The gate itself remains read-only and writes nothing.

#### Scenario: Archive after sync skips specs

- **WHEN** the archive overlay guides a change whose delta was promoted through `/opsx:sync`
- **THEN** it directs the archive to pass `--skip-specs`
- **AND THEN** it explains this avoids re-applying the already-promoted delta, which upstream openspec rejects

#### Scenario: Archive reminds to clear the guard

- **WHEN** the archive overlay guides a completed archive
- **THEN** it reminds the current agent to run `keel guard clear`
- **AND THEN** the gate performs no guard deletion itself, preserving the read-only guard invariant
