## ADDED Requirements

### Requirement: Doctor reports keel-* skills as a plugin surface

`keel --doctor` MUST report the `keel-*` behavioral skills as a plugin-delivered
inventory and MUST NOT imply the CLI installs them. When the Keel plugin (and
therefore the skills) is absent, doctor MUST report the gap with explicit
remediation to install the plugin.

#### Scenario: keel-* inventory is attributed to the plugin

- **WHEN** `keel --doctor` reports the skill surface
- **THEN** it presents the `keel-*` behavioral skills as delivered by the Keel plugin
- **AND THEN** it does not report them as CLI-installed target files

#### Scenario: Missing plugin is actionable

- **WHEN** the Keel plugin is not installed
- **THEN** doctor reports the `keel-*` skills as missing with remediation to install the plugin
- **AND THEN** it does not silently claim the skills are present

### Requirement: Doctor distinguishes keel-resolvable openspec from PATH-reachable

`keel --doctor` MUST distinguish an openspec that Keel can resolve internally from
one reachable as a bare `openspec` command on PATH. When the resolved openspec is
not PATH-reachable, doctor MUST report a warning rather than `ok` and MUST name the
working invocation.

#### Scenario: Internal-only openspec warns

- **WHEN** Keel resolves its internal openspec shim but bare `openspec` is not on PATH
- **THEN** doctor reports the openspec line as a warning, not `ok`
- **AND THEN** it names the working invocation, such as `keel openspec`

#### Scenario: PATH-reachable openspec is ok

- **WHEN** bare `openspec` is reachable on PATH
- **THEN** doctor reports the openspec line as `ok`
