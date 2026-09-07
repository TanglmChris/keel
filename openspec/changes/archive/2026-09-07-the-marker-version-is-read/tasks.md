# Tasks

## 1. The two versions, side by side

- [x] 1.1 `keel --doctor` reads the `version=` attribute of the repository's `keel:start` marker and reports it beside the running CLI's version on every run, warning and naming the behind term and its remedy when they differ, reporting `not comparable` and naming the missing term when nothing is declared, and never changing the exit code
  - Covers:
    - keel-target-surface-diagnostics / Doctor reports protocol version drift
    - D1
    - D2
    - D3
    - D4
    - F1
    - F2
    - F3
  - Read:
    - bin/keel.js
    - plugins/keel/scripts/session-start.js
    - scripts/validate_plugin.py
    - openspec/changes/the-marker-version-is-read/design.md
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `the-marker-version-is-read` scenario in `scripts/validate_plugin.py` drives `keel --doctor` through the real CLI against a fixture repository whose `AGENTS.md` is written per case. A marker declaring a version older than the running CLI reports a warning naming both numbers, names the repository as behind, and names `keel --init`; a marker declaring a newer version reports a warning naming both numbers, names the install as behind, and names updating the Keel package; a marker declaring the running version reports `ok` and still prints both numbers; a repository with no `keel:start` marker, and one whose marker carries no `version=`, each report not comparable and name the missing term, and neither prints an `ok` verdict for the comparison. The exit code of the drifted run equals the exit code of the agreeing run, so drift changes no verdict.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario doctor-openspec-honesty` passes unchanged, so the OpenSpec version line this one is modelled on keeps its wording and its verdicts.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario doctor-reads-the-diagnosed-repository` passes unchanged, so the new line reads the repository under diagnosis and not the process's own working directory.
    - M4 (regression): `npm test` passes with no other scenario affected.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the comparison cannot be made without reading the installed plugin, because D1 states the report has two terms and a repository where the plugin is unreachable is the case this change exists for.
    - Stop if reporting drift changes doctor's exit code in any case, because D2 is the reason this line is safe to add.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:10c3fe79290163361253b619af540e7176ec61313bfab390152cef863409898f
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-marker-version-is-read` reports `the-marker-version-is-read scenario passed.` Run against fixture repositories by hand, the three shapes read: `protocol: warning - repo declares 5.14.0, this CLI is 5.47.0 — the repository is behind its install; run keel --init --target claude to bring the protocol forward`; `protocol: warning - repo declares 9.99.0, this CLI is 5.47.0 — the install is behind the repository, which carries a protocol this CLI cannot enforce; update the Keel package`; and `protocol: not comparable - this CLI is 5.47.0; the repository declares no protocol version in an AGENTS.md `keel:start` marker — run keel --init --target claude to write one`. In this repository the line reports `protocol: ok - repo declares 5.47.0, this CLI is 5.47.0`. The scenario asserts the behind run's exit code equals the agreeing run's, so drift reaches no verdict, and asserts the ahead direction is not told to re-run `keel --init` — the repair for the other direction.
    - M1.red: fail, for the right reason. The scenario was written and registered before `bin/keel.js` was changed, and reported `the-marker-version-is-read scenario: a repository declaring an older protocol did not warn; got ''.` — the empty string is the whole finding: doctor emitted no `protocol:` line at all, because nothing local read the attribute.
    - M1.green: pass. Same command after `printProtocolVersionDrift()` was added and called ahead of the `Project status:` block: `the-marker-version-is-read scenario passed.`
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario doctor-openspec-honesty` reports `doctor-openspec-honesty scenario passed.` The OpenSpec version line keeps its wording and both its verdicts; the new line is printed after it and shares no code with it.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario doctor-reads-the-diagnosed-repository` reports `doctor-reads-the-diagnosed-repository scenario passed.` The new reader takes the same `repo` argument every other doctor surface takes, so it reads the repository under diagnosis rather than the process's working directory.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 155 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — up from 154 by the one scenario this task added, with no other scenario affected.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that both versions are reported on every run, that a disagreement names the behind term and its remedy, that an undeclared version is not reported as agreement, and that none of it touches the exit code. M1 proves all four through the real CLI against fixture repositories written per case: the two directions are asserted separately and each is asserted *not* to carry the other's remedy, which is the check that matters — a line naming both numbers but the wrong repair reads as a failure and fixes nothing. The `not comparable` half is asserted for both ways of having no declaration, a missing marker and a marker with no attribute, because the second is the one that looks present. M1.red shows doctor emitting no such line at all.
      - Scope check: `git status --short` shows exactly the two Touch paths (`bin/keel.js`, `scripts/validate_plugin.py`) plus this change's own untracked directory, the record-write layer. `keel guard status` reports the fingerprint unchanged from task-start. No marker parser was changed: `printTargetSurface()`'s bootstrap regex and `install_to_repo.py`'s `MANAGED_START_RE` still match the marker with its attributes discarded, which is correct for what they ask — whether the block is present. The new reader is a second, separate regex that requires the attribute.
      - Findings: one, still open. The comparison has two terms, not the hook's three: doctor cannot read the installed plugin's version in a consumer repository, where the plugin lives outside the tree. So a session whose plugin is older than both the CLI and the repository still gets no local warning about *that* term, and the hook — the only reader of it — is exactly the component that would be too old to report it. D1 records why the two-term report is still the right one to ship, and it covers the four measured drift cases; the third term is genuinely uncovered. Durable owner: https://github.com/TanglmChris/keel/issues/112 — the same issue that owns the plugin-runtime verification gap this depends on, since a plugin version doctor could read would come from the same probe.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1 — the declared protocol version and the running version are reported side by side, on every run
    - E2 — a drifted repository is told which term is behind and what repairs that direction
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
    - README.md
    - keel/CHANGELOG.md
    - scripts/validate_plugin.py
    - openspec/specs/keel-target-surface-diagnostics/spec.md
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
    - M2: `README.md` no longer tells the reader that `keel --init` is run once, and says instead that it is what repairs the drift doctor reports
    - M3: `keel/CHANGELOG.md` carries an entry stating that the marker's version attribute had no local reader, that the only reader was a plugin hook whose activation doctor itself reports as unverified, and the four measured consumer versions
    - M4: the spec delta is promoted into `openspec/specs/keel-target-surface-diagnostics/spec.md`, `node node_modules/.bin/openspec validate the-marker-version-is-read --strict` passes, and `published-specs-validate-strictly` passes against the promoted store
    - M5: `npm test` passes with no failing scenario and no exception
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:9f1ae02af73282cf919555f985f00cb1243a9781185ec2bfe0d734095aa56b00
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` Every marker moved from 5.47.0 to 5.48.0 via `node scripts/bump_version.js minor` — the package and lockfile, both plugin manifests, the `keel:start` markers in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, and the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants in `scripts/validate_plugin.py`.
    - M2: pass. `README.md`'s day-to-day paragraph no longer says `keel --init` is run once. It now reads that you run `keel --doctor` to check the wiring and `keel --init` whenever doctor tells you the repository is behind its install, and states the reason the reader cannot infer — the protocol version lives in their `AGENTS.md`, and updating the package does not move it.
    - M3: pass. `keel/CHANGELOG.md` carries `## 5.48.0 - the marker version is read`. It states that the attribute had no local reader and quotes the regex both parsers share, that the one reader was a plugin hook whose activation doctor itself reports as `manual` — so a silent check and an agreeing check looked identical — and the four measured consumer versions with the 176 dead links the worst of them cost. It also records what stays uncovered: the third term the hook compares and doctor cannot.
    - M4: pass. The delta is promoted — `openspec/specs/keel-target-surface-diagnostics/spec.md` carries the `Doctor reports protocol version drift` requirement with its four scenarios, placed beside the OpenSpec-resolution requirement it is modelled on. `node node_modules/.bin/openspec validate the-marker-version-is-read --strict` reports `Change 'the-marker-version-is-read' is valid`, and `published-specs-validate-strictly` reports `22 published specs validate strictly against openspec 1.6.0.`
    - M5: pass. `npm test` reports `validation --all passed: baseline plus 155 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.` — unchanged from the count task 1.1 left, with no failing scenario and no exception.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker through the scenario that checks them all, and M4 asserts the promotion through both tools that consume the published store. M2 and M3 are the two prose checks. What M2 has to carry is not that a sentence changed but that the reader is told *why* re-running `keel --init` is a thing they will do — a README that merely dropped the word "once" would leave the same wrong model in place. What M3 has to carry is the reason the defect survived so long: not that a version went unread, but that the component reading it was one whose own activation was never verified, which is why nobody noticed.
      - Scope check: `git status --short` shows exactly this task's Touch entries — `package.json`, `package-lock.json`, both plugin manifests, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `README.md`, `keel/CHANGELOG.md`, `scripts/validate_plugin.py`'s version constants, the promoted `openspec/specs/keel-target-surface-diagnostics/spec.md`, and the twelve `.claude/`/`.codex/` marker files `bump_version.js` rewrites — plus `bin/keel.js` from task 1.1, already declared complete and untouched by this task, plus this change's own untracked directory, the record-write layer.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "you run two commands: `keel --init` once, and `keel --doctor` when you" — the day-to-day
  paragraph in `README.md`. Once doctor reports that the repository is behind its install, `keel --init`
  is exactly what the reader runs again, and "once" tells them not to.
  Updated by: 2.1
- I2: "that check lives in the plugin, so a plugin too old to contain it stays silent" — the Session
  Start section of `AGENTS.md` and of `assets/bootstrap/AGENTS.md`. A version comparison will also live
  in the CLI after this change.
  Discard reason: the sentence explains why the agent compares the two numbers *at session start*, and
  doctor is not a session-start surface. It stays true of the hook it is about, and naming doctor there
  would invite substituting a command nobody runs at session start for a duty that belongs to session
  start — the opposite of what the sentence exists to prevent.
- I3: "AGENTS.md carries the Keel managed bootstrap block" — the `bootstrap` line in
  `printTargetSurface()` in `bin/keel.js`. It stays accurate about the block; it is quoted here because
  it is the wording a reader searches for when asking what doctor knows about `AGENTS.md`, and after
  this change that answer has a second half.
  Discard reason: the line is not stale. D1 makes the version comparison a separate report with its own
  two terms rather than a second clause on the bootstrap line, precisely so that a reader asking whether
  the block is present and a reader asking which protocol it declares get two answers they can tell
  apart.

## Expectation Coverage

- E1: The declared protocol version and the running CLI version are reported side by side on every run, so a passing check is distinguishable from a check that did not run. Covered by: 1.1, 2.1
- E2: A disagreement names which term is behind and the remedy for that direction, and an absent or unreadable declaration is reported as not comparable rather than as agreement. Covered by: 1.1, 2.1
- E3: Reporting drift changes no exit code and no other doctor line. Covered by: 1.1
- E4: A repository that pins an older protocol deliberately now carries a standing warning. Discard reason: A1 records the basis — no such repository is known, and all four measured cases were unintentional — and https://github.com/TanglmChris/keel/issues/112 owns the suppression design if one appears.
