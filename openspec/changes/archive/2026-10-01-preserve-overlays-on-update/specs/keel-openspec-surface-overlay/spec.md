## ADDED Requirements

### Requirement: OpenSpec update restores every installed target overlay

After a successful `keel openspec update`, Keel MUST replay its managed overlays on existing OpenSpec surfaces for every target installed in that repository. It MUST preserve upstream content, avoid duplicate overlays, and create no absent surface. Other OpenSpec commands MUST retain passthrough behavior. A failed update MUST preserve its exit status and MUST NOT replay overlays.

#### Scenario: A multi-target update restores overlays
- **WHEN** Claude and Codex surfaces exist and an OpenSpec update replaces them
- **THEN** the successful Keel update restores exactly one current overlay on each managed surface in the resulting layout
- **AND THEN** another update retains exactly one overlay and upstream body content

#### Scenario: An update fails
- **WHEN** upstream update exits nonzero
- **THEN** Keel returns that status without replaying overlays

#### Scenario: An absent target remains absent
- **WHEN** a repository has only one installed target
- **THEN** updating does not create another target's files

### Requirement: Doctor reports overlays for all repository-installed targets

Doctor MUST report separately attributable overlay health for every repository-installed target, including targets other than the selected one. Discovery MUST use repository surfaces rather than unrelated global prompts. It MUST retain legacy Codex and .agents layout support and name remediation for incomplete coverage.

#### Scenario: Codex overlay is missing while Claude is healthy
- **WHEN** doctor selects Claude in a mixed repository with missing Codex overlays
- **THEN** Claude health remains attributable to Claude and an additional Codex report identifies the missing coverage and Codex remediation

#### Scenario: Global prompts belong to another repository
- **WHEN** global Codex prompts exist but the repository has no Codex surface
- **THEN** doctor does not infer an installed Codex target from those prompts
