## Why

Issue #413, second of three changes. The owner asked for the English and Chinese READMEs to be revised together (2026-10-20): "readme现在应该已经过时了，我建议中英文一直改改".

**English README.** The 2026-10-20 audit found statements the CLI contradicts:
- "skills and agents follow after `/reload-plugins`" — 5.173.0 removed the agents.
- "The eleven names above" — the vocabulary has thirteen.
- The scoped-name list omits `push-protected`.
- Lens skills "load only that one lens" — 5.172.0 removed that limit.
- "`keel --init` whenever it tells you the repository is behind" — `--doctor` names `keel --install`.
- "`keel --init` writes only" an `AGENTS.md` block, the schema, and the overlay — it also declares auto-update in `.claude/settings.json`.
- "/opsx:apply (pick one task)" — 5.172.0 made the protocol work through `tasks.md` in order.
- A command line that gives `--check` and `--doctor` a `--dry-run` they refuse.
- Exit codes that omit `2`, a usage error.
- The Commands block omits `keel lock`, `keel shift`, `keel mail`, `keel worktrees`, `keel capabilities`, `keel project`, `keel openspec`, `--clear`, and most gate, guard, install, and update flags.

**Chinese README.** It is 355 lines against 1000. It lacks 13 of the English sections, and it contradicts the English in places: it says `--init` is the only setup command, and omits the push check from the write guard. The English README nevertheless calls it the "full command and workflow reference".

## What Changes

- **`README.md`** is corrected against the CLI and the specs, and its Commands block lists every command and flag in `keel --help`.
- **`README.zh-CN.md`** is rewritten as the Chinese counterpart of the corrected English: the same sections in the same order, and the same commands, flags, and authorization names.
- **Two scenarios** hold this:
  - `readme-states-the-cli` checks `README.md` against `keel --help`, `STANDING_AUTHORIZATION_ACTIONS`, and the exit codes, and keeps the corrected sentences from coming back.
  - `readme-zh-matches-english` applies the same command and name checks to the Chinese README and requires the same `##` and `###` section counts.
- **Spec:** `keel-native-plugin-package` gains a requirement that both READMEs state the CLI and carry the same sections.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`

## Impact

`README.md`, `README.zh-CN.md`, `scripts/validate_plugin.py`, the published spec, and the changelog. The `docs/` pages, their Chinese counterparts, and the `keel/config.yaml` comments are the third change of #413.
