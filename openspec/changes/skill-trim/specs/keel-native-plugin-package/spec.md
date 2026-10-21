## ADDED Requirements

### Requirement: A skill's plugin copy carries every file of its source
For every Keel skill, the plugin copy under `plugins/keel/skills/<skill>/` MUST hold the same set of files as `src/skills/<skill>/`, and each file in the copy MUST have the same bytes as its source. `native-plugin-manifests` MUST fail and name the file when one is missing from the copy or differs from its source.

#### Scenario: A split-out file missing from the plugin copy is caught
- **WHEN** `src/skills/keel-review-checklist/conditional-checks.md` exists and the plugin copy lacks it
- **THEN** `native-plugin-manifests` fails, naming `conditional-checks.md`

### Requirement: The review checklist loads its conditional checks on demand
The review checklist's `SKILL.md` MUST keep its base checks and MUST name four conditions:
- `Coupling: required`;
- a matching domain lens;
- a new or materially expanded skill;
- an accepted plan-mode artifact.

The criteria that apply only under those conditions MUST live in `conditional-checks.md` beside `SKILL.md`, which is read only when a condition applies. The handoff skill MUST tell the HANDOFF override apart from the shift note.

#### Scenario: The base checklist names the conditions and not their criteria
- **WHEN** the review checklist skill is read
- **THEN** `SKILL.md` names `conditional-checks.md` and its four conditions, and holds no `## Skill change review` or `## Planning artifact funnel` section
- **AND THEN** `conditional-checks.md` holds those sections with their criteria
- **AND THEN** the handoff skill names `keel shift ready` and says that the shift note selects no task
