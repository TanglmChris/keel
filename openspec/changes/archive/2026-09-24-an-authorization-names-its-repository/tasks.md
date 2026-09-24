# Tasks

## 1. A grant names the repository it reaches

- [x] 1.1 `authorize:` accepts `issue:<owner>/<repo>` as a scoped entry, refuses the bare `issue` with the form it requires, refuses a malformed scope by name, and keeps the whole declaration failing closed when any entry is refused
  - Covers:
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary / A tracker action is declared with the repository it reaches
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary / A bare tracker action is refused with the form it needs
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary / A malformed scope is an unrecognized entry
    - keel-standing-authorization / A scope is a declaration Keel carries and never enforces / The scope's shape is checked and its existence is not
    - F1
    - F3
    - D1
    - D3
  - Read:
    - src/core/config.js
    - openspec/changes/an-authorization-names-its-repository/design.md
  - Touch:
    - src/core/config.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `an-authorization-names-its-repository` scenario drives `keel --doctor` against a fixture repository whose `authorize:` lists `commit` and `issue:acme/widgets`. The `authorize` line reports `ok` and names both entries, so the scoped form is accepted rather than reported as a typo. Fails with: `a scoped tracker entry was refused`
    - M2: the same scenario, against a fixture declaring a bare `issue`. The `authorize` line reports `failed`, and the message names both the entry and the `issue:<owner>/<repo>` form it requires — the second half is what is new, because a bare `issue` is already refused today by simply not being in the vocabulary, and a check asserting only the refusal would have passed before this task existed. Fails with: `does not name the form it requires`
    - M3 (regression): a fixture declaring `issue:acme` and one declaring `issue:acme/widgets/extra` are each reported `failed` with the offending entry named, and a fixture declaring `issue:acme/widgets` alongside `commit` authorizes neither when a third entry is unrecognized — so shape is checked, and fail-closed is unchanged by the new form. No network call is made for any fixture; the scoped repositories do not exist.
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario standing-authorization-declaration` and `--scenario standing-authorization-sync-confusion` pass unchanged, so what the four existing names accept, refuse, and report is untouched.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if accepting the scoped form requires `configList` to change, because F1 records that its item pattern already returns `issue:acme/widgets` as one token and a reader change would mean the diagnosis was wrong.
    - Stop if the matcher has to special-case the literal string `issue`, because the design records the scoped form as a property an action declares, not a name the matcher knows.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:fa56a62f26ff008f15e94d5a52f99334bb15718687c32f1c5a0c4c7da21476f3
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario an-authorization-names-its-repository` reports `an-authorization-names-its-repository scenario passed.` Against a fixture declaring `commit` and `issue:acme/widgets`, `keel --doctor`'s `authorize` line reports `ok` and names both entries. The ordinary entry beside it is asserted to keep its authorization, so the assertion is that the scoped entry *joined* the declaration rather than that the block parsed at all — `acme/widgets` does not exist and no network call is made for it.
    - M1.red: fail, for the declared reason, taken against the five-name vocabulary this task replaces. `an-authorization-names-its-repository: a scoped tracker entry was refused. \`gh\` is account-wide, so this is the one entry that has to name its repository, and it is the one the vocabulary rejects.` Carries the declared signature `a scoped tracker entry was refused`.
    - M1.green: pass. Same command after `issue` entered the vocabulary as a scoped action and `classifyAuthorizationEntry` split the entry into action and resource.
    - M2: pass. Against a fixture declaring a bare `issue`, the `authorize` line reports `failed` and the message names both the entry and the `issue:<owner>/<repo>` form, in two places that were both written for it: the accepted-names list now spells the scoped names with their form, so it is copyable rather than a name the next message refuses, and a dedicated sentence says the credentials are account-wide and an unscoped grant would reach every repository the account can touch. The refusal alone is deliberately not the assertion — a bare `issue` was already refused before this task by not being a name at all, so a check asserting only that would have passed against the code this replaces.
    - M2.red: fail, for the declared reason, taken from the real intermediate state rather than from the starting one: `issue` already in the vocabulary and the scoped form already accepted (M1 green), with the accepted-names list still spelling `issue` bare and the missing-scope sentence not yet written. `an-authorization-names-its-repository: the bare-entry refusal does not name the form it requires, so a reader is told \`issue\` is not a name rather than that it is a name needing a scope.` Carries the declared signature `does not name the form it requires`. Taking it here rather than at the start is what makes it M2's red and not a second sighting of M1's.
    - M2.green: pass. Same command after both halves of the message were written.
    - M3: pass. Inside the same run: `issue:acme`, `issue:acme/widgets/extra`, `issue:/widgets`, and `issue:acme/` are each reported `failed` with the offending entry named — both sides of correct, a missing segment and an extra one, plus an empty segment on each side. A fixture declaring `issue:acme/widgets` beside `deploy` authorizes nothing and names `deploy`, and `issue: authorized` is asserted absent from that output, so the new form did not create a path around fail-closed. No fixture's repository exists and no network call is made for any of them, which is the shape check standing alone.
    - M4: pass. `standing-authorization-declaration`, `standing-authorization-sync-confusion`, `standing-authorization-inheritance`, `standing-authorization-never-weakens`, and `continuation-authorization` all report `scenario passed.` unchanged. What the five existing names accept, refuse, report, and inherit is untouched, including the `sync` sentence that shares the message function this task rewrote.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a tracker grant names the repository it reaches and the bare form is refused with the form it requires. Both are proven through `keel --doctor` — the surface an owner actually reads — against fixture repositories, not by calling the parser directly. The pair M1/M2 is where the care went: M1's red is the starting state and M2's is the state after M1 was green, so neither check is carried by the other, and M2's assertion was written specifically to exclude the half that was already true. M3 is honest about being a regression: every one of its assertions holds against the vocabulary this replaces, which refused any entry containing a colon for the simpler reason that no such name existed, and the gate's own prompt is what surfaced that before the evidence was written rather than after.
      - Scope check: `git status --short` shows `src/core/config.js` and `scripts/validate_plugin.py` — exactly this task's Touch — plus this change's own untracked directory. `keel gate task-complete` compared the worktree against the dirty set recorded at task-start. The Stop Rules both held: `configList` is unchanged, because its item pattern already returned `issue:acme/widgets` as one token; and the matcher keys on `SCOPED_AUTHORIZATION_ACTIONS`, a set an action is a member of, rather than on the literal string `issue`. `bin/keel.js` is deliberately untouched and its per-action loop still reports `issue: not authorized` for a declared scoped entry — that contradiction is task 1.2's subject and its red.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: M3 was tagged `(regression)` before any Evidence was recorded, so nothing was invalidated. Its assertions — a malformed scope refused with the entry named, and a valid scoped entry failing closed beside an unrecognized one — are all satisfied by the vocabulary this task replaces, which refused every entry containing a colon for the plainer reason that no such name existed. The check has no honest red, and manufacturing one would have meant breaking fail-closed on purpose to watch it break.

- [x] 1.2 `keel --doctor`'s per-action line reports a scoped entry as authorized and names the scope, instead of reporting `not authorized` for an action the line directly above has just listed as declared
  - Covers:
    - keel-standing-authorization / A scope is a declaration Keel carries and never enforces / The doctor reports the scope beside the action
    - F2
    - D2
    - D4
  - Read:
    - bin/keel.js
    - src/core/config.js
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: against the `issue:acme/widgets` fixture, `keel --doctor`'s per-action `issue` line reports it authorized and names `acme/widgets`. The contradiction is asserted as absent from the same output: the summary line lists the entry as declared and the per-action line no longer says `not authorized`. Fails with: `issue: not authorized`
    - M2: the same output states that Keel does not enforce the scope, so a reader cannot take the line for a sandbox — the one thing D2 records as unfixable by mechanism and therefore owed to wording.
    - M3 (regression): against a fixture declaring only `commit`, the per-action lines for `push`, `release`, `archive`, `continuation`, and `issue` all report `not authorized`, so the new rendering did not turn an undeclared action into a declared one.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if reporting the scope requires the doctor to resolve or contact the named repository, because D3 records that the shape is checked and existence is not.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d6bce75c913b53f3e9230827883e9b7b7e28a2be440b99dc4a2de72eec45683d
    - M1: pass. Against the `commit` + `issue:acme/widgets` fixture, `keel --doctor` now prints `issue: authorized - scoped to acme/widgets`, and the scenario asserts the scope appears on that line rather than anywhere in the output. `issue: not authorized` is asserted absent from the same output, so the two halves of the contradiction are checked together and not merely one replaced by the other.
    - M1.red: fail, for the declared reason. The per-action loop tested `declared.includes(action)` against a list holding `issue:acme/widgets`, so the same screen read: `authorize: ok - declared in keel/config.yaml: commit, issue:acme/widgets` on one line and `issue: not authorized` six lines below it. The scenario reported `the per-action line does not report the scoped entry as authorized and name its scope.` and printed the doctor output carrying the declared signature `issue: not authorized` verbatim.
    - M1.green: pass. Same command after the loop was keyed on the action — `scopes.has(action)` — rather than on the declared string.
    - M2: pass. The same output carries `scope: carried - Keel records a scope and does not enforce it — it invokes no tracker client and cannot observe one, so the boundary is kept by whoever acts, not by this check`, printed once and only where a scoped entry is declared, rather than repeated on every action line. This is the one thing D2 records as unfixable by mechanism and therefore owed to wording: a reader who takes the scope for a sandbox is relying on nothing.
    - M2.red: fail, for the right reason, taken from the intermediate state with M1 already green — the per-action line correct and the non-enforcement sentence not yet written. `an-authorization-names-its-repository: the output does not say Keel carries the scope without enforcing it, so a reader can take it for a fence.`
    - M2.green: pass. Same command after the note was written.
    - M3: pass. Against a fixture declaring only `commit`, the per-action lines for `push`, `release`, `archive`, `continuation`, and `issue` all report `not authorized`, so keying the loop on a map did not turn an undeclared action into a declared one. Correctly tagged regression: this held against the loop this task replaces, whose membership test gave the same answer for every unscoped case.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the doctor reports the scope beside the action and does not contradict itself. M1 asserts both sides of that on one output — the correct line present and the wrong line absent — because asserting only the first would pass a version that printed both. M2 covers the claim no mechanism can make true, and its red was taken after M1 was green so the two checks do not stand on the same failure. The output was also read by eye once against a live fixture, which is how the `scope: carried` line's placement was chosen: said once beneath the actions rather than appended to each, so it reads as a property of the declaration instead of a disclaimer on every row.
      - Scope check: `git status --short` shows `bin/keel.js` and `scripts/validate_plugin.py` — exactly this task's Touch — plus this change's own untracked directory. `scripts/validate_plugin.py` was already dirty from 1.1; what this task added to it is the per-action and non-enforcement assertions and the `only-commit` fixture. The Stop Rule held: the doctor resolves nothing and contacts nothing, and the fixture repositories `acme/widgets` and `acme` do not exist.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.3 This repository declares `issue:TanglmChris/keel`, and the two documents that enumerate the vocabulary plus the scenario pinning their wording move from five names to six
  - Covers:
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary / A declared action is authorized for the whole repository
    - D5
    - I1
    - I2
    - I3
    - I4
  - Read:
    - README.md
    - keel/config.yaml
    - scripts/validate_plugin.py
  - Touch:
    - keel/config.yaml
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node bin/keel.js --doctor` against this repository reports the per-action `issue` line as authorized and scoped to `TanglmChris/keel`, and `commit`, `push`, `release`, and `archive` unchanged from what they report today. Fails with: `issue: not authorized`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario continuation-docs` passes — its README and `keel/config.yaml` assertions name the six-name vocabulary, and every `continuation` clause it pins is unchanged, so updating the enumeration did not quietly drop what that scenario was actually guarding.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if declaring the entry here changes the result of any scenario other than `continuation-docs`, because a repository-level declaration that moves an unrelated assertion means a scenario was reading this repository's policy where it should have read a fixture.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a2f7423cfa3000ea15a684f0e3f4f878a0d34d4b78c60c84dd8b022c285c3a49
    - M1: pass. `node bin/keel.js --doctor` in this repository reports `authorize: ok - declared in keel/config.yaml: commit, push, release, archive, issue:TanglmChris/keel`, then `issue: authorized - scoped to TanglmChris/keel`, with `commit`, `push`, `release`, and `archive` still `authorized` and `continuation` still `not authorized` — the four that were declared before this task read exactly as they did, so the new entry joined the declaration rather than reshaping it.
    - M1.red: fail, for the declared reason, taken against this repository's own configuration before the entry existed: `authorize: ok - declared in keel/config.yaml: commit, push, release, archive` and `issue: not authorized`. Carries the declared signature `issue: not authorized`.
    - M1.green: pass. Same command after `keel/config.yaml` declared `issue:TanglmChris/keel`.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario continuation-docs` reports `continuation-docs scenario passed.` Its three pinned strings moved with the vocabulary — `accepted names: commit, push, release, archive, continuation, issue:<owner>/<repo>` in `README.md`, `The six names above are the whole vocabulary.` there too, and `commit, push, release, archive,\n# continuation, issue:<owner>/<repo>` in `keel/config.yaml` — while every `continuation` clause the same scenario pins is untouched, which is the half that would have made updating the enumeration a silent removal of what it guarded. The Stop Rule was checked rather than assumed: `npm test` reports `validation --all passed: baseline plus 174 scenarios, 1 skipped`, so declaring a repository-level policy moved no scenario other than this one.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that this repository declares the form it ships and that the documents a new project copies from move with the vocabulary. M1 reads the declaration back through `--doctor` rather than through the file that was just edited, so what is asserted is the resolved policy and not the text. M2 is a regression by construction — `continuation-docs` was green before and must stay green — and its value is precisely that it fails when an enumeration is updated carelessly: the three strings it pins are the ones `## Invalidates` named as I1, I2, and I3, so the entry that predicted the breakage and the check that would have caught it are the same three strings. The README paragraph added for the sixth name states the non-enforcement as plainly as the doctor line does, because a reader who learns the form from the README and never runs `--doctor` would otherwise never be told.
      - Scope check: `git status --short` shows `keel/config.yaml`, `README.md`, and `scripts/validate_plugin.py` — exactly this task's Touch — plus `src/core/config.js` and `bin/keel.js` from tasks 1.1 and 1.2, both complete and untouched here, plus this change's own untracked directory. The full suite was run to confirm the Stop Rule rather than to satisfy a check: nothing outside `continuation-docs` moved.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — a tracker grant names the repository it reaches, and the bare form is refused
    - E2 — the doctor reports the scope and does not contradict itself
    - E3 — Keel carries the scope and never enforces it
    - I5
  - Read:
    - keel/CHANGELOG.md
    - openspec/specs/keel-standing-authorization/spec.md
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - scripts/validate_plugin.py
    - openspec/specs/keel-standing-authorization/spec.md
    - .claude/commands/opsx/apply.md
    - .claude/commands/opsx/archive.md
    - .claude/commands/opsx/propose.md
    - .claude/commands/opsx/sync.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
  - Verify:
    - Strategy: evidence-first
    - Reason: this task's whole effect is version markers, a changelog entry, and promoted spec text. The behavior was proven red-green in 1.1, 1.2, and 1.3, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry stating why this one entry is scoped when the other five are not — that `gh` credentials are account-wide while the checkout bounds the rest — and stating plainly that Keel carries the scope and does not enforce it
    - M3: the delta is promoted into `openspec/specs/keel-standing-authorization/spec.md`, `node node_modules/.bin/openspec validate an-authorization-names-its-repository --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f1a3f80d11353e1511b8822e8c2e07609ab221a389fe39cd5d49e9edb9f95c51
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.61.0 to 5.62.0 through `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the three `keel:start` markers, the twelve `keel:openspec-surface-overlay` markers, and the two version constants in `scripts/validate_plugin.py`. The Stop Rule held: no marker turned up that the scenario does not check.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.62.0 - an authorization names its repository`. It states why this one entry is scoped when the other five are not — every other name acts on the checkout the declaration sits in, so the declaration and the thing it permits are the same size, while `gh` is account-wide and a bare `issue` would silently be the widest entry in the file, wider than `push` — and it states plainly, in its own bullet, that Keel carries the scope and does not enforce it, naming each surface that says so. It also records what was deliberately left out: closing, commenting, labelling, and anything cross-repository, with the reason closing needs no name at all.
    - M3: pass. The delta is promoted — `openspec/specs/keel-standing-authorization/spec.md` carries the modified closed-vocabulary requirement with its three new scenarios and the six-name enumeration, plus the added `A scope is a declaration Keel carries and never enforces` requirement. `node node_modules/.bin/openspec validate an-authorization-names-its-repository --strict` reports `Change 'an-authorization-names-its-repository' is valid`, and `published-specs-validate-strictly` reports `23 published specs validate strictly against openspec 1.6.0.`
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 174 scenarios, 1 skipped: output-survives-the-pipe.` The release moved nothing. The single skip is the platform refusing `F_SETPIPE_SZ`, unrelated and pre-existing, verified as such in the previous change.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every marker through the scenario that checks them all rather than through the bump script's own report of what it wrote. M3 asserts the promotion through both tools that consume the published store, strict in both, and the promotion here was a replacement rather than an append — the modified requirement's enumeration is I5, so leaving the old text beside the new one would have published two contradictory closed sets. M2's job is that a reader of this release learns the boundary and its limit in the same entry: what the scope buys, and that nothing enforces it.
      - Scope check: `git status --short` shows 26 modified paths and one untracked directory. Every modified path is in this task's Touch or was declared complete by 1.1, 1.2, or 1.3 — `src/core/config.js`, `bin/keel.js`, `README.md`, `keel/config.yaml` — and untouched here; the untracked entry is this change's own directory. `keel gate task-complete` compared the worktree against the dirty set recorded at task-start.
      - Findings: one, and it belongs to this change rather than to a task. Issue #136 is fixed here and will close when this lands, through the `Closes #136` in the pull request body — the same route the changelog names for #133, #134, and #137, and the reason closing needed no vocabulary entry. Nothing is owed beyond the merge. Durable owner: https://github.com/TanglmChris/keel/issues/136
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "accepted names: commit, push, release, archive, continuation" — the `authorize:` example
  comment in `README.md`. The list is the wrong length after this change, and it is the copy a
  reader is most likely to paste from.
  Updated by: 1.3, 2.1
- I2: "**Not open-ended.** The five names above are the whole vocabulary." — `README.md`'s three
  things the declaration is not. "Five" is a count, so it goes wrong silently; nothing else in the
  sentence does.
  Updated by: 1.3, 2.1
- I3: "accepted names are the whole vocabulary — commit, push, release, archive, continuation —
  and an unrecognized entry is reported with the accepted names" — the `authorize` comment block
  in `keel/config.yaml`, which is also where a new project reads the form from.
  Updated by: 1.3, 2.1
- I4: `"accepted names: commit, push, release, archive, continuation"`, `"The five names above are
  the whole vocabulary."`, and `"commit, push, release, archive,\n# continuation"` — the three
  string assertions inside the `continuation-docs` scenario in `scripts/validate_plugin.py`. They
  are what makes I1 to I3 fail loudly rather than drift, which is why they are listed here rather
  than discovered when the suite goes red.
  Updated by: 1.3
- I5: "The accepted action names MUST be a closed set — `commit`, `push`, `release`, `archive`,
  `continuation`" — `openspec/specs/keel-standing-authorization/spec.md`, and the scenario beneath
  it that enumerates which names remain unauthorized.
  Updated by: 2.1
- I6: "A task that authors no `Autonomy boundary:` inherits what is declared here" and the rest of
  `keel/config.yaml`'s statement of what the declaration does not do. It stays true: this change
  adds a name to the vocabulary and changes nothing about inheritance, gates, evidence, or the
  guard.
  Discard reason: the wording is correct after this change.

## Expectation Coverage

- E1: A tracker authorization names the repository it reaches, and the bare form is refused with the form it requires rather than accepted as a convenience (D1, D3, F1, F3). Covered by: 1.1
- E2: `keel --doctor` reports the scope beside the action, and does not report an action as unauthorized on the same screen where it lists the entry declaring it (F2, D4). Covered by: 1.2
- E3: Keel carries the scope to the surfaces a reader sees and never claims to enforce it (D2). Covered by: 1.2
- E4: The enumerations a new project copies from — `README.md`, `keel/config.yaml` — and the scenario that pins them move together with the vocabulary (I1, I2, I3, I4). Covered by: 1.3
- E5: This repository declares the form it ships, which is what makes the gap that motivated the change closed here rather than only described (D5). Covered by: 1.3
- E6: Whether a project needs to authorize filing into a repository other than its own — a fork reporting upstream, or a monorepo whose issues live elsewhere (A1). Discard reason: deliberately not done rather than deferred. No such project is known here, the parser accepts a second `issue:` entry without any semantics being defined for one, and building multi-entry semantics now would design for a case nobody has. The direction if it appears is to widen the declaration, which is what the precedent `declarative-authorization-over-blanket-bypass` records as the correct response to a declaration that turns out too narrow.
