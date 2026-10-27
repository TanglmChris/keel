## ADDED Requirements

### Requirement: The HANDOFF format is documented without a skill

`keel --help` MUST state the HANDOFF format: YAML front matter with `schema: keel-handoff/v1`, `owner`, `action` naming one of `discuss`, `author`, `task-start`, `task-complete`, or `change-close`, and `reason`, and no other field. `README.md` and `README.zh-CN.md` MUST state the same fields and actions.

#### Scenario: Help names the fields and the actions
- **WHEN** `keel --help` runs
- **THEN** its output names `keel-handoff/v1`, `owner`, `action`, `reason`, and each of `discuss`, `author`, `task-start`, `task-complete`, and `change-close`
