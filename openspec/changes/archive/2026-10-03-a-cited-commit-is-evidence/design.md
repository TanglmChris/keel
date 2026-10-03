## Context

`check_tasks_semantics()` in `scripts/install_to_repo.py` reads each non-archived `tasks.md` line by line. It skips fenced blocks, rule-statement lines, and the `Covers` field, and it blanks quoted spans. It then applies `TASKS_COMMIT_STATUS_PATTERNS` and the submission rule, and `TASKS_CONTEXTUAL_HASH_RE`, which matches a context word and a hash-shaped token anywhere on the same line.

## Decisions

- **F1** — rtl_ppa_prj main `4dbc89f`, `openspec/changes/add-iecc-basic-verification/tasks.md`: the check under keel 5.90.2 reports lines 169, 262, 277, 278 (twice), 327, and 328 as a contextual commit hash or dirty state, and line 219 as dirty state.
  - Seven are in Evidence → Review fields (`Scope check`, `Acceptance check`).
  - Line 262 is an Acceptance criterion of task 5.1, which is checked, so rewording it moves its recorded fingerprint.
  - The context words that fire are not bound to the hash. Examples: `hashes identify actual 211dfb5`, `Shared HEAD is checked`, `before commit.` on the same line as `base dec4d6e`.
  - Basis: running `scripts/install_to_repo.py --target claude --check` against that checkout.
- **F2** — `keel-review-checklist` asks a Scope check to "identify an explicit base if deterministic comparison was used". The rule therefore refuses what the protocol asks for. Basis: `plugins/keel/skills/keel-review-checklist/SKILL.md`.
- **F3** — The existing fixtures that must stay refused all sit in Evidence fields:
  - `commit|commits|committed|committing|hashes a1b2c3d4e5f6 verified` (`a-context-word-is-a-word`);
  - `已提交|未提交|该任务尚未提交 a1b2c3d4e5f6`;
  - `the work is still uncommitted`, `the worktree is uncommitted` (`a-quoted-span-is-not-a-claim`);
  - `the worktree was dirty when the task started` (`a-covers-citation-is-not-a-record`).
  - Basis: `scripts/validate_plugin.py`.
- **D1** — A task field is the region from a two-space `- Name:` label (the compiler's bound, `TASKS_FIELD_LABEL_RE`) up to the next line indented less than two spaces that is not blank. Inside it, the contextual-hash rule matches only a bound form:
  - a context word, then at most punctuation and an optional `is|was|now`, then an optional `at|as|to|into|onto|in|on`, then the hash;
  - or the hash, then an optional `is|was`, then `committed|merged|pushed`;
  - or a Chinese context word, then at most four non-space characters, then the hash.

  Basis: F1, F3, and the owner's choice (2026-10-03) to relax within every task field rather than Evidence only.
- **D2** — Inside a task field, the dirty rule matches:
  - `dirty|uncommitted` directly after `is|are|was|were|remain(s|ed)|stay(s|ed)|left`, with at most one of `still|now|yet` between;
  - or a `Status|State` label whose value is `dirty|uncommitted`;
  - or `not (yet )?committed|pending commit`, unchanged.

  An attributive or negated use does not match. Basis: F1 and F3.
- **D3** — Outside task fields, every rule stays line-wide and unchanged. The commit-hash wording, merge, and submission rules are unchanged everywhere. Basis: the issue asks only for provenance in fields, and a ledger usually lands in a title line or a notes section.

## Risks / Trade-offs

- A state claim phrased loosely inside a field passes. An example is "work on main, last at a1b2c3d", where `at a1b2c3d` is not bound to a context word. Fingerprints, gates, and Review still hold the contract. This rule only discourages ledgers, and refusing provenance (F2) costs more than the miss.
