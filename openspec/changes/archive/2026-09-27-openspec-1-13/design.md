## Findings

- F1 — `openspec init --tools codex` under 1.13.2 writes `.agents/skills/openspec-{propose,explore,apply-change,archive-change,sync-specs}/SKILL.md` and `.agents/skills/.openspec-target` into the repository. It writes nothing under `.codex/` and nothing in `CODEX_HOME`. Measured in a scratch directory on 2026-09-27.
- F2 — Keel already puts its own Codex skills under `.agents/skills` (`skillRootForTarget`). Only the OpenSpec surfaces still point at `.codex/skills` (`openspecSkillRootForTarget`) and at `CODEX_HOME/prompts` (`commandSurfaceForTarget`, `commandPathForAction`).
- F3 — With the pin moved to 1.13.2, `npm test` fails `target-surface`, `sync-surface-overlay`, `openspec-surface-overlay`, `uninstall-removes-the-overlay`, `authoring-alignment-overlay`, and `published-specs-validate-strictly` (20 passed, 6 failed).
- F4 — This repository tracks 1.6-layout Codex surfaces under `.codex/skills`, which `bump_version.js` sweeps for markers.

## Decisions

- D1 — **Pin.** `npm install @fission-ai/openspec@1.13.2`, then restore `package.json`'s range to `^1.4.1` and resync. The range is the oldest OpenSpec Keel accepts; the shrinkwrap is the one it ships.
- D2 — **Codex layout detection** (`codexOpenSpecLayout(repo)`). The layout is `legacy` when `.codex/skills` holds an `openspec-*` directory and `.agents/skills` holds none, and `agents` otherwise, which includes a repository not yet initialized. That default matches what the pinned OpenSpec writes.
- D3 — **Agents layout surfaces.** The skill root is `.agents/skills`, and the command surface is empty, because 1.13 writes no Codex command files. The overlay goes on the skills only. Doctor's Codex command line says the commands are skills under `.agents/skills` rather than printing `0/0`.
- D4 — **Legacy layout** is exactly today's behavior, so a 1.6-era repository, this one included (F4), is untouched.
- D5 — **Purposes.** Each of the six is one or two sentences saying what the capability is for, drawn from its requirements. They are edited directly in the main specs, because a delta's `## Purpose` is read only when a capability is created.
- D6 — **Protocol line.** `AGENTS.md`'s "Target command surface differs by runtime" line says Codex's OpenSpec workflows are skills under `.agents/skills` (OpenSpec 1.13), or `CODEX_HOME` prompts in a repository set up under 1.6.
