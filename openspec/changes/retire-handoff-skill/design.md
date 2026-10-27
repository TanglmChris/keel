## Facts

- F1 — The plugin's skills ship from `plugins/keel/skills/`; `src/skills/` is the source copy, without the Claude-only `argument-hint`. The CLI installs no skill into a project (`scripts/install_to_repo.py` names none), so a project loses `/keel:handoff` at its next plugin update with nothing to clean up.
- F2 — `keel context` validates HANDOFF on its own (`src/core/context.js`): unsupported schema, repeated, missing, or unexpected fields, and unsupported action each yield a reason. The skill is not needed to enforce the format.
- F3 — The skill was the only user-facing place that listed the four fields and the five actions. `keel --help` says only "an optional keel-handoff/v1 pointer override".
- F4 — `docs/shift-change.md` (and its zh-CN copy) already says the shift note "is not `keel/HANDOFF.md` either, and `keel context` does not read it".
- F5 — Validation references the skill in `hosts.py` (`SLASH_SKILLS`, the old-name pattern), `baseline.py` (`CORE_KEEL_SKILLS`), `common.py` (`SKILL_DOC_REQUIREMENTS`), `contract.py` (`handoff_skill_snippets`), and `docs.py` (`review-checklist-conditional-checks`). `install.py`'s uninstall scenario checks that a legacy `.claude/skills/handoff` copy is removed, which stays true.

## Decisions

- D1 — Delete `plugins/keel/skills/handoff/` and `src/skills/handoff/`, drop `handoff` from `KEEL_SKILLS` in `bin/keel.js`, the `/keel:handoff` rows from both command lists, and "and handoff hygiene" from the Codex plugin's `longDescription`.
- D2 — `keel --help` states the format in its Project layout section: YAML front matter with `schema: keel-handoff/v1`, `owner` (a pointer into `openspec/changes/<change>/`), `action` (`discuss`, `author`, `task-start`, `task-complete`, or `change-close`), and `reason`, and nothing else. Both READMEs say the same beside `keel context --clear-handoff`.
- D3 — The checklist requirement's handoff clause now requires `docs/shift-change.md` to tell the shift note apart from `keel/HANDOFF.md`, and its check reads that file.
- D4 — Validation follows: the skill lists drop `handoff`; `contract.py`'s skill snippets are checked against `keel --help`'s source instead; `common.py`'s skill-doc entry is removed.
