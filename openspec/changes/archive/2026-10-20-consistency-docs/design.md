## Context

The facts below were measured on 5080527 (5.176.0).

## Facts

- F1 — `CONFIG_DECLARATIONS` in `src/core/config.js` lists twelve keys "in the order the file documents them": fast_check, authorize, precedents, triage, full_mode_paths, executor_tier, merge, external_agents, read_only_roles, issue_roles, patrol, owner_language.
  - `keel/config.yaml` documents them as owner_language, patrol, issue_roles, read_only_roles, fast_check, authorize, precedents, triage, patrol again, full_mode_paths, merge, external_agents.
  - It has no `executor_tier` block.
- F2 — Two validator checks pin text in `keel/config.yaml`:
  - the header paragraph containing "independent declarations live here" must name every declaration;
  - the four-line vocabulary comment must appear exactly as written.
- F3 — For each pair of `docs/*.md` and `docs/*.zh-CN.md`, the heading counts compare as follows:
  - `shift-change`: 8 English and 5 Chinese, and the Chinese page lacks `keel patrol` and `keel tick`;
  - `chat-slack-setup`: 17 and 17, but the Chinese page lacks "Edits and deletions carry over.";
  - `cli-team`: 7 and 7.
- F4 — `codex-validation`, `resource-lock`, and `updating` have no Chinese page. Neither the owner nor #413 asked for new ones, so this change creates none.

## Decisions

- D1 — `keel/config.yaml` documents each declaration once, in `CONFIG_DECLARATIONS` order. Each block sits directly above its declaration when this repository declares one. The two pinned texts stay verbatim.
- D2 — `docs-zh-match-english` covers every `docs/*.zh-CN.md` that exists. For each, it requires:
  - equal heading counts with its English page;
  - equal code-fence counts;
  - every `keel <word>` command the English page names.

  A new Chinese page is checked the moment it exists.
- D3 — The README's Commands block keeps mirroring `keel --help` and adds one line pointing to each group's own help, rather than copying subcommand lists that already have a home.
