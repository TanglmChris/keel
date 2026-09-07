# Tasks

## 1. The declaration, and where it ends

- [x] 1.1 `declaredPath()` reads the path the value opens with — a leading backticked path, else the first bare run, and a backticked span elsewhere only when neither produced one — and a bare run ends at whitespace or at a CJK sentence terminator, while ASCII punctuation keeps its existing treatment and the alphabet stays unrestricted
  - Covers:
    - keel-core-gates / A declared path is extracted by where it ends, not by what it is made of
    - D1
    - D2
    - D3
    - D4
    - D5
    - A1
    - F1
    - F2
  - Read:
    - src/core/gates.js
    - scripts/validate_plugin.py
    - openspec/changes/a-path-is-what-the-value-declares/design.md
  - Touch:
    - src/core/gates.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-path-is-what-the-value-declares` scenario in `scripts/validate_plugin.py` drives `keel gate task-complete` and `keel gate task-start` through the real CLI against a fixture repository whose files are created for each case. The citation half: a `Durable owner:` naming an existing file and then quoting a second existing file in backticks resolves to the first, proven by deleting the first so the value is refused — and, through `## Invalidates`, the reader that names a missing path, so the refusal names the declared path and not the quoted one; restoring it passes again. The sentence half: `Durable owner: docs/owner.md。②接着说别的` resolves to `docs/owner.md`, and a path whose own segments are CJK words resolves in full. The forms that must not change: a value opening with a backticked path containing a space resolves to it; a value declaring no bare path but quoting one later still resolves to the quoted one; `AGENTS.md` and `./AGENTS.md` still resolve; `pending` and `5.44.0` stay unrecognized; a value whose only separator sits between two adjacent inline code spans (`` `networkx`/`PyYAML` ``) stays unrecognized rather than resolving to the bare separator; an ASCII path ending a sentence still resolves.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-root-file-is-a-path` passes unchanged, so the filename form added in 5.45.0 and its boundary are untouched.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario durable-owner-vocabulary` passes unchanged, so every accepted owner form keeps its verdict.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if ending the run at a terminator requires narrowing which characters a path may hold; #60's rule stands and this change adds boundaries, not an alphabet.
    - Stop if the ordering cannot be expressed inside `declaredPath()` and would need a second extractor for one reader.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3e580b81006794fd5853c723f88f943252eeaa747dcb80895b36aa6d9f869b46
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-path-is-what-the-value-declares` reports `a-path-is-what-the-value-declares scenario passed.` The citation half is proven by deletion rather than by both files existing: `Durable owner: docs/owner.md，判据见 \`docs/cited.md\`` passes with both present, fails once `docs/owner.md` is removed, and through `## Invalidates` — the reader that names a missing path — names `docs/owner.md` and not `docs/cited.md`; restoring the file passes again. The sentence half: `docs/owner.md。②接着说别的` and the CJK-comma form both resolve, and `docs/第一章/总论.md。后文` resolves in full, so terminators were added without narrowing the alphabet. Unchanged forms asserted: a leading backticked path containing a space, a backticked path with nothing declared before it, `AGENTS.md`, `./AGENTS.md`, and an ASCII path ending a sentence. Boundary asserted with the *absence* of a `does not exist` message: `pending`, `5.44.0`, and `首版只装 \`networkx\`/\`PyYAML\`` all stay unrecognized.
    - M1.red: fail, for the right reason, and on the half that fails silently. The scenario was written and registered before `src/core/gates.js` was touched, and reported `with the declared owner deleted the value still passed, so the gate checked the cited file instead` — the pre-change extractor resolved the backticked citation, so a finding was owned by a file the author never named.
    - M1.green: pass. Same command after `declaredPath()` was reordered to read the leading backticked path, then the first bare run bounded by `PATH_TERMINATORS`, then a backticked span elsewhere, with `backtickedPath()` refusing a capture whose segments are all empty.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-root-file-is-a-path` reports `a-root-file-is-a-path scenario passed.` unchanged — the filename form and its `pending`/`5.44.0` boundary are untouched by the reordering.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario durable-owner-vocabulary` reports `durable-owner-vocabulary scenario passed.` unchanged, so every accepted owner form keeps its verdict; `an-owner-outlives-the-change` also passes unchanged, so the transient verdict still runs before existence.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 154 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.`
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that the extractor returns the path the value declared, and that a bare run ends where the sentence does. M1 proves both through the real CLI, and the citation half is proven the only way that distinguishes it: by deleting the declared file, because while both files exist a wrong answer and a right one are indistinguishable from the verdict. The corpus that found the defect is also the acceptance evidence — re-running the fixed extractor over the same 624 consumer declarations takes the mis-extractions from 15 to 2, and the 2 that remain are values that declare no path at all.
      - Scope check: `git status --short` shows exactly the two Touch paths (`src/core/gates.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel gate task-start` reports the fingerprint unchanged from the anchor recorded before the last implementation step.
      - Findings: two. First, fixed in this task: the first draft asserted that the `Findings` refusal names the declared path, and it does not — `findingOwnerIsDurable()` returns a boolean and that reader reports one generic owner refusal, exactly as 5.45.0 recorded. The naming half moved to `## Invalidates`; the `Findings` half keeps the pass/fail assertion, which is what actually distinguishes the two answers. Resolved here: M1 Second, still open: two consumer declarations remain mis-extracted because the value declares no path and its prose contains a separator — `协议/端口标注`, `(M2/M3)`. Telling a CJK word pair from a two-segment path needs semantics the gate does not have, so it is left rather than guessed at; design.md A2 records the measurement. Durable owner: https://github.com/TanglmChris/keel/issues/113 — the issue this change closes carries both remaining instances and the reason they are not fixed here.
    - Blocker: none
    - Reauthorizations: the contract was re-recorded twice, both before completion. Once to move M1's naming assertion off `Findings`, which reports one refusal for every unusable owner, onto `## Invalidates`, which names the path. Once to add D5 and the degenerate-separator assertion after the post-change corpus re-measurement showed two values resolving to the bare string `/` — a shape produced by the fallback branch this task retained, so it belongs to this task rather than to a later one. `sha256:101eb64b10…` → `sha256:c8fc8a6f9e…` → `sha256:3e580b8100…`.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — the extractor returns the path the value declared, in prose that cites other files
    - E2 — a bare run ends where the sentence does, in a script that supplies no whitespace
    - I1 — the published wording this change makes stale
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
    - openspec/specs/keel-core-gates/spec.md
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
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker names the new release version
    - M2: `keel/CHANGELOG.md` carries an entry naming both shapes with the 34-of-624 measurement, saying which half refuses and which half silently accepts, and recording that both are upgrade-surfaced because the repositories carrying them predate the whitespace-run rule, closing issue #113
    - M3: the spec delta is promoted into `openspec/specs/keel-core-gates/spec.md`, `node node_modules/.bin/openspec validate a-path-is-what-the-value-declares --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M4: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9453f302266550805fb8b87234f3d005e2a354e039c2dec8548e9c17671ebe19
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.46.0 to 5.47.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.47.0 - a path is what the value declares`, naming both shapes with the 34-of-624 measurement and the 15-to-2 result of re-running the fixed extractor over the same corpus. It states which half refuses and which half silently accepts — the distinction that makes the second one worse — records the degenerate separator found by the re-measurement, and says both are upgrade-surfaced because the repositories carrying them predate the whitespace-run rule. It also records what stays unfixed and why. Closes issue #113.
    - M3: pass. The delta is promoted — `openspec/specs/keel-core-gates/spec.md` carries the reworded path-extraction requirement with its two new scenarios and the widened backtick scenario. `node node_modules/.bin/openspec validate a-path-is-what-the-value-declares --strict` reports `Change 'a-path-is-what-the-value-declares' is valid`, and `published-specs-validate-strictly` reports `22 published specs validate strictly against openspec 1.6.0`.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 154 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 153 by the one scenario this change added.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all. M3 asserts the promotion through the two tools that consume the published store. M2 is the one prose check, and what it has to carry here is the asymmetry between the two halves: a reader who takes "the extractor was too greedy" from the entry would not learn that one half was passing on a file nobody declared, which is the part that changes how much old evidence can be trusted.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-core-gates/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `src/core/gates.js` from task 1.1, already declared complete and unrelated to this task's own writes, plus this change's own untracked directory, the record-write layer.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "by locating a run of non-whitespace" — the "A declared path is extracted by where it ends, not by
  what it is made of" requirement in `openspec/specs/keel-core-gates/spec.md`. Whitespace is the whole
  boundary it states, and in a script that separates no words with whitespace it bounds nothing.
  Updated by: 2.1
- I2: "Keel MUST accept a path wrapped in backticks and take it verbatim" — the same requirement. It says
  nothing about which of several backticked spans in one value is the declaration, and the implementation
  took the first one anywhere. Updated by: 2.1
- I3: "A declared path is a run of non-whitespace. What ends a path is whitespace" — the comment above
  `declaredPath()` in `src/core/gates.js`, which states the rule beside the code. Updated by: 1.1
- I4: "The backtick form wins when present." — the same comment, describing the ordering this change
  narrows to a leading span. Updated by: 1.1

## Expectation Coverage

- E1: A value that names a path and then quotes another resolves to the one it opened with, and a value that quotes a path while declaring none still resolves to the quoted one. Covered by: 1.1, 2.1
- E2: A bare run ends at a CJK sentence terminator as well as at whitespace, while a path whose segments are CJK words still extracts in full and ASCII paths are unaffected. Covered by: 1.1, 2.1
- E3: Every form accepted today keeps its verdict — the backticked whitespace path, the repository-root filename, the unrecognized non-path, the trailing-punctuation trim, and the missing-path refusal. Covered by: 1.1
- E4: A terminator an author writes that is outside the declared set. Discard reason: such a declaration extracts exactly as it does today, which is the current behaviour rather than a new failure; A1 records the set's basis and https://github.com/TanglmChris/keel/issues/113 owns any instance found later.
