# Tasks

## 1. Say what is wrong, and only that

- [x] 1.1 Name the token in a required field, and derive nothing from the other schema
  - Covers:
    - keel-task-capsule / A non-concrete required field names the token that made it non-concrete / An unfilled slot in a required field is named
    - keel-task-capsule / A non-concrete required field names the token that made it non-concrete / An empty required field keeps the unqualified diagnostic
    - keel-task-capsule / A non-concrete required field names the token that made it non-concrete / A prose token is reported rather than tolerated
    - keel-core-gates / A gate whose contract failed to compile derives no problem from a schema fallback / An unusable contract reports its diagnostics alone
    - keel-core-gates / A gate whose contract failed to compile derives no problem from a schema fallback / Suppression does not turn a refusal into a pass
    - keel-core-gates / A gate whose contract failed to compile derives no problem from a schema fallback / A task declaring no verification form is still refused, naming the compact field
    - D1 — a non-concrete required field names its token and offers the inline-code escape
    - D2 — no verification-form problem is derived when the contract did not compile
    - D3 — the token pattern is deliberately not widened
    - D4 — the diagnostic codes are unchanged
    - D5 — verification runs through the gate, not through the two functions
    - F1 — the reproduced pair of problems and their order
    - F2 — the unbounded angle-bracket match and the span it captures
    - F3 — `unfilledToken()` exists for this and is not called here
    - F4 — the same file already does this one function away
    - F5 — an unusable contract always has a diagnostic already recorded
    - F6 — the recorded decision that a bare token in prose stays reported
    - A1 — the author is left to judge slot versus literal text
    - A2 — nothing outside this repository keys on the derived problem
  - Touch:
    - src/core/task-contract.js
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario unusable-contract-names-only-its-cause` passes. The scenario builds a repository holding a compact task whose `Evidence` carries a bare angle-bracket span in prose, records its contract anchor, then drives `keel gate task-complete` and asserts: no reported problem states that `Commands` must define at least one check; the `Evidence` problem names the matched span and offers the inline-code escape; the gate still returns `fail`; a field left empty rather than token-carrying keeps the unqualified wording; and a task declaring neither `Verify` nor `Commands` is still refused, with the refusal naming `Verify` rather than `Commands`.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario non-concrete-verify-diagnostic` still passes, so the sibling diagnostic this one is modelled on is unchanged.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario inline-code-is-concrete` still passes — D3 in executable form, since that scenario is where the decision recorded in F6 lives.
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates` still passes.
    - M5 (regression): `npm test` passes with no failing scenario and no exception.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if making the named token legible requires changing which fields the gate accepts.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:46554f7f03b3617e97cea8f243b048a246dd623270d47bf7076f89f48817b066
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario unusable-contract-names-only-its-cause` reports `unusable-contract-names-only-its-cause scenario passed.` Six assertions through `keel gate task-complete` on real repositories: the derived verification-form problem is absent, the remaining diagnostic names the matched span and the inline-code escape, the gate still returns `fail`, fencing exactly what the message names records an anchor, an empty required field keeps the unqualified wording, and a task declaring no verification form is still refused naming `Verify`.
    - M1.red: fail, as required, before either edit. The scenario reported `an unusable contract still derived a verification-form problem from the other schema's field.` beside the gate's actual output, `Commands must define at least one M<n>.` — issue #52's reported message verbatim, produced through the gate rather than quoted from the issue. The same fixture at 5.19.0 returned that problem first and `Evidence must be concrete.` second, with neither naming an angle bracket.
    - M1.green: pass. All six assertions hold. The one that matters most is the third: naming the cause and dropping the derived problem did not make the gate pass — it still returns `fail` on the compiler's own diagnostic, which is the only direction in which suppressing a problem could have done harm. The reported case now returns a single diagnostic reading ``Evidence carries the unfilled slot `<0.02），最小照亮比例 0.998107（判据 >`, so it is not concrete.`` — the captured span is the reporter's own text, and its visible length is what shows the match was accidental.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario non-concrete-verify-diagnostic` reports `non-concrete-verify-diagnostic scenario passed.` The sibling diagnostic this one is modelled on is unchanged, including its assertion that expanded v3 fields do not leak.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario inline-code-is-concrete` reports `inline-code-is-concrete scenario passed.` This is D3 in executable form: a bare token in prose is still judged unfilled and a fenced one is still concrete, so what the gate accepts is byte-identical to 5.19.0.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario core-gates` reports `core-gates scenario passed.`
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 129 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: every assertion runs through `keel gate task-complete` on a real repository, not against the two edited functions directly. That is D5, and it is the point: #52's cost came from the *pair* of messages and their order, which only the gate produces. The red half reproduces the reported message verbatim from the unfixed tree.
      - Scope check: `git status --short` lists exactly `scripts/validate_plugin.py`, `src/core/gates.js`, and `src/core/task-contract.js` — the three Touch entries — plus this change's own untracked directory. No file was written by shell redirection; every edit went through the tools the write guard can see.
      - Findings: one. The gate refuses a task whose Evidence carries a token, but this task's own Evidence has to quote the token forms to describe them — the wall recorded in `keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md`. Every quotation here is fenced, which is the recorded escape working as designed, and the new message now names that escape explicitly where it previously did not. Resolved here: M1
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## 2. Close

- [x] 2.1 Release 5.20.0
  - Covers:
    - E6 — a reader of the release notes learns which message changed, and that what the gate accepts did not
    - I1, I3 — the wordings this change makes stale
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
    - openspec/specs/keel-task-capsule/spec.md
    - openspec/specs/keel-core-gates/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names 5.20.0
    - M2: `keel/CHANGELOG.md` carries a 5.20.0 entry naming the reported pair of problems, stating that the token pattern was deliberately not widened and where that decision is recorded, and pointing at the backtick form as the escape
    - M3: both spec deltas are promoted into `openspec/specs/`, `node bin/keel.js openspec validate a-field-the-schema-does-not-have --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:d5d1ce99d19a9b98eb2af7d3e9afa3dfa2c84d97927a5691acf8737c608f875b
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Twenty markers moved from 5.19.0 to 5.20.0 via `node scripts/bump_version.js 5.20.0` — the package and lockfile, both plugin manifests, the three `keel:start` blocks, the twelve `keel:openspec-surface-overlay` markers, the AGENTS.md title and preflight line, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.20.0 - a field the schema does not have`, naming both reported problems and why the first was an artifact of the fallback, stating that what the gate accepts is unchanged, and recording that the token-pattern narrowing is deliberately absent — with the reason, the location of the decision it would reverse (`keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md`), and where it is left open. The backtick form is named as the escape in the entry and in the new message itself.
    - M3: pass. Both deltas are promoted — `A non-concrete required field names the token that made it non-concrete` into `openspec/specs/keel-task-capsule/spec.md` beside the check requirement it generalizes, and `A gate whose contract failed to compile derives no problem from a schema fallback` into `openspec/specs/keel-core-gates/spec.md`. `node bin/keel.js openspec validate a-field-the-schema-does-not-have --strict` reports the change valid, and `published-specs-validate-strictly` reports `21 published specs validate strictly against openspec 1.6.0` against the store now holding both.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 129 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: each release claim is checked by running the thing it describes rather than by inspection — the marker count by `version-alignment`, the promotion by `openspec validate --strict` and then by `published-specs-validate-strictly`, which is the store-validation check 5.17.0 added and which now covers the two requirements this release publishes.
      - Scope check: `git status --short` lists 2.1's Touch entries plus `src/core/gates.js` and `src/core/task-contract.js`, which belong to completed sibling task 1.1 and were not written during this task. No path outside the union of the two tasks' Touch sets. The version markers were written by `scripts/bump_version.js`, the repository's own release tool; because a script's writes are invisible to the PreToolUse guard, every file it touched was declared in Touch beforehand and the resulting worktree was compared against that list here rather than assumed.
      - Findings: none
    - Blocker: none
  - Stop if:
    - Requires files outside Touch.

## Invalidates

- I1: "version=5.19.0" — grep it and you find the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, plus the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`; the same version is written as `"version": "5.19.0"` in `package.json`, `package-lock.json`, and both plugin manifests, in the AGENTS.md title and its preflight line, and in the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants of `scripts/validate_plugin.py`. Updated by: 2.1
- I2: "must be concrete" used as a message *prefix* — `scripts/validate_plugin.py:4918` and `:7743` both assert leakage with `message.startswith(f"{name} must be concrete")`. After D1 a field carrying a token no longer starts with that phrase. Discard reason: both assertions are negative checks over fields that are genuinely absent in their fixtures, and D1 keeps the unqualified wording for exactly that case, so each remains true of what it tests. Rewriting them would weaken a check that currently passes for the right reason.
- I3: "A non-concrete check names the token that made it non-concrete" — the requirement heading in `openspec/specs/keel-task-capsule/spec.md`, and the sentence under it beginning "Keel MUST name the matched unfilled-slot token when a `M<n>` check is judged non-concrete". Read today it says the rule is about checks; after this change the same rule governs the required fields validated beside them, and a reader searching for why a field named its token would not find it there. Updated by: 2.1

## Expectation Coverage

- E1: A required field refused for a token names the span that caused it, so the author does not bisect the field to find it. Covered by: 1.1
- E2: No reported problem names a field belonging to a schema the author did not declare. Covered by: 1.1
- E3: Suppressing the derived problem does not let a refused task pass. Covered by: 1.1
- E4: What the gate accepts is unchanged — a bare token in prose is still refused. Covered by: 1.1
- E5: Whether the token pattern should stop matching prose stays with the owner. Durable owner: https://github.com/TanglmChris/keel/issues/52
- E6: A reader of the release notes learns which message changed and that acceptance did not. Covered by: 2.1
