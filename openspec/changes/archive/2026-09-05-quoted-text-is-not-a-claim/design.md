## Context

`check_tasks_semantics()` in `scripts/install_to_repo.py` scans every line of every active `tasks.md` with four wording patterns (`TASKS_COMMIT_STATUS_PATTERNS`) and one contextual-identifier pattern (`TASKS_CONTEXTUAL_HASH_RE`). It has two exemptions today: `is_tasks_rule_line()` skips a line that *states* the rule, and `covers_field_lines()` skips the whole `Covers` field. Everything else on a line is read as an assertion about this repository.

Two reports say that reading is too wide. Issue #65 (items 2 and 4) says quoted material is still read; issue #103 says a Chinese general verb is read as a Git word. The owner ruled on both on 2026-09-05, and declined #65 item 3 (degrading the failure to a warning) in the same ruling.

## Goals / Non-Goals

**Goals:**
- Stop refusing lines whose match sits inside quoted material.
- Stop refusing `提交` where nothing on the line says the subject is Git.
- Keep every existing true positive refused, and keep the failure level.

**Non-Goals:**
- Changing what a real recorded commit identifier or a real recorded state claim is.
- Touching `unresolved-covers`, the task-contract compiler, or any gate. This change is confined to the project-state check.
- Downgrading `keel state: failed` to a warning (#65 item 3, declined).
- Widening the hash rule's own context-word list (#65 item 1's unquoted residual).

## Decisions

F1 — Corpus measurement, this repository's 35 archived `tasks.md`, 8,169 lines, 2026-09-05 against 5.41.0: the rules fire on 91 lines. Removing inline-code spans clears 13; additionally removing quotation spans clears 8 more; 70 stay refused. Zero of the 91 sit inside a fenced code block. Basis: scripted count over `openspec/changes/archive/**/tasks.md` using the module's own compiled patterns.

F2 — `TASKS_COMMIT_STATUS_PATTERNS[2]`, the Chinese state-word pattern, matches **zero** lines in that corpus, because this repository's own `tasks.md` are written in English. Basis: same count. The evidence for #103 is therefore external — `openspec/changes/add-iap-unlock-and-reminders/tasks.md:303` in a consuming repository — plus a synthetic reproduction run against the current tree on 2026-09-05, which confirmed the asymmetry: `用户当天**已提交**能填的商户与结算资料` is refused and `the user has submitted the merchant paperwork` is not.

F3 — Archived `tasks.md` are not scanned; `check_tasks_semantics()` skips any path whose first segment under `changes/` is `archive`. Basis: `scripts/install_to_repo.py`. F1 is therefore a corpus measurement of authored wording, not a count of live `state-error`s.

F4 — `withoutInlineCode()` in `src/core/task-contract.js` already establishes "an inline code span holds quoted content, not an assertion" for the field-concreteness reader, and strips only after the emptiness test so a field that is entirely one code span is not mistaken for empty. Basis: source, read 2026-09-05.

D1 — A quoted span is citation and is removed from the line before either rule family reads it. The spans are inline code, a fenced code block, and a quotation span. Basis: F4 states the shape for one reader in this codebase; the two reports are the same shape reaching a second reader. A line that is entirely quoted material is therefore never refused, and text outside the quotes on the same line is still read — this is a narrowing of what is read, not an exemption of the line.

D2 — Fenced code blocks are included even though F1 measures zero instances of them. Basis: the rule this change writes into the spec is "quoted material is not a claim," and a three-backtick fence is the same construct as a one-backtick span. Accepting one and refusing the other would put the implementation at odds with its own stated rule — the defect shape #49 reported, where two sections of one file did the same job two ways. The zero count is stated rather than hidden: this half is justified by consistency, not by a measured failure.

D3 — The `提交` family (`已提交`/`未提交`/`待提交`/`尚未提交`) refuses a line only when a Git context word appears on that line. The `合入` family (`未合入`/`待合入`/`已合入`/`合入 master|main`) keeps matching bare. Basis: 合入 names the Git act and has no ordinary-prose reading, while 提交 is an ordinary transitive verb whose object is usually not code — 提交资料, 提交审核, 提交申请. Requiring context is the same construction the contextual-identifier rule already uses for a hash-shaped token, so the two rules answer "is this line about Git" the same way.

D4 — The Git context words for D3 are a list of their own, not a reuse of `_HASH_CONTEXT_WORD`. Basis: that list contains `提交` and `合入` themselves, because it exists to let a state word supply context to a hash-shaped token; reusing it for D3 would let `已提交` supply its own context and change nothing.

D5 — The failure level is unchanged: a match still makes `keel --check` report `keel state: failed`. Basis: the owner declined #65 item 3 on 2026-09-05. Making every true positive quieter to stop the false positives is the worse trade once the false positives are gone.

D6 — The quotation spans are the ASCII double quote and the CJK pairs `“…”`, `「…」`, `《…》`. The ASCII single quote is excluded. Basis: an apostrophe is not a quotation delimiter, and a single-quote span would swallow the remainder of any line containing `doesn't`.

## Hidden Knowledge / Assumptions

A1 — The `提交` phrasings a Git context word must catch are assumed to be the ones an author writes beside a Git noun: `git`, `commit`, `master`, `main`, `HEAD`, `branch`, `PR`, `merge`, and the Chinese `分支`, `仓库`, `代码库`, `代码`, `合入`, `工作区`, `暂存`. A bare `这波已提交` with no Git noun anywhere on the line becomes a false negative. Basis: no corpus evidence exists (F2), so the list is inferred from the phrasings in the reports. Owner: https://github.com/TanglmChris/keel/issues/106 — filed for this list specifically; a real miss is recorded there and the list widens.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- **A genuine commit hash written inside backticks is no longer refused.** This is the cost the owner accepted, and it is the shape #65 item 2 warned about explicitly. It is bounded on three sides: text outside the quotes is still read, `Evidence` recording a hash as a bare token is untouched, and the wording patterns still refuse a state claim written in prose beside the quoted hash.
- **D3 trades false positives for false negatives.** A recorded commit state phrased with no Git noun passes. Per #58, that is the cheaper failure: a false positive costs a rewording round trip *and* teaches the reader to stop reading the check, while a false negative costs one line of stale prose that Git contradicts.
- **The change is loosening.** Nothing that passes today starts failing. Rollback is a revert of one file.

## Open Questions

None.
