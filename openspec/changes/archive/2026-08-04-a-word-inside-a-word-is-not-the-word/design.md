## Context

`check_tasks_semantics()` in `scripts/install_to_repo.py` walks every non-archived `tasks.md` line by line and applies two families of rule: `TASKS_COMMIT_STATUS_PATTERNS`, which reads wording (`commit hash`, `dirty`, `已提交`, `merged into main`), and `TASKS_CONTEXTUAL_HASH_RE`, which pairs a context word with a hash-shaped token. Both are regular expressions over a whole line, with one escape hatch: `is_tasks_rule_line()` skips a line that states the rule itself.

5.19.0 repaired the token half of the contextual rule — a decimal run is not a hash — and its design D3 explicitly left the other half alone, on the grounds that "how the check recognizes a commit hash" is the repository's to decide while "which lines the rule refuses" is the owner's. #65 collects the residue. The owner answered it on 2026-08-04, choosing between two boundary forms and separating the Covers question from the backtick question. This change implements that answer.

## Goals / Non-Goals

**Goals:**
- A context word supplies context only when it appears as a word.
- Inflected forms of the context words keep supplying it, because they are the words authors actually write in evidence prose.
- A Covers citation is not read as a record of the state it cites.
- Every true positive in this repository's corpus survives, verified individually.

**Non-Goals:**
- Exempting backticked text (#65 §2). Declined in 5.19.0 D3 because a real commit hash is most often written in backticks, so exempting them weakens the rule instead of repairing the criterion. This change surfaces no new fact about it.
- Downgrading a violation to a warning (#65 §3). Declined in 5.19.0 D3 because it repairs a false positive by making every true positive quieter.
- Any change to the token criterion. `_HASH_SHAPED_TOKEN` is untouched.
- Exempting any other field. `Verify`, `Touch`, and `Evidence` are prose or paths that an author writes freely; only `Covers` is a citation whose content must exist elsewhere.

## Decisions

- **F1** — the four defect shapes reproduce at 5.28.0 through the shipped CLI. On a scratch repository built with `node bin/keel.js --install`, one active `tasks.md` produces four `state-error` lines: a Covers citation of `keel-core-gates / Dirty-worktree attribution is conservative / …` refused for dirty state, a Covers citation naming a requirement with `commit hash` in it refused for commit wording, and two evidence lines refused as contextual commit hashes because they contain `remaining` and `heading`. A fifth line, `committed a1b2c3d4e5f6`, is refused correctly and is the control. *Basis: direct execution, 2026-08-04.*
- **F2** — the contextual rule's corpus behavior, measured over all 53 `tasks.md` under `openspec/` including archived ones: 12 lines refused before, 8 after, **0 newly refused**. The 4 that change are `openspec/changes/archive/2026-07-20-align-record-anchor-template/tasks.md:23` and `…/2026-08-01-the-runtime-says-which-version-it-is/tasks.md:50` on `remaining`, and `…/2026-07-28-the-gate-reads-what-it-promises/tasks.md:21` and `…/2026-08-01-declare-who-runs-the-task/tasks.md:64` on `heading`. Every hex token on those four lines is a `sha256:` contract anchor or a recompiled capsule fingerprint — `01b9e740`, `3ba2bd7b`, `2f723a87…a541d17`, `4a44890b` — read individually rather than counted. *Basis: running both expressions over the corpus and reading each changed line.*
- **F3** — the Covers rule's corpus behavior: **11 lines** inside a `Covers` field are refused by `TASKS_COMMIT_STATUS_PATTERNS`, spread across 4 changes. 8 of them cite `keel-core-gates / Dirty-worktree attribution is conservative` or `keel-touch-write-guard / The manifest records what was dirty when the task started` — requirements published in `openspec/specs/` today — and the rest cite design references in the same field. #65 reports only the `commit hash` case, which is one change's three lines. *Basis: the same corpus run, bounding the Covers field as F6 describes.*
- **F4** — `TASKS_COMMIT_STATUS_PATTERNS` has been in `scripts/install_to_repo.py` since the initial commit (`git log -S`, pickaxe over the dirty wording, returns one commit: `d92878b`). Every one of F3's 11 lines was therefore a live `state-error` for the whole time its change was active — the check has been refusing correct citations for the life of the project, quietly enough that the workaround (rename the requirement) was cheaper than the report. *Basis: `git log -S --pickaxe-regex`.*
- **F5** — all 165 `Covers:` labels in the corpus are the block form at exactly two spaces of indent, with the citations on the lines below. Not one is inline. So an exemption that skipped only the label line would change no verdict at all. *Basis: counting label forms across `openspec/**/tasks.md`.*
- **F6** — `parseTasks()` in `src/core/task-contract.js:97` bounds a field with `/^ {2}- ([A-Za-z][A-Za-z /-]+):\s*(.*)$/`: a field starts at such a line and holds every line until the next one. The Covers entries the contract compiler resolves are exactly the lines in that region. *Basis: reading the parser.*
- **F7** — **0** lines inside a Covers field are refused by `TASKS_CONTEXTUAL_HASH_RE`, before or after this change. The corpus cannot distinguish exempting the Covers field from that rule from not exempting it. *Basis: the same corpus run.*
- **D1** — the ASCII context words become `\b(?:commits?|committed|committing|master|main|HEAD|hash(?:es)?)\b`. This is the owner's decision on #65, chosen over the stricter `\b(commit|master|main|HEAD|hash)\b`: the strict form would also drop `committed` and `hashes`, which cost 4 real refusals in the corpus, and the owner's answer to "is that worth paying" was no. *Basis: the owner's recorded decision, and F2's line-by-line reading which confirms the 4 dropped lines are all false positives.*
- **D2** — the Chinese context words stay unbounded. `\b` is defined between a word and a non-word character, and every character of `提交` is a word character under Python's Unicode rules, so `\b提交\b` requires non-word neighbours and fails on `已提交`, `未提交`, and `该任务未提交，等待评审` — the exact strings the wording rule and the `decimal-runs-are-not-hash-shaped` fixture depend on. Verified by running both forms rather than reasoned about. *Basis: direct execution against all three strings.*
- **D3** — the exempt region is the `Covers` field as F6 bounds it, not the label line. F5 makes the label-only reading a no-op, so it is the only reading under which the owner's decision does anything. Computing it with the parser's own rule means the exempt region is exactly the set of lines the contract compiler reads as citations — the file cannot have a line that is a Covers entry for one tool and prose for the other. *Basis: F5, F6.*
- **D4** — the exemption covers both rule families, not only the wording patterns. F7 says the corpus cannot decide this, so it rests on the reason rather than on a measurement, and the reason is the same for both: a Covers entry is a citation, and its three segments must resolve to names that exist in a spec or to a `D<n>`/`F<n>/A<n>`/`Q<n>` in the change's own design. Exempting one rule and not the other would mean holding that a citation is a claim about commit state when it contains a hex token but not when it contains the word `dirty`, which is not a distinction anything in the file supports.
- **D5** — the residue is accepted and named: a genuine commit hash inside a Covers entry is no longer refused by this check. Two things bound it. A Covers entry that does not resolve is already refused as `unresolved-covers` by `task-contract.js`, so the hash would have to be part of a name that exists in a published spec; and the field is three-segment citations, not the place an author records what they did. The `Evidence` and `Verify` fields, where a hash actually gets pasted, are untouched.
- **D6** — the scenario asserts both directions and carries positive controls. A check whose passing condition is *acceptance* passes just as well when the rule stopped running altogether, so every accepted fixture is paired with a refused one in the same repository, and the refused ones are the true positives from the corpus rather than invented strings. *Precedent applied: `an-assertion-that-never-failed-proves-nothing` — the pattern to watch for is a check that passes on absence.*

## Hidden Knowledge / Assumptions

- **A1** — a Covers field's content is a citation in every schema this repository ships. The compact v4 template and all 165 corpus instances use `- Covers:` followed by `capability / requirement / scenario` or a `D<n>`/`F<n>`/`A<n>`/`Q<n>` reference. If a schema later allowed free prose under `Covers:`, the exemption would cover that prose too. *Basis: F5 and the shipped template. Owner: this design; no such schema exists or is proposed.*
- **A2** — `is_tasks_rule_line()` and the Covers exemption are independent skips and neither needs to know about the other. A Covers citation containing "source of truth" would be skipped twice, which is the same as once. *Basis: reading `check_tasks_semantics()`.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- Word boundaries make the rule quieter, and quieter is the direction a check degrades in. What bounds it here is F2: the change is not "refuse less", it is "refuse on a word", and every line it stops refusing was read individually and found to hold a fingerprint rather than a commit identifier.
- The Covers exemption is the first field-shaped exemption in this check, which invites the next one. The line that makes it principled is D4's: a Covers entry's content must exist somewhere else and is verified against that elsewhere. `Verify` and `Evidence` have no such second reader, so the argument does not extend to them.
- Two tools now bound a Covers field, in two languages, by rules that must agree. Mitigated by writing the Python bound from the JavaScript one verbatim and citing it in a comment, so a change to the field syntax shows up as a diff in both.

## Open Questions

None. #65's remaining two items are 5.19.0 D3's, unchanged.
