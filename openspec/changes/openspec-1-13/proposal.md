## Why

Issue #169. Since 5.74.0, Keel's published `npm-shrinkwrap.json` pins OpenSpec 1.6.0 (released 2026-07-10) for every install, while consumers had been running 1.13.2 (2026-09-23). 5.77.0 stopped `keel --init` from downgrading their surfaces (#168), but Keel still runs an OpenSpec that is two and a half months old, and a new repository starts on its templates.

Moving the pin to 1.13.2 fails six scenarios, for two reasons measured on 2026-09-27:
- OpenSpec 1.13 writes Codex's surfaces as skills under `.agents/skills/openspec-*` in the repository. It writes no `.codex/skills` and no `CODEX_HOME/prompts/opsx-*.md`, and Keel's Codex overlay, doctor, and uninstall still assume the 1.6 layout.
- 1.13's strict validation refuses a `## Purpose` still reading `TBD - created by archiving change …`, and six published specs carry one.

## What Changes

- **Pin OpenSpec 1.13.2.** The shrinkwrap resolves it, and the declared range stays `^1.4.1`.
- **Codex surfaces follow the layout that is present.** A repository with OpenSpec skills under `.codex/skills` and none under `.agents/skills` keeps the 1.6 layout: skills there, commands as `CODEX_HOME` prompts. Every other Codex repository uses the 1.13 layout: skills under `.agents/skills`, and no command files. The overlay refresh, uninstall, and doctor read that one layout.
- **Six specs get the Purpose they never had**, so the store passes 1.13's strict validation.
- **The protocol line about Codex's command surface** says where 1.13 puts it.

## Capabilities

### Modified Capabilities

- `keel-openspec-surface-overlay`: Codex overlays go to the OpenSpec layout the repository actually carries.

## Impact

- `npm-shrinkwrap.json`, `bin/keel.js`, `src/core/context.js`, `scripts/validate_plugin.py`, `AGENTS.md`, and six `openspec/specs/*/spec.md` Purposes.
- A Codex repository set up under 1.6 keeps working unchanged. A new one gets `.agents/skills`.
- In a repository whose surfaces 1.13.2 wrote, doctor's `OpenSpec surfaces` line becomes `ok`.
