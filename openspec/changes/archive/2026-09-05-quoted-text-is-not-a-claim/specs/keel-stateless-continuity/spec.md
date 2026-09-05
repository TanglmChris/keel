## ADDED Requirements

### Requirement: A quoted span is a citation and not a claim

The project-state check MUST read a `tasks.md` line for recorded commit, merge, and dirty state, and for a contextual commit identifier, only outside its quoted spans. A quoted span is an inline code span, a fenced code block, or a quotation span delimited by `"…"`, `“…”`, `「…」`, or `《…》`. Quoted material is content an author cites — a command that was run, an excerpt of output, a branch base, the name of a requirement — and citing a thing is not recording it.

A line whose every match lies inside a quoted span MUST pass. Text outside the quoted spans on the same line MUST still be read by both rules, so quoting one token does not exempt the sentence around it.

The ASCII single quote MUST NOT delimit a quotation span, because an apostrophe is not a quotation mark and treating it as one would silence the remainder of any line containing a contraction.

This requirement bounds what the rules read for every line. It is independent of the `Covers` field exemption, which bounds which lines the rules read at all.

#### Scenario: A command quoted in evidence is not a recorded state claim
- **WHEN** an active `tasks.md` line records that a Scope check ran `git status --short`, written inside an inline code span
- **THEN** `keel --check` reports `keel state: ok`
- **AND THEN** no `state-error` names that line

#### Scenario: An identifier quoted as data is not a recorded identifier
- **WHEN** an active `tasks.md` line names the branch base an `M<n>.red` check ran against, with the hexadecimal token inside an inline code span or a fenced code block
- **THEN** `keel --check` reports `keel state: ok`

#### Scenario: A requirement name quoted in prose is not a record of what it names
- **WHEN** an active `tasks.md` line outside any `Covers` field names a published requirement whose name contains `commit hash`, written inside a quotation span
- **THEN** `keel --check` reports `keel state: ok`

#### Scenario: Prose beside a quoted token is still read
- **WHEN** an active `tasks.md` line quotes a hexadecimal token and, outside the quotes, records that the work is `uncommitted`
- **THEN** `keel --check` reports `keel state: failed` and names the line

#### Scenario: An apostrophe does not open a quotation span
- **WHEN** an active `tasks.md` line contains a contraction such as `doesn't` and, after it, records dirty or commit state in words
- **THEN** `keel --check` reports `keel state: failed` and names the line

## MODIFIED Requirements

### Requirement: A recorded commit identifier is recognized by what makes it one

Keel's project state check MUST refuse a commit identifier recorded in an active `tasks.md`, and MUST recognize it by the property that makes a token hexadecimal rather than by the length of a digit run. A run carrying no hexadecimal letter MUST NOT be reported as a contextual commit identifier, because a phone number, timestamp, order number, port, or numeric fixture is ordinary evidence prose and refusing it asks an author to reword something that was true.

Keel MUST keep refusing recorded commit, merge, and dirty state by its wording, independently of any digit run on the line, so that narrowing what counts as a hash does not narrow the rule. This holds for every line an author writes as a statement, and what makes a line a statement is bounded by two other requirements rather than left to be inferred: a `Covers` field is a citation of a name that exists elsewhere, and a quoted span is material the author cites. Neither is a record of state, and both are exempt from these rules.

#### Scenario: A decimal number in evidence prose is not an identifier
- **WHEN** an active `tasks.md` line holds a run of decimal digits beside a word such as `commit` or `提交`
- **THEN** `keel --check` reports `keel state: ok`
- **AND THEN** no `state-error` names that line as a contextual commit identifier

#### Scenario: A recorded hexadecimal identifier is still refused
- **WHEN** an active `tasks.md` line holds a hexadecimal token of identifier length beside such a word
- **THEN** `keel --check` reports `keel state: failed` and names the line

#### Scenario: Recorded commit wording fails on its own
- **WHEN** an active `tasks.md` records commit, merge, or dirty state in words, outside any quoted span, and carries no hash-shaped token
- **THEN** `keel --check` still refuses it

### Requirement: A context word is a word and not a substring
The project-state check MUST treat the ASCII context words that make a hash-shaped token a recorded commit identifier — `commit`, `master`, `main`, `HEAD`, `hash` — as whole words. A word that merely contains one of them, such as `remaining`, `heading`, `domain`, or `maintains`, MUST NOT supply the context, because a word inside another word is not that word and refusing the line asks an author to reword something that was true.

The inflected forms an author actually writes MUST keep supplying the context: `commits`, `committed`, `committing`, and `hashes` name the act the rule exists to catch.

The Chinese context words MUST keep matching wherever they appear when they supply context to a hash-shaped token, because a word boundary is not defined between two characters that are both word characters, and requiring one would stop `已提交` and `未提交` from matching at all.

Where a Chinese state word is the whole of what the rule matches, with no hash-shaped token on the line, the check MUST distinguish the two families. `未合入`, `待合入`, `已合入`, and `合入` before `master` or `main` MUST be refused on their own, because 合入 names the Git act and carries no ordinary-prose reading. `已提交`, `未提交`, `待提交`, and `尚未提交` MUST be refused only when the same line also carries a word naming Git or a Git object, because 提交 is an ordinary transitive verb — 提交资料, 提交审核, 提交申请 — and refusing it bare makes the check reject a Chinese sentence whose English translation it accepts.

#### Scenario: A word that merely contains a context word supplies no context
- **WHEN** an active `tasks.md` line carries a hexadecimal token beside a word such as `remaining` or `heading`, and no context word of its own
- **THEN** `keel --check` reports `keel state: ok`
- **AND THEN** no `state-error` names that line as a contextual commit hash

#### Scenario: An inflected context word still supplies it
- **WHEN** an active `tasks.md` line carries a hexadecimal token of identifier length beside `committed`, `commits`, or `hashes`
- **THEN** `keel --check` reports `keel state: failed` and names the line

#### Scenario: A Chinese context word needs no boundary
- **WHEN** an active `tasks.md` line carries a hash-shaped token beside `已提交` or `未提交`
- **THEN** `keel --check` reports `keel state: failed` and names the line

#### Scenario: A merge state word is refused on its own
- **WHEN** an active `tasks.md` line records `已合入` or `未合入` and carries no hash-shaped token and no other Git word
- **THEN** `keel --check` reports `keel state: failed` and names the line

#### Scenario: A submission verb without a Git word is ordinary prose
- **WHEN** an active `tasks.md` Evidence line records that a user `已提交` paperwork to a third-party review queue, and no word on that line names Git or a Git object
- **THEN** `keel --check` reports `keel state: ok`
- **AND THEN** the same fact written in English is accepted as it already was, so the check does not depend on which language the author wrote in

#### Scenario: A submission verb beside a Git word is still refused
- **WHEN** an active `tasks.md` line records `已提交` beside a word such as `main`, `分支`, or `代码`
- **THEN** `keel --check` reports `keel state: failed` and names the line
