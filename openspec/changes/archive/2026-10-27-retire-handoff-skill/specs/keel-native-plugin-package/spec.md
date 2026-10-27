## MODIFIED Requirements

### Requirement: The review checklist loads its conditional checks on demand
The review checklist's `SKILL.md` MUST keep its base checks and MUST name four conditions:
- `Coupling: required`;
- a matching domain lens;
- a new or materially expanded skill;
- an accepted plan-mode artifact.

The criteria that apply only under those conditions MUST live in `conditional-checks.md` beside `SKILL.md`, which is read only when a condition applies. `docs/shift-change.md` MUST tell the shift note apart from the HANDOFF override.

#### Scenario: The base checklist names the conditions and not their criteria
- **WHEN** the review checklist skill is read
- **THEN** `SKILL.md` names `conditional-checks.md` and its four conditions, and holds no `## Skill change review` or `## Planning artifact funnel` section
- **AND THEN** `conditional-checks.md` holds those sections with their criteria
- **AND THEN** `docs/shift-change.md` says the shift note is not `keel/HANDOFF.md` and that `keel context` does not read it

### Requirement: The slash menu offers what a person runs

The plugin MUST ship the skills `align-expectations`, `debug-failure`, `review-checklist`, and `tdd-or-test-first`, with no `keel-` prefix on their names, so that each one is invoked as `/keel:<name>`, and MUST NOT ship a `handoff` skill. `debug-failure`, `review-checklist`, and `tdd-or-test-first` MUST declare `user-invocable: false`, so that only the model invokes them. `align-expectations` MUST stay user-invocable and declare an `argument-hint`. The Claude plugin MUST ship the commands `shift`, `context`, `start`, `done`, and `chat`, and each of the four new ones MUST name the `keel` command it runs: `keel context`, `keel gate task-start`, `keel gate task-complete`, and `keel chat unread`. The plugin MUST NOT ship a Markdown-to-Word skill. `keel docx` MUST print that it was retired and exit nonzero. `docs/commands.md` and `docs/commands.zh-CN.md` MUST list every command and skill a person can invoke.

#### Scenario: The plugin ships the renamed skills and the new commands
- **WHEN** the packaged plugin's skills and commands are read
- **THEN** the skills are exactly the four names without a `keel-` prefix, with `user-invocable: false` on the three model-only ones and an `argument-hint` on `align-expectations`, and no `handoff`; the commands are exactly `shift`, `context`, `start`, `done`, and `chat`, each new one naming its `keel` command; and `claude plugin validate` passes on the plugin directory

#### Scenario: The retired export says so
- **WHEN** `keel docx setup` or `keel docx convert a.md` runs
- **THEN** it prints that `keel docx` was retired and exits nonzero, and installs or converts nothing
