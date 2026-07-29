## 1. The channel is confirmed before the contract hardens

- [x] 1.1 Emit the human line on the ready and idle branches, then confirm the host renders it
  - Covers:
    - keel-native-runtime-projection / SessionStart projection reaches the human directly / Ready projection is visible without a user message
    - D1: the human line ships as top-level `systemMessage` on the existing single JSON emit
    - D3: rendering is confirmed by smoke check before the specs and validator scenarios harden (resolves Q1)
    - F1: the 2.1.220 common hook-output schema declares `systemMessage` as an optional string
    - F2: `systemMessage` and `additionalContext` share one generic hook-output handler
  - Touch:
    - plugins/keel/scripts/session-start.js
  - Verify:
    - Strategy: evidence-first
    - M1: the hook's stdout parses as one JSON object carrying a top-level `systemMessage` that names the selection and next command, while `hookSpecificOutput.additionalContext` stays byte-identical to its pre-change value for the same fixture repository
    - M2: a fresh Claude Code session opened in a Keel repository displays that message to the human before any user message is sent, and the agent's model-facing projection still arrives intact
  - Execution recommendation: M2 is observed by the user, not by this agent — a SessionStart hook fires only on a real session start. Ask the user to open a fresh session, then record what they report as M2 Evidence, including the rendered styling, which D2 wording depends on.
  - Autonomy boundary: none; if M2 shows the host does not render the message, hard-stop and return to design before task 2.1, because the change's premise is void and the reversal is a single-file revert.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3cec01fbcb6ca8210d35c9be1dd4666ffca5a6d10240c482fedbd1c2baccaa73
    - M1: the pre-change script (`git show HEAD:plugins/keel/scripts/session-start.js`) and the working-tree script were run against identical fixture repositories on the ready and idle branches. Both exit 0. `additionalContext` is byte-identical across the pair on both branches (374 and 330 chars); the pre-change script emits no `systemMessage`, and the working-tree script emits `Keel: demo#1.1 — next: task-complete. Disposable projection; OpenSpec and Git are the authority.` and `Keel: idle — No active OpenSpec change was found. Next: keel context. Disposable projection; OpenSpec and Git are the authority.` `npm test` reports baseline plus 90 scenarios, unchanged from before the edit.
    - M2: confirmed by the user on 2026-07-28 in Claude Code 2.1.220, in a different Keel repository (`chip_sec_flow_v2`) on a real change and task, with no user message sent. Rendered at session start as `SessionStart:startup says: Keel: deliverable-artifact-routes#2.1 — next: task-start. Disposable projection; OpenSpec and Git are the authority.` Two observations the design did not predict: the host prefixes the message with `<hookEvent>:<source> says: `, so a message must read as a fragment after `says: ` rather than as a standalone sentence; and the rendering carries no warning affordance despite the host schema naming the field a warning message, so a routine idle projection does not read as an alarm. A1 is resolved in the same session: after one user message, the agent restated `context ready: deliverable-artifact-routes#2.1 (inferred); next action: task-start` and `read first: …`, which appear only in `additionalContext` and not in the rendered human line, so the host delivered both channels rather than substituting one for the other.
    - Review:
      - Status: pass
      - Acceptance check: M1 proves the emit carries a top-level `systemMessage` while `additionalContext` stays byte-identical to the pre-change script on both branches, so the human channel is additive rather than a substitution. M2 proves the host actually renders it to a person at session start with no user message, which is the observable behavior the change exists for and the only thing that could confirm F1/F2 were read correctly from a compiled binary. The two together resolve Q1 and A1 through the public interface — the hook's stdout and the host's rendering — not through the script's internal shape.
      - Scope check: `git status --porcelain` shows one modified product file, `plugins/keel/scripts/session-start.js`, which is the whole of Touch, plus this change's own untracked directory, which is the record-write layer. `npm test` reports baseline plus 90 scenarios, the same count as before the edit, so no existing scenario changed behavior.
      - Findings: none
    - Blocker: none

## 2. Every branch reaches the human

- [x] 2.1 Carry the human line on the non-ready and degraded branches, asserted per branch
  - Covers:
    - keel-native-runtime-projection / SessionStart projection reaches the human directly / Non-ready projection is visible to the human
    - keel-native-runtime-projection / SessionStart projection reaches the human directly / Degraded projection is visible rather than silent
    - keel-native-runtime-projection / SessionStart projection reaches the human directly / The human channel authorizes nothing
    - D4: the fallback branches carry the human line, because a silent fallback reproduces the reported bug
    - A1: an unrecognized `systemMessage` is ignored by the host rather than voiding the whole emit
  - Touch:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the `native-plugin-session-start` scenario asserts a human-visible message naming the status and next command on each of the idle, ambiguous, missing-CLI, malformed-output, and timeout branches, and fails on any branch that emits none
    - M2 (regression): the same scenario still asserts the unchanged `additionalContext` projection and its disclosure phrase on every branch, and still asserts the hook exits 0 and wrote no repository state
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8c72444733cf921d40e6f44d9fa67bdf29ad816cd431bd34cbd47c03805000c0
    - M1: `python scripts/validate_plugin.py --scenario native-plugin-session-start` exits 0 and reports `native-plugin-session-start scenario passed.` The scenario now checks all six branches — ready, idle, ambiguous, missing-CLI, malformed, timeout — for a human message carrying that branch's status token, its explicit next command, and the authority note, and additionally refuses an ambiguous message that names a candidate owner.
    - M1.red: with the assertions added and `fallback()` still emitting no human message, the scenario exits 1 with `native-plugin-session-start missing-CLI branch emitted no human-visible message, so that state reaches only the agent and nobody can catch it being wrong.` A second, independent red confirms the token assertions are not vacuous: mutating only the fallback's human line to drop the authority note makes the scenario exit 1 with `missing-CLI human message omits ['OpenSpec and Git']`, and restoring it returns exit 0.
    - M1.green: after `fallback()` gained its human line, the same command exits 0 at `baseline plus 90 scenarios`.
    - M2: the scenario's pre-existing per-branch assertions on `additionalContext` — the status token, the explicit next command, the disclosure phrase, the refusal to name a guessed owner, exit 0, and the no-repository-write snapshot comparison — are unmodified and still pass on every branch, so the human channel was added beside the model channel rather than in place of it.
    - Review:
      - Status: pass
      - Acceptance check: the checks run the real hook script as a subprocess against six fixture repositories and read its stdout, which is the hook's entire public interface; nothing asserts internal shape. The red proves the missing branch was actually uncovered before the fix, and the mutation proves the token assertions fail when the message degrades, so a passing green means the behavior is present rather than the assertion being weak.
      - Scope check: `git status --porcelain` shows exactly the two Touch files modified, `plugins/keel/scripts/session-start.js` and `scripts/validate_plugin.py`, plus this change's own untracked directory, which is the record-write layer. `npm test` reports baseline plus 90 scenarios, the same count as before, so no scenario was added or dropped — the existing one grew assertions.
      - Findings: none
    - Blocker: none

- [x] 2.2 Open the human message with the owl mark, without letting the mark carry meaning
  - Covers:
    - D5: the three-line owl mark drawn only from the `U+2580–U+259F` block-element family
    - D6: the mark is decorative and the status line stands on its own
  - Touch:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the `native-plugin-session-start` scenario asserts that every emitted human message begins with a newline followed by the three mark rows, that every character in those rows is either a space or in `U+2580–U+259F`, and that the three rows are equal in display width so the mark cannot misalign
    - M2: with the mark's newlines collapsed to spaces, the remaining message still names the status and the next command on the ready, idle, and fallback branches, proving the mark is not load-bearing
    - M3: a fresh Claude Code session renders the mark as three aligned rows rather than one collapsed line
  - Execution recommendation: M3 is observed by the user in a real session, as M2 of task 1.1 was. Record the reported render, including whether the rows align, and treat a collapsed render as the answer to Q2 rather than as a defect to work around.
  - Autonomy boundary: if M3 shows the host collapses newlines, drop the mark and keep the single-line message; that is a pre-authorized reversal of this task only, requires no design change because D6 already bounds it, and must be recorded as the resolution of Q2.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:b81c71f0004cd3261bd6933967cb639c89a8973925c1624108c152265e317b46
    - M1: `python scripts/validate_plugin.py --scenario native-plugin-session-start` exits 0. `mark_problem` runs on all six branches and checks four properties of each emitted message: it opens with a newline, it carries exactly three mark rows, those rows are equal in length, and every cell is a space or in `U+2580-U+259F`.
    - M1.red: before the mark existed the scenario exited 1 with `native-plugin-session-start ready human message does not open with a newline before the mark`. A second red was unplanned and more useful: a scripted patch applied the mark to `fallback()` but silently failed to match the main `emit(lines.join(...))` call, and the scenario stayed red on the ready branch until the missed call site was fixed by hand. The check caught an incomplete patch, not just a missing feature.
    - M1.green: after both call sites went through `withMark`, the same command exits 0 and `npm test` reports baseline plus 90 scenarios.
    - M2: the scenario drops the first four lines of each message and asserts the remainder still carries that branch's status token, its next command, and the authority note, on all six branches. The mark is therefore decorative by test, not by intention.
    - M2.red: mutating `withMark` to return `
${MARK}` — making the mark the whole message and thus load-bearing — makes the scenario exit 1 with `ready human message omits ['demo#1.1', 'OpenSpec and Git']` while every mark-shape assertion still passes, which isolates M2 from M1. A first attempt at this mutation via a scripted string replace silently failed to match and the suite exited 0; the mutation was only real once applied through an editor that fails loudly on a missed match, which is the second time in this task that a green turned out to mean "the patch never landed."
    - M2.green: restoring `withMark` to `
${MARK}
${line}` returns the scenario to exit 0.
    - M3: confirmed by the user on 2026-07-29 in Claude Code 2.1.220. The three rows render as three aligned rows rather than one collapsed line, and the outer ear-tuft cells `▙▖` and `▗▟` align with the eyes on a Chinese-locale Windows terminal. This resolves Q2 and, with it, the ambiguous-width reasoning behind D5: pinning the charset to the family the host's own banner uses was verified, not merely argued.
    - M3.red: the same observable, taken before the mark existed, is recorded as task 1.1's M2: the same user, the same host version, saw `SessionStart:startup says: Keel: deliverable-artifact-routes#2.1 - next: task-start.` on one line with no mark. That is the honest prior state of this check rather than a synthetic failure.
    - M3.green: on 2026-07-29 the same observation returns three aligned rows above the status line.
    - Review:
      - Status: pass
      - Acceptance check: M1 and M2 exercise the hook's stdout, its whole public interface, on every branch rather than on a happy path. M2 is the load-bearing one for D6: it proves the message survives the mark being stripped, which is what keeps a decorative element from becoming a dependency. M3 supplies the one property no local check can reach, since alignment is a property of the terminal rendering the cells, not of the bytes.
      - Scope check: `git status --porcelain` shows only the two Touch files plus this change's own directory. `npm test` reports baseline plus 90 scenarios, unchanged, so the mark assertions joined the existing scenario rather than adding one.
      - Findings: none
    - Blocker: none

- [x] 2.3 Frame the mark and status in a titled, self-sizing box
  - Covers:
    - D7: the titled box modelled on the host's welcome panel, adding the `U+2500-U+257F` border charset
    - D8: the box width is the longest content line and content is never truncated
  - Touch:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: for every branch the scenario reconstructs the box from the emitted message and asserts it closes - a `Keel` title in the top rule, every body row opening and closing with the border glyph, a bottom rule, and every row identical in display width - so a one-cell width error fails rather than skews
    - M2: a message whose status text is longer than the mark still produces a closed box of the wider size, and a change name is never truncated, proving the width is computed from content rather than fixed
    - M3 (regression): stripping the border and mark rows still leaves the branch status token, its next command, and the authority note on all six branches, so D6 survives the frame
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:953291fae44ac31f7f764db228cbe75009c6c5fb1d99f6249984197ec35d3919
    - M1: `python scripts/validate_plugin.py --scenario native-plugin-session-start` exits 0. `panel_problem` runs on all six branches and checks the frame closes: a `Keel` title in a `╭─╮` top rule, a `╰─╯` bottom rule, every body row enclosed by `│`, every row identical in length, and exactly three mark rows inside.
    - M1.red: before the frame existed the scenario exited 1 with `native-plugin-session-start ready panel has 4 rows, too few to frame the mark`.
    - M1.green: after `panel()` replaced `withMark` at both call sites, the same command exits 0 and `npm test` reports baseline plus 90 scenarios.
    - M2: a fixture change named `a-deliberately-long-change-name-that-exceeds-the-panel-default` produces a closed panel whose top rule is wider than the idle panel's, and the full 61-character name appears in the panel content, so no truncation occurred.
    - M2.red: two mutations were needed to isolate this check from M1. Pinning `width` to 58 with a `slice` truncation exits 1 at `missing-CLI human message omits ['missing or incompatible']` - real, but it trips the token check rather than the width check. Pinning `width` to 140 instead leaves every branch token intact and fails precisely where intended: `panel width is fixed, not derived from content: wide=144 narrow=144`.
    - M2.green: restoring `width` to `Math.max(...rows.map(row => row.length), PANEL_TITLE.length + 8)` returns exit 0, with the wide panel measuring 71 against the idle panel's 62.
    - M3: `panel_content` strips the border and every mark row, and the remaining text still carries each branch's status token, its next command, and the authority note on all six branches, so neither the frame nor the mark became load-bearing.
    - Review:
      - Status: pass
      - Acceptance check: every check reads the hook's stdout, which is its whole public interface, and reconstructs the panel from the emitted bytes rather than inspecting how it was built. M2 is the one that proves D8 rather than restating it: it needs content that no fixed width could hold, and its red had to be aimed twice before it failed for the width rather than for truncated text.
      - Scope check: `git status --porcelain` shows the two Touch files for this task, `plugins/keel/scripts/session-start.js` and `scripts/validate_plugin.py`, alongside `AGENTS.md` and `openspec/specs/keel-native-runtime-projection/spec.md`, which are completed work from tasks 3.1 and 4.1 and not modified here, plus this change's own directory. `npm test` reports baseline plus 90 scenarios.
      - Findings: none
    - Blocker: none

- [x] 2.4 Make the frame and mark opt-in, leaving the single line on by default
  - Covers:
    - D9: the frame and mark are gated behind `KEEL_SESSION_PANEL`, default off
    - D6: the message carries the same information whichever form it takes
  - Touch:
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: with `KEEL_SESSION_PANEL` unset, every branch emits a single-line human message carrying no frame glyph and no mark cell, and a value outside the allowlist leaves the default in place
    - M2 (regression): with `KEEL_SESSION_PANEL=1`, every branch emits the framed panel that task 2.3 verified, unchanged
    - M3 (regression): in both modes and on all six branches the message still names the branch status, its next command, and the authority note
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:65887dc2425c66a8b7e660b650648b479379af9306d122d8854defda42bf3104
    - M1: `python scripts/validate_plugin.py --scenario native-plugin-session-start` exits 0. With the variable unset, each of the six branches emits a message containing no character in either `U+2580-U+259F` or `U+2500-U+257F` and no newline. `run_session_start_hook` now removes `KEEL_SESSION_PANEL` from the child environment before optionally setting it, so the default-off assertion cannot pass or fail by accident of the developer's shell. A separate check drives the value `yeah` and requires the default to hold.
    - M1.red: with the assertions in place and `panel()` still unconditional, the scenario exits 1 with `native-plugin-session-start ready draws the panel without being asked: ['╭', '─', '─', '─', '─', '─']`. The allowlist half was aimed separately: relaxing `PANEL_ENABLED` to `Boolean(value)` exits 1 at `enabled the panel for a value outside the allowlist`, so that check is not carried by the default-off check.
    - M1.green: after gating `panel()` on `PANEL_ENABLED`, the same command exits 0 and `npm test` reports baseline plus 90 scenarios.
    - M2: the same loop re-runs every branch with `KEEL_SESSION_PANEL=1` and applies the full `panel_problem` frame check from task 2.3 - title, both rules, enclosed rows, equal widths, three mark rows - which still passes on all six. The content-derived width check was repointed at panel mode and still reports the wide panel at 71 against the idle panel's 62.
    - M3: in the default mode the whole message is checked for the branch status token, its next command, and the authority note; in panel mode the same tokens are checked against `panel_content`, which strips the frame and the mark. All six branches pass in both modes, so switching the decoration off costs no information.
    - Review:
      - Status: pass
      - Acceptance check: the branch matrix runs the real hook twice per branch and reads its stdout, so both modes are proven by the same public interface rather than one being asserted and the other assumed. M1's two independent reds matter here: default-off and allowlist-strictness are separate ways to leak the panel, and one check passing would otherwise have masked the other.
      - Scope check: `git status --porcelain` shows this task's two Touch files plus the files completed under tasks 3.1 and 4.1 and this change's own directory. `npm test` reports baseline plus 90 scenarios.
      - Findings: none
    - Blocker: none

## 3. The statements this change falsifies are corrected

- [x] 3.1 Rewrite the model-only claims that the human channel makes wrong
  - Covers:
    - keel-native-runtime-projection / Projected session state is reported to the user / The agent restates the projection even when the host showed it
    - D3: the two channels are complementary, so neither document may describe the other as the only path to the human
  - Touch:
    - AGENTS.md
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: evidence-first
    - M1: no file under `AGENTS.md`, `plugins/keel/scripts/session-start.js`, or `scripts/validate_plugin.py` still asserts that the projection reaches only the agent or is never rendered for the human, and each rewritten passage states both channels and why the agent still restates the projection
    - M2 (regression): the resident Session Start scenario still finds its required snippets in `AGENTS.md`, so correcting the wording does not drop the continuity rules that section already carried
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:16210b4d4e1f22eb601dedeb5bf349486931591abffc196cd9ed6bc4b5164047
    - M1: grepping the three files for `reaches only you`, `never rendered for the human`, `reaches nobody`, `model-only channel`, and `sole reader` returns no match. Each passage was rewritten to state both channels and why they are not redundant: `AGENTS.md` now says a host may also show the projection directly, "that is a second channel, not a substitute, because what the user needs to check is the state you are actually working from"; the `DISCLOSURE` comment says the host's line says what the state is while the instruction "surfaces the state the agent actually worked from"; the `SESSION_START_DISCLOSURE` comment says "one proves the state was shown, this one proves the agent was told to say which state it is working from, and only the second can expose the two disagreeing."
    - M2: the resident Session Start section still contains all three tokens `RESIDENT_SESSION_START_REQUIRED` pins — `to the user in your first reply`, `keel context`, and `never infer continuity from native memory` — and `npm test` reports baseline plus 90 scenarios, so the `native-plugin-session-start` scenario that reads that section still passes.
    - Review:
      - Status: pass
      - Acceptance check: the passages are prose contracts, so their observable behavior is what a reader finds in them. M1 checks both directions — the falsified claims are gone, and each replacement states the thing that is now true — rather than only asserting an absence, which a deletion would also satisfy. M2 guards the replacement against dropping the continuity rules the section already carried.
      - Scope check: `git status --porcelain` shows exactly the three Touch files modified, `AGENTS.md`, `plugins/keel/scripts/session-start.js`, and `scripts/validate_plugin.py`, plus this change's own untracked directory. `assets/bootstrap/AGENTS.md` was deliberately not touched: it never carried the falsified sentence, and its managed block sits at 1014 of its 1023-byte ceiling.
      - Findings: none
    - Blocker: none

## 4. The deltas become the live spec

- [x] 4.1 Promote the delta into the live spec and record the workflow change
  - Covers:
    - keel-native-runtime-projection / SessionStart projection reaches the human directly
    - keel-native-runtime-projection / Projected session state is reported to the user
  - Touch:
    - openspec/specs/keel-native-runtime-projection/spec.md
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: evidence-first
    - M1: after the delta is promoted into `openspec/specs`, `npx openspec validate session-start-reaches-the-human --strict` reports the change valid, `npm test` reports pass at the raised scenario count, and the live requirement no longer states that the projection is delivered on a model-only channel
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ce96d5f718827fc5e00f826330d61aa9ebabd7b01c064aa495b1d33e26b63a2d
    - M1: the delta's MODIFIED requirement replaced the live one in place and its ADDED requirement was appended, taking `openspec/specs/keel-native-runtime-projection/spec.md` from 230 to 277 lines and 13 to 14 requirements. `npx openspec validate session-start-reaches-the-human --strict` reports the change valid; `npm test` reports baseline plus 90 scenarios; and grepping the live spec for `model-only channel` and `sole reader` returns nothing, so the sentence I3 names is gone from the file it named. `keel/CHANGELOG.md` carries the 5.4.0 entry.
    - Review:
      - Status: pass
      - Acceptance check: the observable is what the promoted file now says, checked in both directions — the falsified sentence is absent, and the requirement that replaces it is present and validates under the schema. The default-off decision taken after this task started does not reopen it: the ADDED requirement asks for a human-visible message carrying status, selection, and next command, which the default single line satisfies exactly as the panel does, so gating decoration changed no requirement.
      - Scope check: `git status --porcelain` shows this task's two Touch files, `openspec/specs/keel-native-runtime-projection/spec.md` and `keel/CHANGELOG.md`, alongside files completed under other tasks of this change and this change's own directory. The write guard refused a `keel/CHANGELOG.md` write while task 2.4 was still the authorized task, which is why this task was explicitly re-authorized rather than inheriting the previous one's permission.
      - Findings: none
    - Blocker: none

- [x] 4.2 Document the panel switch where a user would look for it
  - Covers:
    - D9: the frame and mark are gated behind `KEEL_SESSION_PANEL`, default off
  - Touch:
    - README.md
  - Verify:
    - Strategy: evidence-first
    - M1: README names `KEEL_SESSION_PANEL`, states that it is off by default, shows the value that enables it, and says what turning it on changes, so the switch is discoverable without reading the changelog or the hook source
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:08eb016e8cb781bfb4807e30149aa2946fac945d325eb29e5c479b9173985f65
    - M1: the `## Use` section now shows the default single-line message verbatim, then names `KEEL_SESSION_PANEL=1`, states it is off by default, and says that turning it on changes presentation only because the same status and next command appear in both forms. A reader looking for the switch finds it in the section describing what happens at session start, not in the changelog or the hook source. `npm test` reports baseline plus 90 scenarios.
    - Review:
      - Status: pass
      - Acceptance check: the observable for a documentation task is what the document tells a reader who does not already know the answer. M1 checks all four things a user needs — the name, the default, the value that flips it, and the consequence — rather than only that the identifier appears somewhere.
      - Scope check: `git status --porcelain` shows `README.md`, this task's only Touch entry, alongside files completed under earlier tasks of this change and this change's own directory.
      - Findings: none
    - Blocker: none

## Invalidates

- I1: "A plugin projection reaches only you, so a state the user never sees is a state the user cannot correct." — the Session Start section of `AGENTS.md`. The justification becomes false once the host renders the projection directly; the obligation it justifies survives for a different reason. Updated by: 3.1
- I2: "This text is injected into the agent and never rendered for the human, so without an explicit instruction the projection reaches nobody who can catch it being wrong." — the `DISCLOSURE` comment in `plugins/keel/scripts/session-start.js`. Updated by: 3.1
- I3: "SessionStart projection is delivered on a model-only channel, so the agent is the sole reader unless it speaks." — the `Projected session state is reported to the user` requirement in `openspec/specs/keel-native-runtime-projection/spec.md`. Updated by: 4.1
- I4: "The projection is delivered through additionalContext, which the host injects into the agent and never renders for the human." — the `SESSION_START_DISCLOSURE` comment in `scripts/validate_plugin.py`. Updated by: 3.1
- I6: "The mark must lead, be drawn from the pinned charset, and be rectangular." and "human message does not open with a newline before the mark" - the `mark_problem` docstring and first check in `scripts/validate_plugin.py`, which task 2.2 verified and task 2.3 falsifies: once a titled border wraps the mark, the first row after the newline is the top rule, not a mark row. Updated by: 2.3
- I7: "begins with a newline followed by the three mark rows" - the M1 wording of task 2.2 in this file, true of what 2.2 shipped and wrong the moment 2.3 lands. Discard reason: it is completed-task evidence describing what was verified at that point, and rewriting it would falsify the record rather than correct it.
- I5: "唯一对人可见的缝是 exit 2 + stderr" and "keel 目前完全没覆盖它" — issue #32's analysis of available channels. The first is wrong for Claude Code 2.1.220; the second stays true of the statusline it proposes. Durable owner: https://github.com/TanglmChris/keel/issues/32

## Expectation Coverage

- E1: The human is told the Keel state and next action at session start without sending a message. Covered by: 1.1
- E2: Every projection branch, degraded ones included, produces the human line. Covered by: 2.1
- E3: The human channel authorizes nothing and the hook keeps exit 0, no blocking, and no state writes. Covered by: 2.1
- E4: Documents that justify the disclosure rule by the absence of a human channel are corrected rather than left standing. Covered by: 3.1
- E9: A user-facing switch is discoverable from the README rather than only from the changelog or the source. Covered by: 4.2
- E8: Decoration that appears in every session of every installation is opted into rather than inherited, and turning it off costs no information. Covered by: 2.4
- E7: The projection frames itself the way the host frames its own welcome panel, without truncating the identifier a user is reading. Covered by: 2.3
- E6: The projection carries a Keel mark that survives a CJK-locale terminal and never becomes load-bearing. Covered by: 2.2
- E5: The statusline segment proposed in issue #32 remains unbuilt and its rejection is recorded where a future reader will find it. Durable owner: https://github.com/TanglmChris/keel/issues/32
