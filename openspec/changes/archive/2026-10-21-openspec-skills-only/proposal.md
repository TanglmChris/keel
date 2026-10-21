## Why

Issue #406. In a Keel-managed repository (kaiwu-ip, Keel 5.170.0, OpenSpec 1.14.0) the Claude surface carries every OpenSpec workflow twice: a skill under `.claude/skills/openspec-*` and a command under `.claude/commands/opsx/*`. Both show in the model's listing every session with slightly different descriptions, and every protocol bump refreshes the Keel overlay on both copies. The cause is OpenSpec's `delivery` setting, which defaults to `both` and which OpenSpec reads only from the user's global configuration (`~/.config/openspec/config.json`); there is no project-level setting and no flag.

The owner decided on 2026-10-21 (recorded on #406): Keel itself guarantees skills only, without touching the user's global configuration.

## What Changes

- Every OpenSpec `init` and `update` Keel runs — `keel --init` and `keel openspec init|update` — runs with a temporary OpenSpec configuration: the user's global configuration with `delivery` set to `skills`. The global file is not written. OpenSpec then generates skills only and removes the command files a `both` delivery left, for Claude and, because the setting is per run rather than per tool, for OpenCode too. Codex already had skills only.
- `keel --doctor` stops expecting command files on Claude and OpenCode. Command files still present read `duplicate`, with the count and `keel --init --target <target>` as the remedy, and the overlay count covers the skills plus any leftover command file.
- Shipped guidance names the workflows by skill instead of `/opsx:*`: the archive overlay, the README pair, the Keel skills that mention them, the Keel schema, and this repository's protocol text.
- This repository drops its own `.claude/commands/opsx/` and rewrites its Claude skills' `/opsx:*` references the way OpenSpec's skills delivery does.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-openspec-surface-overlay`: OpenSpec workflows are generated as skills only, and guidance names them by skill.
- `keel-target-surface-diagnostics`: doctor expects no command files on Claude and OpenCode and reports leftovers as duplicates.

## Impact

`bin/keel.js` (OpenSpec invocation, command surfaces, doctor, archive overlay text), `scripts/validate_plugin.py`, `README.md`, `README.zh-CN.md`, `src/skills/*` and `plugins/keel/skills/*` (three skills), `assets/openspec/schemas/keel-spec-driven/schema.yaml` and this repository's copy, `AGENTS.md`, this repository's `.claude/commands/opsx/` and `.claude/skills/openspec-*`, the published specs, the changelog.
