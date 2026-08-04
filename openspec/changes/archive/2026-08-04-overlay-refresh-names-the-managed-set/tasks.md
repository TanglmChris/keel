# Tasks

## 1. Derive the label the summary reports

- [x] 1.1 The refresh summary names the managed set, and a check watches it
  - Covers:
    - keel-openspec-surface-overlay / Every overlay summary names the managed action set / The refresh summary names the derived set
    - keel-openspec-surface-overlay / Every overlay summary names the managed action set / Refresh and removal agree on one repository
    - keel-openspec-surface-overlay / Every overlay summary names the managed action set / A drifting summary is a failing check
    - D1 — derive the label rather than correct the literal
    - D2 — assert by comparison, with a positive control that both lines exist
    - D3 — pin transitively to the doctor literal instead of writing a third copy
    - D4 — split each assertion so it carries its own message
    - F1 — nothing consumes the refresh summary line
    - F2 — neither sibling assertion is pinned to a label
    - F3 — the defect reproduces at 5.24.0 on the current tree
    - A1 — `openspec-surface-overlay` is the scenario that already owns both halves
  - Read:
    - bin/keel.js
    - scripts/validate_plugin.py
    - openspec/specs/keel-openspec-surface-overlay/spec.md
    - openspec/changes/overlay-refresh-names-the-managed-set/design.md
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the shipped CLI reports the managed set. `keel --init --target claude` on a temporary repository prints an overlay summary naming `apply/archive/sync`, and the string `OpenSpec apply/archive overlay` does not appear in that output. The same run's removal summary from `--uninstall` names the same three actions, so the two directions agree on one repository.
    - M2: the check fires on drift, and distinguishes drift from absence. Within the `openspec-surface-overlay` scenario, the label extracted from the refresh line and the label extracted from the doctor line are compared, and four failures are reported distinctly: the refresh line absent, the doctor line absent, the two labels disagreeing, and an extracted label that is empty. The positive control is proven by mutation rather than assumed — the extraction is aimed at a line that does not exist and the check must fail as "absent", not pass on two empty strings agreeing.
    - M3 (regression): `openspec-surface-overlay` and `uninstall-removes-the-overlay` both pass, so the surfaces covered, the counts reported, the per-surface dry-run lines, and the doctor health lines are unaffected.
    - M4 (regression): `assertion-shape-count` passes at its recorded number, so the added assertions did not put two failures behind one message.
    - M5 (regression): `npm test` passes with no failing scenario and no exception.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the fix would change which actions receive the overlay, or `overlayActionLabel()`'s exclusion of `propose`. This change reports the set; it does not decide it.
    - Stop if any existing check has to be repinned to a different literal to make this pass. That would mean something did depend on the wrong label, and what depends on it is the owner's call.
    - Stop if the summary line needs to become machine-readable for the assertion to work. It is human-facing output, and giving it a parseable contract is a new interface.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:bd1a3e899dfc68d39ad20c58e34db401ef6dbc847a74b3a7baf33f4a8dea6156
    - M1: pass. Measured through the shipped CLI on one temporary repository, the three commands run back to back: `--init` printed `keel: OpenSpec apply/archive/sync overlay refreshed=8 current=0 missing=0`, `--doctor` printed `Keel apply/archive/sync overlay: ok - 8/8 under apply/archive/sync skills and commands`, and `--uninstall` printed `keel: OpenSpec apply/archive/sync overlay removed=8 absent=0 missing=0`. All three name the same three actions; the string `OpenSpec apply/archive overlay` appears in none of them. This is the same measurement shape the issue used to report the defect, so the before and after are directly comparable.
    - M1.red: fail. `openspec-surface-overlay scenario overlay summaries disagree: refresh names 'apply/archive' and doctor names 'apply/archive/sync'. They describe the same managed surface list, so one of them is written beside the action set instead of derived from it.` This is the shipped 5.24.0 state rather than a mutation — the literal at `bin/keel.js:1306` was still there, and the check named which of the two was written beside the set.
    - M1.green: pass, after the literal `OpenSpec apply/archive ` became `OpenSpec ${overlayActionLabel()} `. One line; the function it calls, its exclusion of `propose`, the counts, and the per-surface dry-run lines are untouched.
    - M2: pass. The `openspec-surface-overlay` scenario now extracts the action label from all three summaries produced by one repository — refresh from the init output, health from the doctor output, removal from a new uninstall step — and compares refresh and removal against doctor. Four failures report distinctly, each behind its own `if` with its own message: a summary line absent, a label that derived to empty, refresh disagreeing with doctor, and removal disagreeing with doctor. The doctor label is already pinned to the literal `apply/archive/sync` at two sites above, so the comparison pins the other two transitively and an action joining the managed set needs one literal updated rather than three.
    - M2.red: fail, in three separate mutations, because a check that passes on *agreement* also passes when the mechanism producing both sides is broken — the failure mode the precedent names, so each branch was aimed at rather than assumed. (1) Disagreement: the shipped state above, M1.red. (2) Absence: the refresh pattern was aimed at `overlay refreshedZZ=`, a line that does not exist, and the result was `found no refresh overlay summary at all, so there was no label to compare rather than a label that disagreed` — not a pass on two empty strings agreeing. (3) Empty: the refresh line was made to interpolate `""` while `overlayActionLabel()` stayed correct, which is the drift direction where one line stops sharing the source, and the result was `read an empty action label from the refresh summary; a label that derives to nothing reports no actions at all`. Note on (3): making `overlayActionLabel()` itself return empty does *not* reach this branch — the doctor literal assertion above fires first — so the mutation was aimed at the one caller instead, which is the case the branch can actually see. *Precedent applied: `an-assertion-that-never-failed-proves-nothing`.*
    - M2.green: pass, with all three mutations reverted; `git diff --stat` after reverting shows `bin/keel.js | 2 +-`, the single intended line.
    - M3: pass. `openspec-surface-overlay` and `uninstall-removes-the-overlay` both report `scenario passed.` — the surfaces covered, the counts, the per-surface dry-run lines, the Codex prompt-directory surfaces, and the doctor health and missing-marker lines are unaffected.
    - M4: pass. `assertion-shape-count` reports `passed: 75 sites, a bound on a shape and not a count of defects.` — unchanged at its recorded number, because every added assertion is a single condition carrying its own message rather than an `or` guarding several failures.
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 133 scenarios.` — no failing scenario, no exception, none skipped. 133 before and after: this change extended an existing scenario rather than adding one.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a summary names the set it derives from, and M1 proves it the way a reader would — three commands on one repository, reading what they printed, which is the same comparison the issue used to report the defect. That is behavior through the public interface, not the shape of `overlayActionLabel()`. M2 is the part that has to outlive this change: the defect was not the wrong string but a copy nobody was watching, so a fix that only corrected the string would have been the same defect one action later. Comparing the three summaries against each other rather than restating the literal is what avoids writing a fourth copy, and the transitive pin means the next action to join needs one literal updated. The three mutations matter more than the green here — an agreement check passes when both sides are broken, so absence and empty were each aimed at and watched to fail with their own message. One is worth stating plainly: the empty branch is unreachable by breaking `overlayActionLabel()`, because the doctor assertion fires first, and it was proven through the caller-level drift it can actually see rather than recorded as proven by a mutation that never reached it.
      - Scope check: `git status --short` shows `bin/keel.js` and `scripts/validate_plugin.py` — the Touch list exactly — plus this change's own untracked directory, which is the record-write layer. Both files were clean when the task started, so deterministic attribution covers every write here. `keel guard status` reports the fingerprint unchanged from the one recorded at task-start, so no contract edit occurred. Every write went through the editing tools; no heredoc was used, so the write guard saw each one.
      - Findings: two. First: the same drift class exists in the published specs — nine sites across `openspec/specs/keel-openspec-surface-overlay/spec.md` and `openspec/specs/keel-target-surface-diagnostics/spec.md` still say `apply/archive` in requirement prose and scenario wording, and three of them spell the set three different ways. Spec prose cannot be derived and no assertion can compare it, which is why it needs an owner rather than a mechanism; it is also outside this task's Touch, and rewriting requirement text is a spec change of its own. Durable owner: https://github.com/TanglmChris/keel/issues/79. Second: the comment above `overlayActionLabel()` describes the literal in the past tense — "the label *was* the literal string" — which was inaccurate while a second copy of it sat twenty lines below in the same file. It is accurate now, and the comment needed no edit for that to become true. Resolved here: M1, the run in which the last copy stopped being a literal.
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## 2. Close

- [x] 2.1 Release 5.25.0
  - Covers:
    - E4 — a reader of the release notes learns which line was wrong, why the copy was the defect, and that a check now watches it
    - I1, I2 — the wordings this change makes stale
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
    - openspec/specs/keel-openspec-surface-overlay/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.25.0
    - M2: `keel/CHANGELOG.md` carries a 5.25.0 entry naming the line that was wrong, that the label is now derived from the managed set, that the two summaries on one repository agreed only in one direction before, and that the line now has an assertion where it had none
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate overlay-refresh-names-the-managed-set --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:cc375f88ff4570af05ec1b447aa48337266f36911a34da6fad4b943067c2c764
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.24.0 to 5.25.0 via `node scripts/bump_version.js 5.25.0` — the package and lockfile, both plugin manifests, the three `keel:start` blocks in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, the AGENTS.md title and preflight line, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants. The scenario reads every marker rather than sampling, so one left at 5.24.0 fails by path.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.25.0 - the copy nobody was watching`. It names the line that was wrong and where it sat, that `overlayActionLabel()` was written in 5.20.0 for exactly this drift and that converting `--doctor` left a second copy of the literal twenty lines below it, the back-to-back measurement in which `--init` and `--uninstall` described one surface list differently, that the label is now derived and the counts and `propose` exclusion are unchanged, that the assertion compares the three summaries against each other rather than restating the literal a fourth time, and the three mutations including the one that does not reach its branch. It also records #79 as the same drift class found in spec prose and filed rather than folded in.
    - M3: pass. The delta is promoted — `Every overlay summary names the managed action set` and its three scenarios now sit at the end of `openspec/specs/keel-openspec-surface-overlay/spec.md`, which is an ADDED requirement and therefore an append rather than a replacement. `node bin/keel.js openspec validate overlay-refresh-names-the-managed-set --strict` reports `Change 'overlay-refresh-names-the-managed-set' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding it.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 133 scenarios.` — no failing scenario, no exception, none skipped. Unchanged at 133: this change extended an existing scenario rather than adding one.
    - Review:
      - Status: pass
      - Acceptance check: each check names the artifact a reader would open. M1 is the scenario that reads every version marker rather than spot-checking, which is what makes "every marker names 5.25.0" a measurement instead of a claim. M3 asserts the promotion through the two tools that consume the published store rather than by reading the file back. M2 is the one prose check, and what it asserts is what a reader cannot reconstruct from the diff: that the defect was a copy rather than a wrong string, which is why the assertion and not the one-line fix is the durable part, and the non-obvious mutation result — that breaking `overlayActionLabel()` never reaches the empty branch because the doctor assertion fires first. A future reader who does not know that would record a control as proven by a mutation that never touched it.
      - Scope check: `git status --short` shows twenty-three paths — this task's twenty-two Touch entries plus `bin/keel.js` from task 1.1 — and this change's own directory, which is the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at 2.1's task-start, so no contract edit occurred. Note the gate's limit here, which is the same one the previous release task hit: `bin/keel.js` and `scripts/validate_plugin.py` were both already dirty when 2.1 started, carrying 1.1's writes, so deterministic attribution cannot speak to them and this Review is their scope evidence. 2.1's own write to `scripts/validate_plugin.py` is the two version constants `bump_version.js` reported changing, and M1 is what verifies them; 2.1 wrote nothing to `bin/keel.js`, whose diff remains the single line M2.green recorded under 1.1.
      - Findings: none
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## Invalidates

- I1: "OpenSpec apply/archive " written as a literal inside the summary at the end of `refreshOpenSpecSurfaceOverlay` in `bin/keel.js` — the string a reader greps to find where that label comes from, and the second copy of the literal that `overlayActionLabel()` was written to end. Its neighbouring comment, which says the label "was the literal string" and became wrong when a third action joined, stops describing a copy that is still there. Updated by: 1.1
- I2: "version=5.24.0" — grep it and you find the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, plus the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`; the same version is written as `"version": "5.24.0"` in `package.json`, `package-lock.json`, and both plugin manifests, in the AGENTS.md title and its preflight line, and in the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants of `scripts/validate_plugin.py`. Updated by: 2.1
- I3: "so an action added to the set cannot be left out of the diagnostic" — the 5.20.0 entry in `keel/CHANGELOG.md` describing the doctor label's conversion. The claim was true of the diagnostic and not of the refresh line beside it, which is this change. Discard reason: a shipped changelog entry records what that release did, and editing one to match later behavior makes the history unreadable as history. The 5.25.0 entry says which line the earlier conversion missed.
- I4: "Durable owner: https://github.com/TanglmChris/keel/issues/75" in the Review findings of `openspec/changes/archive/2026-08-03-uninstall-leaves-nothing-behind/tasks.md`. Discard reason: archived evidence is a record of what was true when that task closed, and the issue it names is closed by this change rather than by editing the record that filed it.

## Expectation Coverage

- E1: The actions a summary names come from the set the overlay actually covers, in every direction that reports one. Covered by: 1.1
- E2: An action joining the managed set reaches the refresh summary without anyone editing that line. Covered by: 1.1
- E3: The next drift in this line is a failing check rather than something a reader notices by comparing two commands. Covered by: 1.1
- E4: A reader of the release notes learns which line was wrong, why a second copy of a corrected literal was the defect, and that the line now carries an assertion. Covered by: 2.1
