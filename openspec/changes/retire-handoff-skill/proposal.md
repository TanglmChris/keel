## Why

Issue #485. On 2026-10-27 the owner chose to retire the `handoff` skill entirely, reversing the 2026-10-25 choice in #464 that kept `/keel:handoff` in the slash menu. Nobody runs it: `keel/HANDOFF.md` has never been committed in keel, kaiwu-ip, or my-yizhan, and ChipSTRIDE's last of three commits, on 2026-08-17, cleared it. A person picks a task with `/keel:start` and clears the pointer with `keel context --clear-handoff`; writing one is the model's move when `keel context` cannot infer the next step.

## What Changes

- **The `handoff` skill is gone** from the plugin and from `src/skills/`, with its rows in `docs/commands.md` and `docs/commands.zh-CN.md`. The plugin ships four skills.
- **The HANDOFF override stays.** `keel context` still reads, validates, and clears `keel/HANDOFF.md`; the resident protocol text about it is unchanged.
- **The format moves to `keel --help` and the README,** which now name `schema: keel-handoff/v1`, `owner`, `action` with its five values, and `reason`, so it stays documented without the skill.
- **The shift note is told apart from HANDOFF in `docs/shift-change.md`,** which already says so; the checklist requirement that pointed at the skill now points there.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`
- `keel-stateless-continuity`

## Impact

`plugins/keel/skills/handoff/`, `src/skills/handoff/`, `bin/keel.js`, `plugins/keel/.codex-plugin/plugin.json`, `docs/commands.md`, `docs/commands.zh-CN.md`, both READMEs, `scripts/validation/` (`hosts.py`, `baseline.py`, `common.py`, `contract.py`, `docs.py`, `registry.py`), the published specs, and the changelog.
