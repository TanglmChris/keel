# Tasks

## 1. `keel --help` lists the triage command

- [x] 1.1 `keel --help` names `keel triage` and both its flags
  - Covers:
    - keel-unattended-triage / The triage command is discoverable from `--help` / Help lists the triage command
    - D1 — add the missing lines as literals, matching how every other HELP line is written
    - D2 — house the requirement inside keel-unattended-triage rather than a new capability
    - D3 — verify by extending the existing `cli` scenario
    - F1 — `triage` is the only dispatcher-recognized command absent from HELP's Usage block
    - F2 — reproduced 2026-08-05 at 5.29.0 by `node bin/keel.js --help | grep -i triage`
  - Read:
    - bin/keel.js
    - scripts/validate_plugin.py
    - README.md
    - openspec/changes/help-lists-the-command-it-has/design.md
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `keel --help` lists the command through the real CLI. `node bin/keel.js --help` exits 0 and its `Usage:` block contains a `keel triage` line, and that line names both `--labels` and `--issue`.
    - M2 (regression): the `cli` scenario and full `npm test` pass, so `--help`'s `Usage:` presence, `--version`, and the missing-repo `--check` behavior the scenario already asserts are unaffected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if closing this needs a change to `keel triage`'s flags, behavior, admission logic, or exit codes — this task is discoverability only.
    - Stop if the fix needs a generated/derived Usage block instead of one added line (per D1) — that is a redesign this task does not authorize.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0849c04f7991574f733e8bb07a55115bfb63089eaa79f766953e7ff5d375ad68
    - M1: pass. `node bin/keel.js --help` exits 0 and its `Usage:` block prints `keel triage [repo] [--labels <l1,l2>] [--issue <n>] [--json]`, naming both `--labels` and `--issue`. The `cli` scenario in `scripts/validate_plugin.py` asserts the same three things separately (the line exists, it names `--labels`, it names `--issue`) against the same live CLI output, and reports `cli scenario passed.`
    - M1.red: fail. `cli scenario expected keel --help Usage: block to list a \`keel triage\` line.` — measured by temporarily stashing only the `bin/keel.js` half of this task's diff (`git stash push --keep-index -- bin/keel.js`) and rerunning the `cli` scenario against the unfixed HELP text; the fingerprint recorded at task-start was unaffected since the stash/pop round-trip restored the file byte-for-byte before continuing.
    - M1.green: pass, after `git stash pop` restored the added lines; `git diff --stat bin/keel.js` shows `3 insertions(+)` — the same three-line addition (`Usage:` line, two `Examples:` lines) this task started with.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario cli` reports `cli scenario passed.`, and `npm test` reports `validation --all passed: baseline plus 138 scenarios.` — no failing scenario, no exception. `assertion-shape-count` (a sibling regression check unrelated to this task's own Acceptance) initially failed at 76 measured sites against 75 recorded, because the first version of the new check was one `if` guarding three distinct failures (line absent, `--labels` absent, `--issue` absent) behind one message; split into three single-cause `if` statements per that scenario's own guidance, after which it reports `75 sites` again with no change to the recorded constant.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that `keel --help`'s `Usage:` block lists `keel triage` naming both flags, and M1 proves it by reading the same live `--help` stdout a user would see, not the shape of `HELP` or of `parseArgs`. The `cli` scenario now asserts the line's presence and each flag's presence as three separate conditions, so a future regression names which of the three broke rather than a compound message covering all three.
      - Scope check: `git status --short` shows exactly the Touch list — `bin/keel.js` and `scripts/validate_plugin.py` — plus this change's own untracked directory, which is the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at task-start, so no contract edit occurred, and neither file was in `startedDirty` (only the four files under this change's own directory were), so deterministic attribution covers both writes cleanly. Every write went through the Edit tool; the one `git stash`/`git stash pop` round trip used to capture clean red evidence restored `bin/keel.js` to byte-identical content, verified by `git diff --stat` showing `3 insertions(+)` before and after.
      - Findings: none
    - Blocker: none

## 2. Close

- [x] 2.1 Release 5.30.0
  - Covers:
    - E1 — a user learns `keel triage` and its flags exist from `keel --help` alone
    - E2 — a reader of the release notes learns which command was undiscoverable and why
    - I1 — the version markers this task moves
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
    - openspec/specs/keel-unattended-triage/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.30.0
    - M2: `keel/CHANGELOG.md` carries a 5.30.0 entry naming the missing `keel triage` HELP line, that it was documented in exactly one place before this, and that a check now watches it
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate help-lists-the-command-it-has --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:0e782cdb085e20fac53ce16542c37effeabcbe02376e689b1c86cb64b3e5d469
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.29.0 to 5.30.0 via `node scripts/bump_version.js 5.30.0` — the package and lockfile, both plugin manifests, the `keel:start` blocks in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.30.0 - a command exists whether or not the help text says so`. It names the missing `keel triage` line, that it was documented in exactly one place (`README.md`) and not the one reachable from the terminal, that `--help` now lists it in the position README already uses, that grep confirmed `triage` was the only one of eight dispatcher commands missing (not a pattern needing a general mechanism), and that the `cli` scenario's new check is split into three single-cause conditions after `assertion-shape-count` caught the first, compound version.
    - M3: pass. The delta is promoted — `The triage command is discoverable from \`--help\`` and its scenario now sit in `openspec/specs/keel-unattended-triage/spec.md`, inserted directly after the sibling doctor-parity requirement it pairs with (an ADDED requirement, appended rather than replacing anything). `node bin/keel.js openspec validate help-lists-the-command-it-has --strict` reports `Change 'help-lists-the-command-it-has' is valid`, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding it.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 138 scenarios.` — no failing scenario, no exception, none skipped. Unchanged at 138: this change extended the existing `cli` scenario rather than adding one.
    - Review:
      - Status: pass
      - Acceptance check: M1 is the scenario that reads every version marker rather than spot-checking, which is what makes "every marker names 5.30.0" a measurement instead of a claim. M3 asserts the promotion through the two tools that consume the published store (`openspec validate --strict` and `published-specs-validate-strictly`) rather than by reading the file back. M2 is the one prose check, and what it asserts is what a reader cannot reconstruct from the diff alone: that `triage` was confirmed the *only* gap among eight dispatcher commands rather than assumed, and that the compound-condition mistake was caught and split rather than shipped.
      - Scope check: `git status --short` shows twenty-two paths — this task's twenty-one Touch entries (twenty-two listed, `keel/CHANGELOG.md` counted once) plus `bin/keel.js` from task 1.1 — and this change's own untracked directory, which is the record-write layer. `keel guard status` reports the fingerprint unchanged from the one recorded at 2.1's task-start, so no contract edit occurred. Note the same gate limit the prior release in this repository's history hit: `scripts/validate_plugin.py` was already dirty when 2.1 started, carrying 1.1's `cli`-scenario writes, so deterministic attribution cannot speak to it and this Review is its scope evidence instead — 2.1's own change to that file is exactly the two version constants `bump_version.js` reported changing, which M1 verifies. `bin/keel.js` shows modified in `git status` but is not in 2.1's Touch at all; it carries only 1.1's already-completed write, confirmed by `git diff --stat bin/keel.js` matching the `3 insertions(+)` recorded in 1.1's own Evidence.
      - Findings: none
    - Blocker: none

## Invalidates

- I1: "version=5.29.0" — the `keel:start` managed markers in `AGENTS.md`, `CLAUDE.md`, and
  `assets/bootstrap/AGENTS.md`; the four `.claude/commands/opsx/*.md` files; the four
  `.claude/skills/openspec-*/SKILL.md` files; the four `.codex/skills/openspec-*/SKILL.md` files;
  `"version": "5.29.0"` in `package.json`, `package-lock.json`, and both plugin manifests
  (`plugins/keel/.claude-plugin/plugin.json`, `plugins/keel/.codex-plugin/plugin.json`); and
  `PACKAGE_VERSION`/`PROTOCOL_VERSION` in `scripts/validate_plugin.py`. Updated by: 2.1

## Expectation Coverage

- E1: A user running `keel --help` learns that `keel triage` exists and what both its flags are, without reading `README.md` or the source. Covered by: 1.1
- E2: A reader of the release notes learns which command was undiscoverable from `--help`, that README already documented it, and that a check now watches for the same gap on any dispatcher command. Covered by: 2.1
