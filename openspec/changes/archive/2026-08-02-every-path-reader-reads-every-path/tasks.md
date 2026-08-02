## 1. Read the path the filesystem has

- [x] 1.1 Extract a declared path by where it ends, in one shared reader
  - Covers:
    - keel-core-gates / A declared path is extracted by where it ends, not by what it is made of / A path with non-ASCII directories is accepted
    - keel-core-gates / A declared path is extracted by where it ends, not by what it is made of / A path is not required to begin with an ASCII segment
    - keel-core-gates / A declared path is extracted by where it ends, not by what it is made of / A path containing whitespace is declared in backticks
    - keel-core-gates / A declared path is extracted by where it ends, not by what it is made of / A path ending a sentence is not extended by its punctuation
    - keel-core-gates / A declared path is extracted by where it ends, not by what it is made of / A path that does not exist is still refused
    - D1 — a path is a non-whitespace run containing a separator
    - D2 — a backtick-wrapped path is taken verbatim
    - D3 — trailing punctuation is trimmed in both ASCII and CJK forms
    - D4 — the change-name validators are deliberately untouched
    - D5 — this is not precedent for widening the pattern #58 reports
    - F1 — four copies of one character class
    - F2 — the three measured failing shapes
    - F3 — Touch already accepts the backtick form
    - A1 — a path with whitespace is expected to arrive in backticks
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario declared-paths-are-read-whole` passes. The scenario builds a repository holding a file under a CJK directory, a file whose first segment is CJK, and a file whose name contains a space, then drives `keel gate change-close` and `keel gate task-complete` over `Durable owner:`, `Resolved here:`, and a `keel/archive/…` reference, asserting each is accepted; it asserts the backtick form carries the whitespace path; it asserts a path followed by `。` and by `,` is read without the punctuation; and it asserts a path that does not exist is still refused, naming the full path rather than a prefix.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates` still passes, so the ASCII paths every existing task declares are unaffected.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario git-paths-carry-no-escaping` still passes — the same defect class on the worktree-reading side, fixed in #40, stays fixed.
    - M4 (regression): `npm test` passes.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:07cecb7166c103744bdba35a7cfe638d8ecebf72b42f90e9320a4feb5321160d
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario declared-paths-are-read-whole` reports `declared-paths-are-read-whole scenario passed.` The fixture holds three real files — one under a CJK directory, one whose first segment is CJK, one whose name contains a space — and drives `keel gate change-close` over `Durable owner:` in both `Findings` and `Expectation Coverage`, the backtick form, a path abutting `。` and one abutting `,`, and a path that does not exist.
    - M1.red: fail, as required, against the branch base `68e4fd2` (5.17.0). Restoring `src/core/gates.js` from that commit and re-running reports `a Expectation Coverage durable owner naming an existing file under a non-ASCII directory was refused, and the refusal names a path nobody wrote.` beside the gate's actual output, `E1 names \`notes/note-006-\` as its durable owner, but no such file exists in this repository.` — which is #60's reported message verbatim, reproduced through the scenario rather than quoted from the issue.
    - M1.green: pass. With `declaredPath()` in place all six shapes are accepted or refused as the requirement states. The last is the one that matters most: `notes/不存在的目录/note.md` is still refused, and the refusal now names the whole path instead of a prefix — widening the extractor did not weaken the existence check, which is the only thing making a path a valid owner at all.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates` reports `core-gates scenario passed.` The ASCII paths every existing task declares are unaffected. `expectation-completion-gates`, the other reader of `Expectation Coverage`, also passes.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario git-paths-carry-no-escaping` reports `git-paths-carry-no-escaping scenario passed.` The same defect class on the worktree-reading side, fixed in #40, stays fixed — and the two are now covered from both directions.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 127 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: every check runs through the gate a user runs — `keel gate change-close` over a real repository holding real files — rather than over the regular expression in isolation. The red half reproduces #60's message verbatim from the branch base. The negative case is asserted alongside the positives, because a widening whose test suite only proves that more things pass has not shown it kept the check.
      - Scope check: `git status --short` lists exactly `src/core/gates.js` and `scripts/validate_plugin.py`, the two Touch entries, plus this change's own untracked directory. The completion gate's own attribution, recorded in this task's manifest at task start, reported no out-of-Touch path.
      - Findings: one. Reproducing #60 turned up two shapes the issue does not report and that its own suggested fix would have left broken. A path whose *first* segment is non-ASCII did not match at all rather than truncating — a different failure needing its own case — and a path containing a space truncated at the space, which no character-class widening can fix because the terminator is the problem. Both are covered by M1, and the second is why the backtick form is part of this change rather than the optional extra the issue offers it as. Resolved here: M1
    - Blocker: none
    - Blocker: none

## 2. Close

- [x] 2.1 Release 5.18.0
  - Covers:
    - E5 — a reader of the release notes learns a path in any script may now be named, and how to name one containing a space
    - I1, I2 — the wordings this change makes stale
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
    - openspec/specs/keel-core-gates/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.18.0
    - M2: `keel/CHANGELOG.md` carries a 5.18.0 entry naming the reported failure and the two shapes found while reproducing it, stating the backtick form for a path with whitespace, and recording that #58 is the same cause with the opposite repair so this entry is not read as licence to widen a pattern that over-matches
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate every-path-reader-reads-every-path --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a5d92d1c63da4dc15d58da15be01cd03ad6474d77dd2815e2618c743d13532b4
    - M1: pass. `version-alignment` passes; 20 markers moved from 5.17.0 to 5.18.0 across the package and lockfile, both plugin manifests, the three `keel:start` blocks, the twelve overlay markers, the AGENTS.md title and preflight line, and the validator constants.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.18.0 - every path reader reads every path`, naming the reported failure and the two shapes found while reproducing it, stating the backtick form and that it is an existing `Touch` convention rather than a new one, and recording that #58 is the same cause with the opposite repair — so the entry cannot be read as licence to widen a pattern whose problem is over-matching.
    - M3: pass. The delta is promoted into `openspec/specs/keel-core-gates/spec.md`, `node bin/keel.js openspec validate every-path-reader-reads-every-path --strict` reports the change valid, and `published-specs-validate-strictly` — the check added in 5.17.0 — reports `21 published specs validate strictly against openspec 1.6.0` against the store now containing this requirement.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 127 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: the release claims are checked by running what they describe. M3 is worth naming: the requirement added here was promoted and then validated by the store-validation check 5.17.0 added one release earlier, so each release in this stack is now verified by the mechanism the previous one built.
      - Scope check: `git status --short` lists only 2.1 Touch entries plus this change's own directory, and the completion gate's attribution — recorded in this task's manifest at task start — reported no out-of-Touch path. Third task bound by the 5.16.0 check.
      - Findings: none
    - Blocker: none

## Invalidates

- I1: "any repo-relative path that exists" — the enumeration of accepted durable-owner forms, which appears in `src/core/gates.js` problem text, in the `Project Conventions` section of `AGENTS.md`, and in `src/skills/keel-review-checklist/SKILL.md` with its `plugins/keel/` projection. The phrase was true of the rule and false of the implementation, which accepted only paths spellable in ASCII; after this change it is true of both, and the backtick form it does not mention becomes available. Discard reason: the sentence is correct as written and becomes *more* correct here — the repair is in the implementation that failed to honour it. The backtick form is recorded by the 5.18.0 changelog entry and by the promoted requirement, which is where a reader looking for accepted forms is sent.
- I2: "version=5.17.0" — grep it and you find the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, plus the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`; the same version is written as `"version": "5.17.0"` in `package.json`, `package-lock.json`, and both plugin manifests, in the AGENTS.md title and its preflight line, and in the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants of `scripts/validate_plugin.py`. Updated by: 2.1

## Expectation Coverage

- E1: A path that exists can be named as a durable owner whatever script it is written in. Covered by: 1.1
- E2: A path containing whitespace can be named, through the form `Touch` already accepts. Covered by: 1.1
- E3: A path that does not exist is still refused, and the refusal names the whole path rather than a prefix. Covered by: 1.1
- E4: One extractor serves every gate reader, so this class cannot be repaired in one reader and left in the others. Covered by: 1.1
- E5: A reader of the release notes learns what is now nameable and how to name a path containing a space. Covered by: 2.1
