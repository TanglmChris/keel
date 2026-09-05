## Why

`keel --check`'s project-state rules read every line of an active `tasks.md` for state Git already owns. Two classes of text they read are not claims about this repository at all.

**Quoted material.** A line quoting a command, a log excerpt, a branch base, or the name of a requirement is citing something, not asserting it. Measured across this repository's 35 archived `tasks.md` (8,169 lines, 2026-09-05, 5.41.0): the rules fire on 91 lines, and 21 of those matches sit entirely inside backticks, a fenced block, or quotation marks — `` `git status --short` `` written as the command a Scope check ran, `` `68e4fd2` `` written as the branch base an `M1.red` ran against. `src/core/task-contract.js` established the shape for this in `withoutInlineCode()` — inline code is quoted content, not an assertion — and this checker never got it. Issue #65 items 2 and 4; the owner decided both on 2026-09-05.

**A general verb read as a Git word.** `TASKS_COMMIT_STATUS_PATTERNS[2]` matches `已提交`/`未提交`/`待提交`/`尚未提交` as bare words, requiring no Git identifier and no Git context on the line. Chinese 提交 is an ordinary transitive verb — 提交资料, 提交审核, 提交申请 — so an Evidence line recording that a user submitted merchant paperwork to a third-party review queue is refused as recorded commit state, while the same fact written in English (`has submitted the paperwork`) passes untouched. Reproduced against the current tree; the field report is issue #103, from `openspec/changes/add-iap-unlock-and-reminders/tasks.md:303` in a consuming repository.

Both are the failure #58 already named: a check that refuses correct work is one people learn to route around, and the cost of a false positive is that the true positives stop being read.

## What Changes

- A quoted span is read as citation rather than assertion. Inline code (`` `…` ``), a fenced code block, and a quotation span (`"…"`, `“…”`, `「…」`, `《…》`) are removed from a line before the recorded-state rules and the contextual commit-identifier rule read it. A line that is *only* quoted material is therefore never refused; text outside the quotes on the same line is still read.
- The `已提交`/`未提交`/`待提交`/`尚未提交` family refuses a line only when that line also carries a Git context word. The 合入 family (`未合入`/`待合入`/`已合入`/`合入 master|main`) keeps matching bare, because 合入 names the Git act and has no ordinary-prose reading.
- The existing whole-`Covers`-field exemption is unchanged and stays the narrower, field-shaped rule; the quoted-span rule applies everywhere including inside `Covers`.
- **Not changing**: the failure level. `keel state` stays `failed` for a real match rather than degrading to a warning — issue #65 item 3, which the owner explicitly declined on 2026-09-05, because making every true positive quieter is a worse trade than making the false positives stop.

## Capabilities

### Modified Capabilities
- `keel-stateless-continuity`: the "A context word is a word and not a substring" requirement states that the Chinese context words match wherever they appear and that `已提交`/`未提交` are refused whether or not a hash shares the line; the state-word half of that now requires Git context on the line, so the requirement and its Chinese scenario change and the hash-context half stays as written. The "A recorded commit identifier is recognized by what makes it one" requirement says the wording rule "holds for every line an author writes as a statement" without saying what makes a line a statement; a new requirement states that a quoted span is not one, and that requirement and "A Covers citation is not a record of what it cites" together bound what the rules read, so that requirement changes too — its second paragraph now names both bounds instead of leaving one to be inferred.

## Impact

- Affected code: `scripts/install_to_repo.py` — `TASKS_COMMIT_STATUS_PATTERNS`, `TASKS_CONTEXTUAL_HASH_RE`, and `check_tasks_semantics()`, which gains the quoted-span strip and the fenced-block skip.
- Affected tests: `scripts/validate_plugin.py` — new scenarios for the quoted-span rule and the Git-context requirement on the 提交 family; the existing Chinese-context scenario asserted the behavior this change removes and must move to a line that carries Git context.
- Direction is **looser**: lines this check refused now pass. Both halves are bounded — a real recorded hash or commit state written outside quotes is refused exactly as before, and `unresolved-covers` still refuses any `Covers` entry that does not resolve to a published name. Owner-decided (issues #103 and #65, 2026-09-05).
- No new dependency, no schema change, no CLI surface change.
