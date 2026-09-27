## ADDED Requirements

### Requirement: Codex overlays follow the OpenSpec layout the repository carries

Keel MUST place and remove Codex OpenSpec overlays, and count Codex OpenSpec surfaces, in the layout the repository actually carries. When the repository has OpenSpec skills under `.codex/skills` and none under `.agents/skills`, that is the OpenSpec 1.6 layout: skills under `.codex/skills`, commands as `CODEX_HOME` prompts. Otherwise it MUST use the OpenSpec 1.13 layout: skills under `.agents/skills`, with no command files.

#### Scenario: A new Codex repository gets the 1.13 layout
- **WHEN** `keel --init --target codex` runs in a new repository with the pinned OpenSpec
- **THEN** the Keel overlays are on `.agents/skills/openspec-*/SKILL.md`, and doctor reports the full Codex surface there

#### Scenario: A 1.6-era Codex repository keeps its layout
- **WHEN** a repository carries OpenSpec skills only under `.codex/skills`
- **THEN** the overlay refresh writes there and to the `CODEX_HOME` prompts, exactly as before
