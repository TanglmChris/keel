<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Stop the silent compact-to-v3 downgrade

- [x] 1.1 Report a non-concrete Verify as its own diagnostic instead of switching required-field sets
  - Covers:
    - D1 a non-concrete Verify produces its own diagnostic and does not silently select the v3 field set
    - keel-task-capsule / Expanded v3 tasks normalize through the same compiler / Non-concrete Verify is reported, not silently downgraded
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md
  - Verify:
    - Strategy: regression-first
    - M1: a compact v4 task whose Verify carries an unfilled template token reports one diagnostic naming that token and stating that compact detection needs a concrete Verify, and no longer reports the expanded v3 fields Candidate Boundary, Report, Owner, Mode, Commands, Acceptance, or Stop Rules as missing; a new validator scenario locks both the presence of the naming diagnostic and the absence of the v3 field list
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:2821a5738b02891abc97c18e7a10ccc169573dff67c0eceab05868807d7e584c
    - M1: requiredFieldProblems now returns a single non-concrete-verify diagnostic when Verify is declared but carries an unfilled token, naming the matched token and stating that the expanded v3 fields are not required. unfilledToken was extracted alongside isConcrete over a shared normalizeFieldText and UNFILLED_TOKEN, so the concreteness rule has one definition. A task with no Verify at all still receives the expanded v3 required-field diagnostics, verified by the second half of the new scenario
    - M1.red: with src/core/task-contract.js stashed, the reported case (Verify prose containing an angle-bracket filename pattern) produced 10 problems — 8 missing-field entries for Owner, Mode, Read, Commands, Acceptance, Candidate Boundary, Stop Rules, Report, plus missing-boundary and missing-command-check — and named the offending token nowhere. The new non-concrete-verify-diagnostic scenario exited 1 with "an unfilled token in Verify did not produce the non-concrete-verify diagnostic"
    - M1.green: the same case now produces 2 problems, the first quoting the matched angle-bracket date token back to the author and stating that compact v4 detection requires a concrete Verify; the scenario exited 0 and npm test reported "validation --all passed: baseline plus 59 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — the author is told which token caused the failure and is no longer handed a field list from the other schema, satisfying D1
      - Scope check: pass — only src/core/task-contract.js and scripts/validate_plugin.py changed, both within Touch
      - Findings: the defect is wider than issue #7 reported. the token pattern also matches three bare keywords case-insensitively, so prose describing them trips it. This change hit that three times while being authored: task 1.1's own Verify, a Covers reference whose target scenario name used one keyword, and this Evidence block itself, which cannot quote the tokens it describes. Recorded as F6 in this change's design.md; task 1.2 narrows the angle-bracket case, and whether the bare keywords should also be narrowed is deferred. Durable owner: keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md
    - Blocker: none

- [x] 1.2 Treat token forms inside inline code spans as concrete prose
  - Covers:
    - D2 angle brackets inside inline code spans are concrete prose
    - keel-task-capsule / Expanded v3 tasks normalize through the same compiler / Documented patterns in inline code are concrete
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
    - keel/archive/follow-ups/2026-07-27-unfilled-token-keywords.md
  - Verify:
    - Strategy: regression-first
    - M1: a field whose token forms appear only inside inline code spans compiles as filled, the same form outside inline code is still judged unfilled, a field whose whole value is one inline code span is not judged empty, and the existing fingerprint-stability scenarios still pass unchanged; a new validator scenario locks all three cases together
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:97266399531b8d8de2cb2fac3e0f4d4bfd558a52cf768ef7005ffee01258cfde
    - M1: `withoutInlineCode` strips backtick-delimited spans and is applied inside both `isConcrete` and `unfilledToken`, after the empty/none/pending test so a field whose whole value is one span is not read as empty. The exemption covers all four token forms per the widened D2, not only angle brackets. This Evidence line is itself the demonstration: it quotes `<date>`, `TODO`, and `TBD` inside code spans and the gate accepts it, which it refused to do on task 1.1
    - M1.red: with only the `src/core/task-contract.js` change stashed against post-1.1 HEAD, the new `inline-code-is-concrete` scenario exited 1 with "token forms inside inline code spans were still judged unfilled"
    - M1.green: the scenario exits 0, asserting all three cases — fenced tokens accepted, the same token bare still reported as `non-concrete-verify`, and a whole-value code span not judged empty. Issue #7's original reproduction (a filename pattern written inside backticks) now returns `status: pass` with **0 problems**, against 10 before task 1.1 and 2 after it. `npm test` reported "validation --all passed: baseline plus 60 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — documented patterns and prose naming the token forms are writable in task fields, while a token left bare is still reported, satisfying the widened D2
      - Scope check: pass — `src/core/task-contract.js`, `scripts/validate_plugin.py`, and the archive note, all within Touch
      - Findings: task 1.1's `non-concrete-verify-diagnostic` scenario fixture had written its token inside backticks, so this task correctly made it stop firing; the fixture was moved to a bare token, which is what that scenario must exercise now. E6 verified directly: task 1.1's recorded fingerprint `sha256:2821a573...` recomputes unchanged after this task, so no existing valid task shifts. Durable owner for the residual false-negative, an unfilled slot deliberately written inside backticks: openspec/changes/diagnostics-must-not-mislead/design.md risk A1, accepted with the mitigation that Touch-path checks still reject a path that does not exist
    - Blocker: none

## 2. Make Covers and authority diagnostics name their cause

- [x] 2.1 Name a separator collision, and stop over-segmented capability refs from degrading silently
  - Covers:
    - D6 a reference whose first segment names an existing capability is always treated as a spec reference
    - keel-task-capsule / Covers resolves durable authority and Acceptance / Separator collision is named
    - keel-task-capsule / Covers resolves durable authority and Acceptance / Over-segmented capability reference does not degrade silently
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: both spellings of a reference to a requirement whose name contains the separator now fail loudly and name the cause — the over-segmented spelling no longer compiles to an unlinked legacy-task-reference, and the trimmed spelling's diagnostic states that a requirement name in that capability contains the separator; an ordinary unresolved reference keeps its existing wording, and a free-text reference whose first segment names no capability is still accepted; a new validator scenario locks all four cases
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6376ae8ccb56ea2d8587ab4114de086c0be22e453d00754019244c42662e3293
    - M1: `specAuthority` no longer returns null for an over-segmented reference whose first segment names a capability with an existing spec file; it reports `unresolved-covers` naming the segment count and the accepted hierarchy. A shared `collisionHint` scans the target capability for requirement and scenario headings whose own title contains the separator and appends them by name, and is applied to the over-segmented path, the missing-scenario path, and the unresolved-reference path
    - M1.red: with `src/core/task-contract.js` stashed, the new `covers-separator-collision` scenario exited 1 with "an over-segmented reference to a real capability still degraded to a free-text reference"
    - M1.green: the scenario exits 0, asserting four cases — the reporter's kept-slash spelling now fails instead of compiling to an unlinked reference and names the colliding requirement; the trimmed spelling gains the same naming; a capability with no colliding name keeps the plain wording; and free text merely containing slashes is still accepted as a legacy reference. `npm test` reported "validation --all passed: baseline plus 61 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — both spellings the reporter tried now fail loudly and name the cause, satisfying D6 and the two covered scenarios
      - Scope check: pass — `src/core/task-contract.js` and `scripts/validate_plugin.py`, both within Touch
      - Findings: the silent half of this defect was worse than the reported half and was outside this task's original scope. The reporter's *correct* spelling compiled to an unlinked `legacy-task-reference` with `status: pass` and empty Acceptance, so the task as first written would not have fixed their case. Scope was widened before implementing, because delivering the narrow version would have closed issue #7 example 2 without fixing it. Durable owner: openspec/changes/diagnostics-must-not-mislead/design.md, which records the reproduction as F7 and the decision as D6, with a matching spec scenario
    - Blocker: none

- [x] 2.2 State the exact field and line prefix in the unresolved-authority diagnostic
  - Covers:
    - keel-task-capsule / Task modes and conditional fields are executable / Authority diagnostic names the field to add
  - Touch:
    - src/core/task-contract.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: a task whose Covers references an unresolved Q reference without an authorized fallback reports a diagnostic naming the Autonomy boundary field and the Pre-authorized fallback line prefix, and no longer describes the requirement only as documented design authority; a new validator scenario locks the diagnostic text
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:6b0af80d560f6e3cdcf736f8a81811b502416524aa4191fb534049bd9f9b38a6
    - M1: the `unresolved-authority` message now names the task id, the `Autonomy boundary:` field, and the `Pre-authorized fallback:` line prefix, states that the line must carry the reversible bound plus its required evidence, and says explicitly that this check reads only that line on the task and that prose in design.md does not satisfy it. The phrase "documented design authority", which sent authors to design.md, is gone
    - M1.red: with `src/core/task-contract.js` stashed, the new `unresolved-authority-names-field` scenario exited 1 — "the diagnostic omitted Autonomy boundary:, Pre-authorized fallback:, design.md" — against the old text "Q1 requires documented design authority and an authorized fallback before implementation."
    - M1.green: the scenario exits 0. It reproduces the reporter's exact state, a design.md that already documents Q1 and its authorized fallback in prose, asserts the new message names all three needles and no longer says "documented design authority", and then asserts that doing literally what the message asks clears the gate. `npm test` reported "validation --all passed: baseline plus 62 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — the diagnostic names the field and prefix it actually reads, and following it resolves the failure, satisfying the covered scenario
      - Scope check: pass — `src/core/task-contract.js` and `scripts/validate_plugin.py`, both within Touch
      - Findings: none
    - Blocker: none

## 3. Separate Keel's own repository from a consuming project

- [x] 3.1 Add the Keel-source-repository predicate and scope the dev-only doctor check to it
  - Covers:
    - D3 one exported predicate answers whether this is Keel's own repository
    - D4 a consumer repository omits the native plugin source line
    - keel-target-surface-diagnostics / Native plugin diagnostics are behavior-probed / Development-only source check is scoped to Keel's own repository
  - Touch:
    - src/core/capabilities.js
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: doctor run in a temporary consumer repository prints no native plugin source line and no remediation directing the author to install an already-installed plugin, while doctor run in this repository still prints the line as ok; a new validator scenario asserts both directions
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f14d9b5f71f24c836239cf002aa41354422fec1c84dc064b6a21b1b9c4c93763
    - M1: `isKeelSourceRepo` is exported from `src/core/capabilities.js` and requires both signals from D3 — `package.json` name equal to the Keel package, and an existing `plugins/keel/` directory. Three surfaces now consult it: `pluginObservation` omits the source clause outside Keel's repository, doctor omits the `native plugin source` line entirely, and the `Keel behavioral skills` remediation stops saying "install the plugin if it is missing" and instead directs the reader to the runtime's own plugin listing, since Keel cannot observe installation from the repository
    - M1.red: with `src/core/capabilities.js` and `bin/keel.js` stashed, the new `dev-only-plugin-source-scoping` scenario exited 1 with "a consuming project was still shown the development-only plugin source check"
    - M1.green: the scenario exits 0, asserting a consumer project built by `keel --init` shows neither the source line, nor the install-if-missing remediation, nor any leaked plugin source clause in its capability lines, while this repository still reports `native plugin source: ok`. Verified by hand in both directions: the consumer capability line now begins with the runtime-evidence clause, and this repository's still carries `plugin source valid ... (version 5.2.2)`. `npm test` reported "validation --all passed: baseline plus 63 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — a consuming project is shown neither a permanently unactionable `missing` nor a remediation it has already performed, while the check keeps working where it means something, satisfying D3 and D4
      - Scope check: pass — `src/core/capabilities.js`, `bin/keel.js`, and `scripts/validate_plugin.py`, all within Touch
      - Findings: the existing `thin-native-install` scenario asserted the reported defect as a requirement. Its Case E required a consuming temp repository to report `native plugin source`, and a bare repository to report `plugin source absent` — so the suite was locking issue #6 in rather than catching it. Case E now asserts the opposite for the source line while keeping its runtime-line and install-remediation assertions, with a comment recording why. Durable owner: openspec/changes/diagnostics-must-not-mislead/design.md decision D4
    - Blocker: none

- [ ] 3.2 Skip the AGENTS.md bootstrap write inside Keel's own repository
  - Covers:
    - D5 install and init skip the bootstrap write in Keel's own repository and report the skip
    - keel-target-surface-diagnostics / Keel install does not damage its own source repository / Install skips the bootstrap write in Keel's own repository
    - keel-target-surface-diagnostics / Keel install does not damage its own source repository / Install still writes the bootstrap in a consuming project
  - Touch:
    - scripts/install_to_repo.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: keel --install --target claude run in this repository leaves the AGENTS.md managed block byte-identical and prints a skip line naming the reason, while the same command in a temporary consumer repository still writes the bootstrap block from the asset; a new validator scenario locks both directions, and the full suite passes, proving the four scenarios that assert on managed-block protocol text stay green
  - Evidence:
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Expectation Coverage

- E1: an author writing a first compact v4 tasks.md is never handed a v3 field list they did not ask for Covered by: 1.1, 1.2
- E2: a diagnostic that requires the author to add a field names that field and its exact prefix Covered by: 2.2
- E3: a diagnostic that cannot resolve a reference names the reason when the reason is structural Covered by: 2.1
- E4: a consuming project is never shown a check it cannot satisfy or a remediation it has already done Covered by: 3.1
- E5: running keel --install inside Keel's own repository does not turn the repository red Covered by: 3.2
- E6: no existing valid task changes its compiled fingerprint Covered by: 1.2
