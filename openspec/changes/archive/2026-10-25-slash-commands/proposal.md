## Why

Issue #464. On 2026-10-25 the owner asked to tidy and update Keel's slash commands, and set the scope the same day:

- The six plugin skills all appeared in the slash menu. Nothing separated those a person runs from those the protocol has the model run at fixed points.
- Every skill read as `/keel:keel-<name>`, with the namespace repeated in the name.
- Of Keel's everyday CLI flows, only the shift change had a slash entry.
- `keel-md-docx`, a Markdown-to-Word export, is not Keel's job ("这不是keel该做的") and is retired.
- Old `/opsx:*` command files are already removed by `keel --init` (#406). What was missing is a list of the commands and skills a person can invoke.

## What Changes

- **Markdown-to-Word export is removed.** This removes the `keel-md-docx` skill, `keel docx setup|convert`, `src/core/docx.js`, the converter scripts, and their scenarios. `keel docx` now says it was retired and exits nonzero. **BREAKING** for anyone still calling `keel docx`.
- **Skills drop the repeated prefix.** The skills are renamed `align-expectations`, `debug-failure`, `handoff`, `review-checklist`, and `tdd-or-test-first`, so they read as `/keel:<name>` on Claude and `keel:<name>` on Codex. The protocol, specs, overlays, and checks name them the new way. **BREAKING** for a downstream repository's protocol block, which names the old skills until its next `keel --init` refresh; `keel context` already prints that refresh when the block is older than the running Keel.
- **Person or model.** `debug-failure`, `review-checklist`, and `tdd-or-test-first` declare `user-invocable: false`, so they leave the slash menu and the model still invokes them. `align-expectations` and `handoff` stay in the menu and declare an `argument-hint`.
- **Four new commands.** `/keel:context`, `/keel:start`, `/keel:done`, and `/keel:chat` run `keel context`, `keel gate task-start`, `keel gate task-complete` with the review checklist, and `keel chat unread`.
- **A command list.** `docs/commands.md` and `docs/commands.zh-CN.md` list every command and skill a person can invoke, and the READMEs link to them.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`
- `keel-md-docx-export` (every requirement removed; the published spec is deleted at release)
- `keel-authoring-continuity`, `keel-core-gates`, `keel-domain-lenses`, `keel-expectation-alignment`, `keel-expectation-slice-evidence-gates`, `keel-openspec-surface-overlay`, `keel-stateless-continuity`, `keel-unattended-triage`, `keel-validation-runner`, `keel-verification-layering` (the skill names only)

## Impact

The change touches the plugin's skills and commands, `src/skills/`, `bin/keel.js`, `src/core/context.js`, `src/core/gates.js`, `src/core/docx.js` (deleted), `scripts/install_to_repo.py`, the OpenSpec schema and overlays, `AGENTS.md`, the READMEs, new `docs/commands*.md`, `scripts/validation/`, every affected published spec, and the changelog.
