## Purpose

Define stateless continuity resolution, the versioned context result, and the optional validated HANDOFF override.
## Requirements
### Requirement: Keel continuity is stateless

Keel MUST compute continuity from current durable inputs and MUST NOT persist active change, selected task, session identity, execution cursor, capability state, or a working-tree baseline.

#### Scenario: Repeated context calls recompute current state
- **WHEN** `keel context` runs twice and OpenSpec state changes between the calls
- **THEN** the second result reflects the current OpenSpec state
- **AND THEN** Keel does not read a prior context result or Keel-owned state cache

#### Scenario: Native runtime state is not continuity authority
- **WHEN** a target runtime has goals, todos, memory, transcripts, checkpoints, or subagent state
- **THEN** Keel does not require or treat those surfaces as the durable owner of the current change, task, evidence, or follow-up

### Requirement: Keel resolves continuity conservatively
Keel MUST resolve continuity in the order explicit selection, valid HANDOFF override, unique actionable OpenSpec inference, then a non-ready status. Keel MUST classify authoring, executable task, and change-close owners as actionable, MUST NOT let storage-only zero-task backlogs compete with them, and MUST NOT use Git dirty state to choose a change or task.

#### Scenario: Explicit selection wins
- **WHEN** `keel context` receives a valid explicit change or task selection
- **AND WHEN** a different valid HANDOFF or inferred owner exists
- **THEN** the result selects the explicit owner
- **AND THEN** `selection.source` is `explicit`

#### Scenario: HANDOFF overrides inference
- **WHEN** no explicit selection is supplied
- **AND WHEN** a valid HANDOFF names a durable owner and action
- **THEN** the result uses that owner and action
- **AND THEN** `selection.source` is `handoff`

#### Scenario: Unique actionable OpenSpec state is inferred
- **WHEN** no explicit selection or HANDOFF exists
- **AND WHEN** exactly one authoring, executable-task, or change-close owner is actionable
- **THEN** the result selects that owner and action
- **AND THEN** `selection.source` is `inferred`

#### Scenario: Incomplete authoring remains actionable
- **WHEN** a scaffold or proposal has required OpenSpec artifacts still pending
- **THEN** context may identify its authoring action
- **AND THEN** it is not hidden merely because it has no executable task yet

#### Scenario: Storage-only standing backlog does not create ambiguity
- **WHEN** a change directory contains no proposal, design, specs, or task checkboxes and serves only as a zero-task follow-up store
- **THEN** context excludes it from actionable inference and reports a warning
- **AND THEN** explicit selection can still inspect it

#### Scenario: Invalid no-task change blocks instead of disappearing
- **WHEN** a change has authored proposal, design, specs, or a tasks artifact but cannot produce a valid next authoring, task, or close action
- **THEN** context reports it as blocked or ambiguous with the missing authority
- **AND THEN** it is not treated as a harmless storage-only backlog

#### Scenario: Multiple candidates are not guessed
- **WHEN** no explicit selection or HANDOFF exists
- **AND WHEN** multiple actionable OpenSpec owners or next actions are plausible
- **THEN** the result status is `ambiguous`
- **AND THEN** the result explains the candidates without selecting one

#### Scenario: Dirty paths are warnings only
- **WHEN** Git reports uncommitted paths
- **THEN** the context result may include those facts in `warnings`
- **AND THEN** the dirty paths do not determine `selection`

### Requirement: Keel context has one versioned result contract

`keel context` MUST expose JSON with `schemaVersion: 1`, one of `ready`, `ambiguous`, `blocked`, or `idle`, an optional selection, one supported next action, a minimal read list, reasons, and warnings. Human-readable output MUST render the same result.

#### Scenario: Ready context identifies the next action
- **WHEN** continuity resolves to one executable task whose contract is not yet complete
- **THEN** JSON status is `ready`
- **AND THEN** the selection identifies the change and task
- **AND THEN** `nextAction.kind` is `task-start`

#### Scenario: Evidence-ready unchecked task needs completion
- **WHEN** one unchecked task has all required command and Review evidence
- **THEN** the result identifies that task
- **AND THEN** `nextAction.kind` is `task-complete`

#### Scenario: Completed change needs close
- **WHEN** all tasks in the unique active change are complete
- **AND WHEN** the change has not completed its close action
- **THEN** `nextAction.kind` is `change-close`

#### Scenario: Non-ready domain state is not an operational error
- **WHEN** context computation succeeds with `ambiguous`, `blocked`, or `idle`
- **THEN** the command returns a successful process status
- **AND THEN** the JSON status and reasons describe the domain result

#### Scenario: Context parsing failure is operational
- **WHEN** Keel cannot parse required OpenSpec or HANDOFF input
- **THEN** the command reports an operational error distinct from a computed `blocked` result

### Requirement: HANDOFF is an optional validated override

Keel MUST treat an absent `keel/HANDOFF.md` as normal inference and MUST accept a new HANDOFF only when it contains `keel-handoff/v1` front matter with `owner`, `action`, and `reason`.

#### Scenario: New install omits HANDOFF
- **WHEN** Keel initializes or installs into a repository without `keel/HANDOFF.md`
- **THEN** Keel does not create the file
- **AND THEN** `keel context` remains usable through inference

#### Scenario: Valid override remains pointer-only
- **WHEN** HANDOFF uses `schema: keel-handoff/v1`
- **THEN** it contains only a durable owner pointer, supported action, and concise reason
- **AND THEN** it does not copy task progress, evidence, expectation state, or a conversation summary

#### Scenario: Stale override blocks instead of falling through
- **WHEN** HANDOFF points to a missing or completed owner
- **THEN** context status is `blocked`
- **AND THEN** Keel does not silently select a different inferred owner

#### Scenario: Legacy HANDOFF is preserved
- **WHEN** install, update, check, or doctor encounters a user-authored pre-v1 HANDOFF
- **THEN** Keel preserves its bytes
- **AND THEN** diagnostics identify it as legacy and describe explicit migration or clearing

#### Scenario: Clearing restores inference
- **WHEN** the user explicitly clears the HANDOFF override
- **THEN** the override is removed without changing its durable owner
- **AND THEN** the next context call returns to normal inference

### Requirement: Stateless continuation reconstructs fingerprinted task authority
Keel MUST reconstruct the selected task capsule from current OpenSpec artifacts on every start, resume, handoff, compaction, or worktree move and compare it with the fingerprint recorded in durable task evidence. It MUST NOT persist a session identity, execution cursor, or capsule cache as continuity authority.

#### Scenario: Matching fingerprint resumes
- **WHEN** a selected task has a recorded start fingerprint and fresh compilation matches it
- **THEN** context identifies the task's current start or completion action from durable Evidence
- **AND THEN** native session, goal, or transcript identity is unnecessary

#### Scenario: Fingerprint mismatch blocks continuation
- **WHEN** fresh compilation differs from the recorded start fingerprint
- **THEN** context is blocked with a contract-drift reason
- **AND THEN** it does not project or execute the changed task until explicit reauthorization

#### Scenario: No start anchor means task-start
- **WHEN** an executable task has no recorded start fingerprint
- **THEN** context selects `task-start`
- **AND THEN** existing product diffs or native progress do not substitute for the missing durable anchor

### Requirement: Minimal bootstrap preserves continuity without native plugin state
Keel v4 MUST install one concise AGENTS managed block that preserves the invariant continuity and ownership rules when the native plugin or hook is absent. Claude projects MUST import that AGENTS file without duplicating the full Keel protocol.

#### Scenario: Bootstrap is concise and idempotent
- **WHEN** Keel initializes or refreshes a repository repeatedly
- **THEN** AGENTS contains exactly one managed block under the defined size budget
- **AND THEN** user-authored content outside the block is byte-preserved

#### Scenario: Claude imports AGENTS
- **WHEN** a Claude project has or receives Keel bootstrap guidance
- **THEN** CLAUDE.md contains one effective `@AGENTS.md` import while preserving user-authored Claude-specific text
- **AND THEN** Windows does not require a symlink

#### Scenario: Hook is absent but continuity works
- **WHEN** plugin SessionStart projection does not run
- **THEN** the current agent follows the bootstrap to run `keel context`
- **AND THEN** OpenSpec/Git selection, task capsule, and gates remain correct without native state

### Requirement: Legacy resident protocol migration is conservative
Keel MUST replace only its known managed full-protocol block with the minimal v4 bootstrap and MUST preserve unknown or user-modified resident content.

#### Scenario: Known v3 managed block migrates
- **WHEN** AGENTS or CLAUDE contains a recognized Keel v3 managed block
- **THEN** update replaces that block with the v4 bootstrap/import shape
- **AND THEN** surrounding content remains byte-preserved

#### Scenario: Modified or legacy content is uncertain
- **WHEN** resident Keel-looking content cannot be matched to a known managed version
- **THEN** update preserves it and reports the path and manual resolution
- **AND THEN** it does not append a conflicting second full protocol silently

### Requirement: Single-task automation authorization is durable but not session state
Keel MUST record explicit automation authorization and its start fingerprint in the selected OpenSpec task Evidence, and MUST NOT persist a Keel execution cursor, goal identifier, turn count, retry counter, or session identifier.

#### Scenario: Another agent or session takes over
- **WHEN** a current agent starts in a checkout containing one incomplete task with valid single-task authorization
- **THEN** it recomputes that explicitly named task and fingerprint before continuing
- **AND THEN** it does not depend on the previous transcript, native goal identifier, or Keel cache

#### Scenario: Authorization does not match current authority
- **WHEN** the recorded task or fingerprint differs from the recomputed capsule
- **THEN** context reports a blocked automation continuation
- **AND THEN** the current agent performs no product writes until the user reauthorizes the repaired task

### Requirement: Continuity never chains tasks
Keel MUST treat completion or invalidation of the authorized task as the end of that automation authorization.

#### Scenario: Authorized task is complete
- **WHEN** context observes that the authorized task is durably checked
- **THEN** it reports the single-task run ended
- **AND THEN** it does not infer authorization for the next incomplete task

#### Scenario: Multiple active changes remain
- **WHEN** other changes or tasks are actionable after the authorized task ends
- **THEN** normal conservative context may report them as candidates
- **AND THEN** no candidate is projected into a goal without new explicit authorization

### Requirement: The context projection names the Keel that produced it

`keel context` MUST state the Keel version that produced its answer, on the surface the protocol already requires an agent to read. The resident protocol MUST ask the agent to report that version beside the protocol version the repository declares, so a disagreement reaches the human without depending on any runtime component being current.

This placement is required rather than incidental. A version check that lives only inside the plugin cannot report its own absence: when the installed plugin predates the check, its silence is indistinguishable from three versions agreeing. The repository is the only participant that cannot be stale, because the working tree is what every runtime reads.

Keel MUST NOT install, update, or select a version. It reports.

#### Scenario: The context answer carries its own version
- **WHEN** `keel context` reports a status
- **THEN** the output names the Keel version that produced it
- **AND THEN** the version appears for every status, including idle and failure results, because a result that omits it cannot be compared

#### Scenario: The protocol asks for the comparison
- **WHEN** an agent reports the context result at session start
- **THEN** the resident protocol requires it to state the Keel version that answered beside the protocol version the repository declares
- **AND THEN** the requirement does not depend on the SessionStart hook having run, so a runtime too old to carry the comparison does not suppress it

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

### Requirement: A Covers citation is not a record of what it cites
A `Covers` field in an active `tasks.md` MUST be exempt from the rules that read prose for recorded commit, merge, and dirty state, and from the contextual commit-hash rule. A Covers entry is a citation whose segments must resolve to a requirement or scenario that exists in a spec, or to a design reference in the change's own design; naming a requirement about dirty state is not recording dirty state, and refusing it leaves an author no repair except renaming the requirement.

The exempt region MUST be the whole `Covers` field as the task contract compiler bounds it — the label line and every line under it up to the next field label — and not the label line alone, because every citation is written on a line below the label.

Every line outside a `Covers` field MUST still be read by both rules, so that exempting a citation does not exempt the evidence around it.

#### Scenario: A citation naming a requirement about dirty state is accepted
- **WHEN** an active `tasks.md` cites a published requirement whose name contains `dirty`, `uncommitted`, or `commit hash`
- **THEN** `keel --check` reports `keel state: ok`
- **AND THEN** no `state-error` names any line of that `Covers` field

#### Scenario: The exemption is the field and not the label
- **WHEN** the citations sit on the lines below a `- Covers:` label rather than on the label line
- **THEN** those lines are exempt

#### Scenario: Prose outside the Covers field is still refused
- **WHEN** the same wording that is exempt inside a `Covers` field appears in an `Evidence` or `Verify` line of the same task
- **THEN** `keel --check` reports `keel state: failed` and names that line

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
