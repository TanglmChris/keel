## Facts

- F1 — Claude Code's skill frontmatter accepts `user-invocable` and `argument-hint` in plugin skills. `user-invocable: false` hides a skill from the `/` menu and leaves it to the model. `argument-hint` is the autocomplete hint. For a plugin skill, `name` sets the last segment and the plugin prefix stays. Source: https://code.claude.com/docs/en/skills.md, read 2026-10-25.
- F2 — Codex CLI 0.164.0 loads a skill whose frontmatter also carries `user-invocable: false` and `argument-hint`. Measured on 2026-10-25: in a scratch directory, `codex exec` listed both `probe-frontmatter`, which carries those fields, and `probe-plain`, a control with only `name` and `description`.
- F3 — Codex shows Keel's plugin skills as `keel:keel-<name>`: 172 occurrences each in `~/.codex/sessions` on 2026-10-25. So the repeated prefix shows on both hosts, and a bare name stays namespaced on both.
- F4 — The old skill names appear in 53 files outside archives and `keel/CHANGELOG.md`: 21 requirements in 11 published specs, `AGENTS.md`, the OpenSpec schema in `assets/` and `openspec/`, the generated overlays under `.claude/skills` and `.codex/skills`, `bin/keel.js`, `src/core/context.js`, `src/core/gates.js`, `scripts/install_to_repo.py`, both READMEs, and 10 validation modules. `keel-handoff/v1` is a file-format name, not the skill's, and stays.
- F5 — `keel --init` already removes `/opsx:*` command files that a `both` delivery left behind (#406, `bin/keel.js` around line 1814).
- F6 — `keel docx` is reached from `bin/keel.js` (`process.argv[2] === "docx"` → `src/core/docx.js`). Its checks are the four scenarios of `scripts/validation/export.py`. `docx` is listed among `MUTATING_KEEL_COMMANDS` in `scripts/validation/baseline.py`.

## Decisions

- D1 — The owner's scope (2026-10-25, #464):
  - `align-expectations` and `handoff` stay user-invocable, with an `argument-hint`.
  - `debug-failure`, `review-checklist`, and `tdd-or-test-first` declare `user-invocable: false`.
  - The `keel-` prefix is dropped.
  - Four commands are added: `context`, `start`, `done`, and `chat`.
  - The export is removed entirely.
  - A command list is written.
- D2 — The renamed skill keeps its directory name equal to its `name`, as all of Keel's skills do now. Old directories are removed, not aliased, because an alias would put both names in the menu.
- D3 — `keel docx` stays a recognized word and prints `keel docx was retired in 5.202.0: Markdown-to-Word export is not part of Keel. Use a general document tool.`, exiting 2. An unknown word would print the general usage, which says nothing about where the export went.
- D4 — Each new command is a Claude plugin command file that orders steps and names the `keel` command it runs, as `shift.md` does. The commands are:
  - `context`: run `keel context` and report it in the owner's language.
  - `start`: take the change and task from the arguments or from `keel context`, run `keel gate task-start`, and record the fingerprint.
  - `done`: run `keel gate task-complete`, then the review checklist.
  - `chat`: run `keel chat unread` and act on what is addressed to the role.

  Codex plugins carry skills and no commands, so these four are Claude-only, and the command list says so.
- D5 — A downstream repository's protocol block keeps the old names until it is refreshed. This change does not edit other repositories, and `keel context` already names the refresh when the block is older than the running Keel.
