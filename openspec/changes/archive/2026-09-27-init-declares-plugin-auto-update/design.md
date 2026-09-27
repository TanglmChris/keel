## Context

The host facts are from the Claude Code plugin loading reference, recorded on #164.
- Whether a marketplace auto-updates follows the first of these that is set:
  1. `autoUpdate` on its `extraKnownMarketplaces` entry in a settings file;
  2. `autoUpdate` on its `known_marketplaces.json` entry;
  3. the default, which is off for every non-official marketplace.
- Auto-update runs after a session's first message, following a random delay of up to ten minutes, and prompts `Run /reload-plugins to apply`.

## Findings

- F1 — `keel --init --target claude` writes `AGENTS.md`, `CLAUDE.md`, `keel/config.yaml`, `openspec/`, and the `/opsx` surfaces. It never writes `.claude/settings.json`. `scripts/install_to_repo.py` already has a merge strategy for that file, `keel-hook-settings`, used only by the retired hook path.
- F2 — `claude plugin marketplace list --json` reports `name`, `source`, `repo`, and `installLocation`, but no auto-update state, so the setting's effect cannot be probed from Keel.
- F3 — This repository's own `.claude/settings.json` carries only `permissions.allow`.

## Decisions

- D1 — **A new installer strategy, `claude-marketplace-settings`**, on the Claude target. It merges one entry into `extraKnownMarketplaces`. If there is no entry, it writes Keel's. If there is an entry, it keeps the entry's `source`, keeps any `autoUpdate` it states, and adds `autoUpdate: true` only when the key is absent. Everything else in the file is kept, and the output is `json.dumps(indent=2)`, the formatting `keel-hook-settings` uses. A file that is not a JSON object fails the install with its reason, as the existing strategy does.
- D2 — **Keel's entry** is `{"source": {"source": "github", "repo": "TanglmChris/keel"}, "autoUpdate": true}` under the name `keel-marketplace`. The name and repository are the ones the README tells users to add, so the declared marketplace is the one they already have and not a second copy. A developer who added the marketplace from a local directory under that name keeps it, because an existing entry's `source` is never replaced.
- D3 — **Uninstall** removes the entry only when it equals Keel's exactly. It then drops `extraKnownMarketplaces` if that is left empty, and the file if it is left `{}`. A changed entry belongs to the project.
- D4 — **Doctor** prints `plugin auto-update` on the Claude target:
  - `ok` when the entry says `autoUpdate: true`;
  - `manual` when it says `false`, naming it as the project's choice;
  - `manual` when it is absent, naming `keel --install --target claude` and the `/plugin` → Marketplaces toggle.

  It says it reports the declaration, and that the host exposes no way to observe whether updates actually run (F2).
- D5 — **Assertions** live in one new scenario, `init-declares-plugin-auto-update`. It drives the real `keel --init`, `--install`, `--uninstall`, and `--doctor` against scratch repositories. There is no host probe (F2).
