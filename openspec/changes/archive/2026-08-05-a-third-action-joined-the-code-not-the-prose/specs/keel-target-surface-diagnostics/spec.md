## MODIFIED Requirements

### Requirement: Missing Keel overlays are visible

Keel doctor MUST distinguish missing apply/archive/sync overlay markers from unsupported hook gates and missing OpenSpec command files.

#### Scenario: Missing overlay marker is reported

- **WHEN** an apply/archive/sync OpenSpec file exists without the Keel overlay marker
- **AND WHEN** `keel --doctor --target <target>` runs
- **THEN** the report marks the Keel apply/archive/sync overlay as missing
- **AND THEN** the report tells the user to run `keel --init --target <target>` or `keel --install --target <target>` to refresh the overlay
