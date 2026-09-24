# Tasks

## 1. The rule and its exceptions arrive where the decision is made

- [x] 1.1 `keel/config.yaml` declares `full_mode_paths:`, one `- <path>: <reason>` entry per path; a third reader holds the form neither existing reader can, an entry with no reason is refused by name, and `keel context` reports what is declared and stays silent when nothing is
  - Covers:
    - keel-full-lite-routing / A project declares the paths the size heuristic gets wrong / A declared path carries the reason it must route Full
    - keel-full-lite-routing / A project declares the paths the size heuristic gets wrong / An entry with no reason is refused by name
    - keel-full-lite-routing / The declared exceptions are reported where the decision is made / A declaring repository sees its exceptions at session start
    - keel-full-lite-routing / The declared exceptions are reported where the decision is made / A repository declaring nothing sees nothing
    - keel-full-lite-routing / An unreadable routing declaration routes everything Full / An absent declaration changes nothing
    - F3
    - D2
    - D4
    - D5
    - D6
  - Read:
    - src/core/config.js
    - src/core/context.js
    - openspec/changes/the-routing-rule-reaches-the-decision/design.md
  - Touch:
    - src/core/config.js
    - src/core/context.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `the-routing-rule-reaches-the-decision` scenario runs `keel context` against a fixture declaring `full_mode_paths:` with `results/experiments.jsonl: append-only; a one-field diff is not revertible`. The projection reports the path **and its reason**, and its `status` and next action are asserted identical to the same fixture without the declaration — so the line is added and nothing else moved. The declared path names no existing file in the fixture, which is D5 asserted rather than assumed. Fails with: `no routing line`
    - M2: a fixture whose entry is a bare path with no reason is reported unreadable, naming the entry and the `- <path>: <reason>` form; the entry is asserted not to appear as a declared path anywhere in the output, so it did not silently degrade into a bare declaration. Fails with: `was read as a declaration`
    - M3 (regression): a fixture with no `keel/config.yaml`, one with no `full_mode_paths:` block, and one with an empty block each produce a projection with no routing line at all, byte-identical to the same fixture before this task — so the common case pays nothing, which is the whole reason D6 keeps the line conditional.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if holding the entry requires widening `configList`'s or `configMap`'s pattern, because F3 records that both are exact for declarations this must not disturb and D4 confines the new form to its own reader.
    - Stop if reporting a declared path requires checking that a file exists at it, because D5 records that the path which does not exist yet is the case the declaration most needs.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:858c4a3bf2fe49d2b3a42e404829e4d92d6c55194e923e04928222b837409bcb
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-routing-rule-reaches-the-decision` reports `the-routing-rule-reaches-the-decision scenario passed.` Against a fixture declaring `full_mode_paths:` with `results/experiments.jsonl: append-only; a one-field diff is not revertible`, `keel context` prints `Routing: results/experiments.jsonl always routes Full — append-only; a one-field diff is not revertible`. The reason is asserted separately from the path, so a line naming the file without saying what makes it special does not pass. The projection's `Keel context:` and `Next action:` lines are compared against the same fixture without the declaration and asserted identical — the line is added and nothing else moved. D5 is asserted rather than assumed: the scenario checks that no file exists at the declared path, so what was resolved was the declaration and not the filesystem.
    - M1.red: fail, for the declared reason. `keel context` against the declaring fixture printed the four lines it prints for any idle repository and nothing else: `the-routing-rule-reaches-the-decision: no routing line — a repository that declared 'results/experiments.jsonl' is told nothing about it at the one moment the routing decision is made.` Carries the declared signature `no routing line`.
    - M1.green: pass. Same command after `readFullModePaths` and the conditional `Routing:` line were written.
    - M2: pass. A fixture whose entry is a bare `- results/experiments.jsonl` with no reason produces no routing line naming that path, and a warning naming the entry and the `- <path>: <reason>` form, with the sentence stating why the reason is required rather than only that it is. At the time this ran the fixture produced no routing line at all; task 1.2 then added the conservative line for exactly this input, because a reason-less entry *is* an unreadable one and an unreadable declaration routes everything Full. The assertion is, and always was, that the entry is not reported as a declared path — the scenario code was tightened to match that wording once 1.2 made the difference observable.
    - M2.red: fail, for the declared reason, taken from the obvious implementation rather than from the starting state: the reader written so the reason is optional and a bare path still declares. `the-routing-rule-reaches-the-decision: the reason-less entry was read as a declaration; ['Routing: results/experiments.jsonl always routes Full — ']` — the degraded line is in the evidence, and it is exactly what D2 exists to refuse: a declaration that parses, routes, and teaches nothing. Carries the declared signature `was read as a declaration`. The scenario's assertions were reordered to put this one first before the red was taken; it is the substantive claim, and whether the entry is also reported well comes after whether it counts.
    - M2.green: pass. Same command after an unreadable entry was routed to `unreadable` instead of to `paths`.
    - M3: pass. Inside the same run: a fixture with no `keel/config.yaml`, one with a config but no `full_mode_paths:` block, and one with an empty block each produce a projection containing neither `Routing:` nor `full_mode_paths`. The repositories that declare nothing pay nothing, which is what D6 keeps the line conditional for. Correctly tagged regression: all three printed nothing before this task for the simpler reason that the line did not exist.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a declared path reaches the projection with its reason, and that an entry without a reason is not read as one. Both are proven through `keel context` — the surface the protocol already requires an agent to open before deciding anything — against fixture repositories, never by calling the reader. The pair is staged so neither check carries the other: M1's red is the state with no reader at all, and M2's is the state where the reader exists and is permissive, which is the implementation a careful author would actually have written. Two design decisions are asserted rather than trusted: the declared path names no existing file (D5), and the three non-declaring fixtures produce no line (D6). What no check here covers is A1 — whether an agent holding the line routes by it — and the design says plainly that this is where the change's reach ends.
      - Scope check: `git status --short` shows `src/core/config.js`, `src/core/context.js`, and `scripts/validate_plugin.py` — exactly this task's Touch — plus this change's own untracked directory. `npm test` reports `validation --all passed: baseline plus 175 scenarios, 1 skipped`, so adding a field to the context result and a line to its renderer moved no other scenario. Both Stop Rules held: `configList` and `configMap` are byte-unchanged, and the new reader touches only its own key; nothing consults the filesystem for a declared path.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 An unreadable `full_mode_paths:` reports that every change routes Full until it is corrected, naming the entry that could not be read — the opposite of `authorize:`'s fail-closed and the same principle, because for a declaration that adds process, failing toward more scrutiny means more Full mode
  - Covers:
    - keel-full-lite-routing / An unreadable routing declaration routes everything Full / A malformed entry raises the floor rather than dropping it
    - D1
    - D3
  - Read:
    - src/core/config.js
    - src/core/context.js
    - bin/keel.js
  - Touch:
    - src/core/config.js
    - src/core/context.js
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: against a fixture whose `full_mode_paths:` carries one readable entry and one unreadable one, `keel context` reports that every change routes Full until the declaration is corrected, and names the unreadable entry. The readable entry is asserted **not** to be reported as the declared set, because a declaration Keel half-read is not a policy to act on. Fails with: `routes only the entries it could read`
    - M2: `keel --doctor` against the same fixture reports the declaration as failed and names the same entry, so the diagnostic and the projection agree rather than one of them reporting health the other contradicts.
    - M3 (regression): against the readable fixture from 1.1, neither surface reports the everything-routes-Full state, so the conservative branch is reached by an unreadable declaration and not by any declaration at all.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the conservative behavior has to be expressed as a gate result or a refusal, because the Non-Goals record that routing precedes the change and there is nothing for a gate to bind to.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:66c613350c94f6eef7c5409e3da681e7161e0a8283c777228012bc444ca11ac0
    - M1: pass. Against a fixture whose `full_mode_paths:` carries one readable entry and one bare `- src/lib.js`, `keel context` prints `Routing: every change routes Full until keel/config.yaml's full_mode_paths is corrected`. The readable entry is asserted **absent** from the routing lines — a declaration Keel half-read is not a policy to act on — and `src/lib.js` is asserted present in the output, so the state is attributable to an entry rather than mysterious.
    - M1.red: fail, for the declared reason. The half-read declaration acted as the whole policy: `the-routing-rule-reaches-the-decision: routes only the entries it could read — a declaration Keel half-read was treated as the policy, so a typo silently lowers the process floor. ['Routing: results/experiments.jsonl always routes Full — append-only; a one-field diff is not revertible']` The red evidence holds the dangerous output verbatim: one path declared, one path silently dropped, and nothing saying so. Carries the declared signature `routes only the entries it could read`.
    - M1.green: pass. Same command after the unreadable branch cleared the resolved set and set the conservative state instead of reporting a partial one.
    - M2: pass. `keel --doctor` against the same fixture prints `full_mode_paths: failed` with the same entry named and `Every change routes Full until it is corrected.`, so the diagnostic and the projection reach the same verdict from the same read rather than leaving a reader to pick which to believe. On a readable declaration the same surface reports `full_mode_paths: ok - declared in keel/config.yaml: 2 paths always route Full` with one line per path carrying its reason.
    - M2.red: fail, for the right reason, taken from the intermediate state with M1 already green — the projection reporting the conservative state and the doctor having no routing surface at all. `the-routing-rule-reaches-the-decision: the doctor does not report the declaration as failed and name the entry, so it reports health the projection contradicts.`
    - M2.green: pass. Same command after `printRoutingSurface` was added to the doctor sequence. One defect was found by reading that surface against a live fixture rather than through the scenario: with a single declared path it read `1 path always route Full`. The verb is now pluralized with the noun, confirmed against both a one-path and a two-path fixture.
    - M3: pass. `keel context` against the readable fixture from 1.1 contains no `every change` statement, so the conservative branch is reached by an unreadable declaration and not by any declaration at all. Correctly tagged regression: that fixture produced no such statement before this task for the simpler reason that the branch did not exist.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a declaration Keel cannot fully read raises the floor instead of dropping it, and says which entry caused it. M1 proves all three parts through `keel context` — the conservative statement present, the readable entry absent from the resolved set, the unreadable entry named — and the middle one is the load-bearing assertion, because an implementation that added the warning while still publishing the half-read set would satisfy the other two. Its red holds that exact output. M2 covers the second surface, and its point is agreement: a `--doctor` reporting health while the projection reports the conservative state would be two answers to one question. This task also surfaced a real interaction rather than papering over it — a reason-less entry is an unreadable entry, so 1.1's fixture now reaches this branch; 1.1's scenario assertion was tightened to what its check text always said (no routing line *naming the entry*) and its Evidence records the interaction rather than leaving a sentence that stopped being true.
      - Scope check: `git status --short` shows `src/core/config.js`, `src/core/context.js`, `bin/keel.js`, and `scripts/validate_plugin.py` — exactly this task's Touch — plus this change's own untracked directory. `src/core/config.js` and `src/core/context.js` were already dirty from 1.1; what this task added is the conservative branch and its renderer. `npm test` reports `validation --all passed: baseline plus 175 scenarios, 1 skipped`. The Stop Rule held: the conservative behavior is a reported state, not a gate result or a refusal — no gate was given a routing verdict, because there is no change for one to bind to.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.3 The installed bootstrap carries the routing rule in one line inside its existing budget, the resident-block topic list pins it, and the three documents that describe the declaration set or what the bootstrap states move with it
  - Covers:
    - keel-full-lite-routing / The routing rule reaches the agent that makes the decision / A consuming repository receives the routing rule
    - keel-full-lite-routing / The routing rule reaches the agent that makes the decision / Routing is carried and not gated
    - F1
    - F4
    - F5
    - D7
    - I1
    - I2
    - I3
    - I5
    - I6
  - Read:
    - assets/bootstrap/AGENTS.md
    - README.md
    - keel/config.yaml
    - scripts/validate_plugin.py
  - Touch:
    - assets/bootstrap/AGENTS.md
    - README.md
    - keel/config.yaml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the same scenario asserts the installed block through the artifact `keel --init` writes: `assets/bootstrap/AGENTS.md` states both modes, the size heuristic, and that a project may declare exceptions, and the managed block is within **both** its budgets — the 12-line one via the baseline `validate_resident_blocks` rather than by counting in the scenario, and the byte one at its raised value. Fails with: `bootstrap states no routing rule`
    - M2: the raise is loud, which is the whole condition D7 rests on. Both assertions of the byte cap — in `thin-native-install` and in `delegation-resident-text` — name the new number and carry the reason it moved, and the scenario asserts that a reader of either one finds the reason there rather than only a larger constant. Fails with: `names the new cap without the reason it moved`
    - M3 (regression): `continuation-docs`, `thin-native-install`, `delegation-resident-text`, and the baseline all pass, and `keel/config.yaml`'s header now counts six declarations rather than five, so the enumerations a new project reads from moved with the declaration set and the two cap-asserting scenarios still hold the cap rather than having been switched off.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the raise is made without its reason landing at both assertions, because D7's authority is that the spending is loud — a larger constant with no argument beside it is the quiet drift the cap was built to prevent, and it would pass every check here.
    - Stop if fitting the line requires compressing an existing bullet, because D7 records that trade as the rejected alternative: it goes green while paying for routing out of content that was already earning its place.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:95c85f5bd423bbebf9079112eb352abaf26d784133fe4ec4e7e08d3a52f4986a
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-routing-rule-reaches-the-decision` reports `the-routing-rule-reaches-the-decision scenario passed.` The assertion reads `assets/bootstrap/AGENTS.md` — the artifact a consuming repository actually receives — for `Full`, `Lite`, `100 lines`, and `full_mode_paths`, and checks both budgets: the line budget by running the baseline `validate_resident_blocks` rather than counting in the scenario, and the byte budget against `BOOTSTRAP_BLOCK_BYTE_BUDGET`. Measured after the line: **1325 bytes of 1400, 75 bytes of headroom, 10 lines of 12.**
    - M1.red: fail, for the declared reason, retaken under this contract after the first one was reauthorized: `the-routing-rule-reaches-the-decision: bootstrap states no routing rule — the block must name the complete flow; 'Full' is absent. Routing is the first decision of a session and the block a consuming repository receives is where it has to arrive.` Carries the declared signature `bootstrap states no routing rule`.
    - M1.green: pass. Same command after the routing line was written and the cap raised.
    - M2: pass. The rationale for the raise lives in the comment block above `BOOTSTRAP_BLOCK_BYTE_BUDGET` and the check reads it from there, walking back over the contiguous comment lines rather than guessing a window. Both assertions of the cap — `thin-native-install` and `delegation-resident-text` — now read the constant instead of a literal `1024`, so there is one number and one place to learn why it is that number. The rationale states what the cap defends (`not quietly`), why routing earned the bytes and delegation did not, and why 1400 rather than a round 1536.
    - M2.red: fail, for the declared reason, from the state D7 exists to forbid — the number raised to 1400 and the argument deleted, leaving `# The installed bootstrap block's byte budget.` `the-routing-rule-reaches-the-decision: names the new cap without the reason it moved; 'routing' is absent from the constant's own rationale. A reader inheriting a larger number and no argument is the drift the cap exists to prevent.` That is a real red for the condition the owner's authorization rests on, not for a missing feature. An earlier firing of the same message was my check looking after the constant while the rationale sat above it; the aim was corrected before this red was taken, so the red is the absence of the reason and not a misaimed assertion.
    - M2.green: pass. Same command with the rationale restored.
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 175 scenarios, 1 skipped: output-survives-the-pipe.` `continuation-docs`, `thin-native-install`, and `delegation-resident-text` all pass, the last two still holding the cap through the constant rather than having been switched off, and `keel/config.yaml`'s header now counts six declarations. Recorded fresh under this contract rather than carried: the re-record declared it stale, and it was re-run.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the rule reaches the block a consuming repository receives, inside its budgets. M1 asserts it on the shipped artifact rather than a fixture, and runs the suite's own line-budget check rather than reimplementing it, so what is enforced is the budget the project enforces. M2 is the check that makes the authorization honest rather than convenient: the owner permitted raising the cap **because the raise is loud**, so the condition worth testing is that the argument is present, and its red is the bare larger constant — the exact artifact of a quiet raise. Two things are deliberately not claimed. The block now carries routing and says `No gate checks routing`, which is the honest statement of a rule nothing enforces; and A1 still stands — no check here observes an agent actually routing by what it read.
      - Scope check: `git status --short` shows `assets/bootstrap/AGENTS.md`, `README.md`, `keel/config.yaml`, and `scripts/validate_plugin.py` — exactly this task's Touch — plus `bin/keel.js`, `src/core/config.js`, and `src/core/context.js` from 1.1 and 1.2, both complete and untouched here, plus this change's own untracked directory. Both Stop Rules held: the reason landed at the constant both assertions now read, and no existing bullet was compressed — the block grew from 1014 to 1325 bytes and every original bullet is byte-identical.
      - Findings: one, still open and not fixed here. `delegation-resident-text` pins `keel/config.yaml`'s declaration count as a written-out English numeral, asserted from both sides, and has now been hand-bumped twice — `Four` to `Five` when delegation arrived, `Five` to `Six` here. The count is derivable from the declarations `src/core/config.js` actually reads, and deriving it would let the failure name the declaration missing from the header instead of a number. This task does not fix it: that is a different module and would be scope expansion on a task whose acceptance is the routing rule. It cost this change one red suite run and the `## Invalidates` entry I6 that the first pass missed — because I2 named the file the wording lives in and not the check that holds it, which is the same miss that produced this task's hard stop. Filed under the `issue:TanglmChris/keel` standing authorization declared in 5.62.0, which is the first use of that entry. Durable owner: https://github.com/TanglmChris/keel/issues/143
    - Blocker: none
    - Reauthorizations: this task hard-stopped once and was reauthorized. Its first contract's Stop Rule read "Stop if the routing line does not fit the existing budget … the line would then need to be shorter rather than the block larger", and the implementation hit a byte cap F1 had not found: the block is 1014 bytes against 1024, so no line of any length fits and shortening was not a fix (F4). The checkout was reverted to green and the decision returned to the owner rather than resolved inside the task. The owner authorized raising the cap with its reason recorded, 2026-09-25; design gained F4, F5, and D7, the Stop Rules were replaced by the two D7 actually needs, and the contract was re-recorded. The stale M1 red from the first contract was discarded and retaken. It was then re-recorded a second time, with `--keep-evidence M1,M2`, when `I6` was added to Covers: the suite turned red on an assertion inside `delegation-resident-text` pinning the config header's declaration count, which `## Invalidates` had not named. M1's and M2's check texts did not move — only the Covers list gained an identifier — which is the claim `--keep-evidence` records and Keel does not verify. M3 was declared stale by that re-record and re-run rather than carried.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — the routing rule is in the installed block
    - E2 — a project declares the paths the heuristic gets wrong, each with its reason
    - E3 — an unreadable declaration raises the floor rather than dropping it
    - I4
  - Read:
    - keel/CHANGELOG.md
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
    - openspec/specs/keel-full-lite-routing/spec.md
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
    - Reason: this task's whole effect is version markers, a changelog entry, and a promoted spec. The behavior was proven red-green in 1.1, 1.2, and 1.3, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry giving the measured gap — a 5-bullet installed block with no routing content, and routing with no implementation at all — stating that there is deliberately no opposite-direction key and why, and stating that Keel carries the rule and does not gate it
    - M3: the new capability is published at `openspec/specs/keel-full-lite-routing/spec.md`, `node node_modules/.bin/openspec validate the-routing-rule-reaches-the-decision --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9f8b88f9313e4e1734b59b9b68e47678990f3c7eee1ed7c832555057d5f23ac4
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.62.0 to 5.63.0 through `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the three `keel:start` markers, the twelve overlay markers, and the two version constants. The Stop Rule held: no marker turned up that the scenario does not check.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.63.0 - the routing rule reaches the decision`. It gives the measured gap — a 9-line, 5-bullet installed block with no routing content, and two unrelated grep hits standing for the whole of routing's implementation — states that there is deliberately no opposite-direction key with the reason the symmetric case is not the test, and states that Keel gates no routing decision and why. It also records the budget raise as its own bullet with the numbers (1014 bytes, 10 bytes of headroom, 1024 to 1400), the rejected alternative and why it would have gone green on the worse outcome, and why routing earned the bytes where delegation did not.
    - M3: pass. `openspec/specs/keel-full-lite-routing/spec.md` is published with its four requirements. `node node_modules/.bin/openspec validate the-routing-rule-reaches-the-decision --strict` reports `Change 'the-routing-rule-reaches-the-decision' is valid`, and `published-specs-validate-strictly` reports `24 published specs validate strictly against openspec 1.6.0.` — one more than before, this change adding the capability rather than modifying one.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 175 scenarios, 1 skipped: output-survives-the-pipe.` The one skip is the platform refusing `F_SETPIPE_SZ`, unrelated and pre-existing.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every marker through the scenario that checks them all rather than through the bump script's own report. M3 asserts the publication through both tools that consume the store, strict in both, and the count moving 23 to 24 is the check that a new capability was published rather than an existing file edited. M2 carries the part a later reader most needs: not what the change added, but what it cost and what was refused — the budget number moved, and the entry says so in its own bullet rather than leaving it to be discovered in a diff.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, and the paths 1.1 to 1.3 declared complete, plus two untracked directories: this change's own, and `openspec/specs/keel-full-lite-routing/` — the published capability, which is this task's `openspec/specs/keel-full-lite-routing/spec.md` Touch entry appearing as untracked because the capability is new rather than modified. `keel gate task-complete` compared the worktree against the dirty set recorded at task-start.
      - Findings: two, both still open, neither fixed here, and both found by hitting them during this change. The first is the hand-bumped declaration count in `delegation-resident-text`, recorded on task 1.3 and not repeated. The second is a false stop in this gate: a Review `Findings` entry reading `Not resolved here: it …` was refused with `records a finding as resolved here, but its evidence is not usable — it read \`it\``, because the marker scan matches `resolved here:` inside the negation and takes the next word as evidence. The entry had a valid `Durable owner:` and said in as many words that the finding was unresolved, so the gate read a dismissal as a repair and then refused it for lacking repair evidence — the exact inversion `## Follow-up Ownership` warns about, running the other way. The workaround is to know the phrase is booby-trapped and write "This task does not fix it:" instead, which is knowledge that lives nowhere. Durable owner: https://github.com/TanglmChris/keel/issues/144
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "Use **Full mode** (the OpenSpec flow above) for new features, interface or protocol
  changes, cross-module work, or anything over ~3 files / 100 lines." — `README.md`'s
  `### Full vs Lite`. The rule stays correct and stops being the whole statement: it is the only
  place the rule lives today, and after this change a project can correct the size heuristic, which
  this section does not mention.
  Updated by: 1.3, 2.1
- I2: "Five independent declarations live here: fast_check, which names a command; authorize,
  ...; precedents, ...; triage, ...; and delegation, which names who runs a task." — the header
  comment of `keel/config.yaml`. "Five" is a count, so it goes wrong silently, and this file is
  where a new project reads the declaration set from.
  Updated by: 1.3, 2.1
- I3: "It states the rules the agent follows: open every session with `keel context`, pass the
  gates at task boundaries, and stay inside the task's declared write scope." — `README.md`'s
  description of what the installed bootstrap contains. It enumerates, so adding a rule to the
  block makes it an incomplete list rather than a wrong sentence — the shape that is never noticed
  by a reader who is not counting.
  Updated by: 1.3, 2.1
- I5: "thin-native-install bootstrap block is not sub-1KB" and "the bootstrap block is {size}
  bytes, over its 1KB budget." — the two byte-cap assertions in `scripts/validate_plugin.py`, plus
  the comment above the second one stating the block "has a sub-1KB budget with 11 bytes of
  headroom". All three are wrong once the cap moves, and the headroom figure was already wrong
  before this change (measured 10, not 11), which is the shape of a number nobody re-measures.
  Updated by: 1.3, 2.1
- I6: "the config header still says four declarations" / "Five independent declarations" — the
  count assertion inside `delegation-resident-text` in `scripts/validate_plugin.py`. It pins the
  header wording I2 changes, from both sides, and was not found when I2 was written: the entry
  named the file the wording lives in and not the check that holds it, which is the same miss that
  produced this change's one hard stop.
  Updated by: 1.3
- I4: "Keel context: idle / Next action: none" and the rest of the `keel context` output shape —
  `openspec/specs/keel-stateless-continuity/spec.md`. It stays true: this change adds one
  conditional line and changes no status, next action, selection, or reason.
  Discard reason: the wording is correct after this change; the projection gains a line and loses
  nothing, and 1.1's M1 asserts the status and next action are unchanged by the declaration.

## Expectation Coverage

- E1: The routing rule is in the block `keel --init` installs, in one line inside the existing budget, and nothing claims routing is gated (F1). Covered by: 1.3
- E2: A project declares the paths the size heuristic gets wrong, each entry carrying the reason, read by a reader confined to this key, with the path's shape checked and its existence not (F3, D2, D4, D5). Covered by: 1.1
- E3: An unreadable declaration routes everything Full and names the entry, so a typo raises the floor rather than dropping it (D1, D3). Covered by: 1.2
- E4: The exceptions arrive at the session's first decision, and the repositories that declare nothing pay nothing for it (D6). Covered by: 1.1
- E5: The enumerations a new project reads from — the declaration set, and what the bootstrap states — move with the change (I1, I2, I3). Covered by: 1.3
- E6: Whether an agent holding the declaration actually routes by it (A1). Discard reason: deliberately not done rather than deferred. Routing precedes the change, so there is nothing for a gate to bind to and no artifact whose existence would prove the decision was made correctly; a check invented for it would be asserting on the absence of a change, which is also what a session that did no work looks like. What this change can do is put the rule and the exceptions in front of the decision, and A1 states plainly that this is where its reach ends.
