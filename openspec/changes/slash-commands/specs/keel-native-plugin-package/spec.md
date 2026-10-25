## MODIFIED Requirements

### Requirement: A skill's plugin copy carries every file of its source
For every Keel skill, the plugin copy under `plugins/keel/skills/<skill>/` MUST hold the same set of files as `src/skills/<skill>/`, and each file in the copy MUST have the same bytes as its source. `native-plugin-manifests` MUST fail and name the file when one is missing from the copy or differs from its source.

#### Scenario: A split-out file missing from the plugin copy is caught
- **WHEN** `src/skills/review-checklist/conditional-checks.md` exists and the plugin copy lacks it
- **THEN** `native-plugin-manifests` fails, naming `conditional-checks.md`

## ADDED Requirements

### Requirement: The slash menu offers what a person runs

The plugin MUST ship the skills `align-expectations`, `debug-failure`, `handoff`, `review-checklist`, and `tdd-or-test-first`, with no `keel-` prefix on their names, so that each one is invoked as `/keel:<name>`. `debug-failure`, `review-checklist`, and `tdd-or-test-first` MUST declare `user-invocable: false`, so that only the model invokes them. `align-expectations` and `handoff` MUST stay user-invocable and declare an `argument-hint`. The Claude plugin MUST ship the commands `shift`, `context`, `start`, `done`, and `chat`, and each of the four new ones MUST name the `keel` command it runs: `keel context`, `keel gate task-start`, `keel gate task-complete`, and `keel chat unread`. The plugin MUST NOT ship a Markdown-to-Word skill. `keel docx` MUST print that it was retired and exit nonzero. `docs/commands.md` and `docs/commands.zh-CN.md` MUST list every command and skill a person can invoke.

#### Scenario: The plugin ships the renamed skills and the new commands
- **WHEN** the packaged plugin's skills and commands are read
- **THEN** the skills are exactly the five names without a `keel-` prefix, with `user-invocable: false` on the three model-only ones and an `argument-hint` on the other two; the commands are exactly `shift`, `context`, `start`, `done`, and `chat`, each new one naming its `keel` command; and `claude plugin validate` passes on the plugin directory

#### Scenario: The retired export says so
- **WHEN** `keel docx setup` or `keel docx convert a.md` runs
- **THEN** it prints that `keel docx` was retired and exits nonzero, and installs or converts nothing
