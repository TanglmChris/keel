## 1. Answer about the repository you named

- [x] 1.1 Read the OpenSpec declaration from the diagnosed repository and say whose it is
  - Covers:
    - keel-target-surface-diagnostics / The interpreter and the OpenSpec binary that run are checked against what is required / The declared version is read from the diagnosed repository
    - keel-target-surface-diagnostics / The interpreter and the OpenSpec binary that run are checked against what is required / A repository declaring no OpenSpec version is reported as declaring none
    - keel-target-surface-diagnostics / The interpreter and the OpenSpec binary that run are checked against what is required / The reporting is exercised from outside Keel's own checkout
    - D1 — the read is rooted at the diagnosed repository with no fallback to Keel's install location
    - D3 — the pin is attributed in the output rather than left for the reader to assign
    - D4 — absence produces no warning
    - D5 — the scenario simulates a differing root rather than a differing installation method
    - F1 — the measured misattribution this task removes
    - F4 — `lockedOpenSpecVersion()` has one caller, so rerooting it reaches no other surface
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario doctor-reads-the-diagnosed-repository` passes. The scenario builds a repository whose `package-lock.json` declares an OpenSpec version no installed binary reports, runs `keel --doctor` from it, and asserts the `openspec:` line names that declared version and attributes it to the repository; it then builds a repository declaring none and asserts the line says the repository declares none, carries no warning arising from the absence, and does not report the absence as a failure to read.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario runtime-versions-are-checked` still passes, so Keel's own checkout — where the two roots coincide — keeps reporting the disagreement it reported before.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario source-repo-cli-resolution` still passes, so the consumer-facing resolution hint is unchanged.
    - M4 (regression): `node bin/keel.js openspec --version` reports the same version from Keel's checkout and from a repository declaring a different one, proving D2 — which binary answers is not affected by what a repository declares.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:46a5203f499dcf51d8a44b497d648d3f3b2b49388a42163cf50ebb3a24c7b2d6
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario doctor-reads-the-diagnosed-repository` reports `doctor-reads-the-diagnosed-repository scenario passed.` The scenario drives `keel --doctor` at two temporary repositories: one declaring `0.0.1`, which no OpenSpec release reports, and one declaring nothing at all.
    - M1.red: fail, as required, and re-proved after every assertion change. Against the original implementation, restored from the index, the scenario reports `the openspec line does not attribute any declared version to the repository, so a reader seeing two versions cannot tell which one is theirs.` beside the actual line `openspec: ok - .../node_modules/.bin/openspec (1.6.0, lockfile 1.6.0)` — both numbers read from Keel's own checkout. The second branch of that assertion was proved live by a separate mutant that keeps the attribution but roots it at `PACKAGE_ROOT`: it emits `(1.6.0, repo pins 1.6.0)` and the scenario reports `attributes a declared version to the repository, but not 0.0.1, which is what this repository declares.` Neither branch is dead, and each names only the failure that actually occurred.
    - M1.green: pass. With `declaredOpenSpecVersion(repo)` in place the same repository reports `openspec: warning - .../node_modules/.bin/openspec (1.6.0, repo pins 0.0.1) — validation is answering from a different build than this repository pins…`, and the repository declaring nothing reports `repo declares no OpenSpec version` with no disagreement clause and no `unreadable`. The scratch repository from the original report, which pins `9.9.9`, now reads `(1.6.0, repo pins 9.9.9)` where it previously read `(1.6.0, lockfile 1.6.0)`.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario runtime-versions-are-checked` reports `runtime-versions-are-checked scenario passed.` Keel's own checkout, where the two roots coincide, keeps reporting what it reported before; the scenario asserts the version number appears in the line rather than the surrounding words, so the wording change from `lockfile 1.6.0` to `repo pins 1.6.0` does not move it.
    - M3: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario source-repo-cli-resolution` reports `source-repo-cli-resolution scenario passed.`, and `doctor-openspec-honesty` — the other scenario reading this line — also passes. Resolution and the consumer-facing hint are untouched.
    - M4: pass. `node bin/keel.js openspec --version` reports `1.6.0` both from Keel's checkout and from a repository declaring `9.9.9`, so what a repository declares does not change which binary answers. D2 holds: the declaration is reported, never acted on.
    - Review:
      - Status: pass
      - Acceptance check: each check runs the public surface — `keel --doctor` and `keel openspec` — against a repository whose identity differs from Keel's install location, which is the distinction the Acceptance is about. The behavior is asserted by reading the emitted line, not by inspecting the function that produces it, and the red half was proved against the real prior implementation rather than a simulated one. M4 is the check for a non-goal, and it is a real observation rather than a restatement: it compares the answering binary across the same two roots that M1 separates.
      - Scope check: `git status --short` lists exactly `bin/keel.js` and `scripts/validate_plugin.py`, the two Touch entries, plus this change's own untracked directory, which is the record-write layer. `grep` confirms no caller of the removed `lockedOpenSpecVersion` remains. `openspecCandidates()` and `findOpenSpecCommand()` were not edited, so `keel openspec` at `bin/keel.js:896` and `:1755` resolve exactly as before.
      - Findings: four. First, found by this checklist inside this task's own new code: one condition guarded two distinct failures. A single assertion reported that the line was "answering about some other repository, or it leaves the reader to infer which of the two versions is theirs" — but a line carrying the right version with no attribution is not answering about another repository, so half of every reader would have been sent somewhere with no problem in it. It is split into two conditions with one cause each, and both branches were proved live: the unattributed branch against the original implementation, the misattributed branch against a mutant that keeps the attribution and roots it at `PACKAGE_ROOT`. This is the same defect class the change is about — a message that names something other than what happened — reproduced by me while fixing it, which is worth recording rather than quietly correcting. Resolved here: M1. Second: the `Covers` diagnostic cost two authorization cycles. `Covers reference could not be resolved: <ref>.` is emitted for a reference whose capability resolves and whose segments do not, and it never says that the second segment is the Requirement name and the third the Scenario — so a reference naming a real scenario in the second position is reported identically to one naming nothing at all. This is the shape #49 already describes for `Covers` (present but unparsed reported as absent), reached by a different route. Durable owner: https://github.com/TanglmChris/keel/issues/49. Third: the scenario's first assertion form was too strict — it rejected any occurrence of Keel's own declared version in the line, which also rejects the correct output whenever the answering binary happens to report that same number. It was replaced with an assertion on the declared position, and re-proved red against the original implementation so the correction could not be a weakening. Resolved here: M1. Fourth: two observations about other open issues were confirmed in passing and belong to them rather than here — `keel gate task-start --record` no longer causes guard drift in 5.14.0 (`guard status` reported `active` immediately after `--record`, against #53 item 1), and the mechanical scenario-name check proposed in #51 would false-positive on registry entries split across two lines, which `runtime-versions-are-checked` is. Durable owner: https://github.com/TanglmChris/keel/issues/53
    - Blocker: none

## 2. Close

- [x] 2.1 Release 5.15.0
  - Covers:
    - E5 — a reader of the release notes learns the openspec doctor line changed what it is a statement about
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
    - .claude/commands/opsx/explore.md
    - .claude/commands/opsx/sync.md
    - .claude/skills/openspec-apply-change/SKILL.md
    - .claude/skills/openspec-archive-change/SKILL.md
    - .claude/skills/openspec-propose/SKILL.md
    - .claude/skills/openspec-explore/SKILL.md
    - .claude/skills/openspec-sync-specs/SKILL.md
    - .codex/skills/openspec-apply-change/SKILL.md
    - .codex/skills/openspec-archive-change/SKILL.md
    - .codex/skills/openspec-propose/SKILL.md
    - .codex/skills/openspec-sync-specs/SKILL.md
    - openspec/specs/keel-target-surface-diagnostics/spec.md
  - Verify:
    - Strategy: evidence-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, so every version marker in the package, both plugin manifests, the managed blocks, the overlay markers, and the validator constants names 5.15.0
    - M2: `keel/CHANGELOG.md` carries a 5.15.0 entry stating that the openspec doctor line reports the diagnosed repository's declaration rather than Keel's own, that absence is now distinguished from a read failure, and that which binary runs is deliberately unchanged
    - M3: the spec delta is promoted into `openspec/specs/`, `node bin/keel.js openspec validate doctor-answers-for-the-repo-it-names --strict` passes, and `openspec validate --specs --strict` reports 21 passed and 0 failed after the promotion, so the promoted requirement satisfies the strict validator it is stored beside
    - M4: `npm test` passes with no failing scenario and no exception
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:788bdcf737f1135a633076bfb4667efe980ab8b17a2ba7d15fe8f71ab5e0e9a1
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` reports `version-alignment scenario passed.` 20 markers moved from 5.14.0 to 5.15.0 across twenty files: the package and lockfile, both plugin manifests, the three `keel:start` managed blocks, the twelve `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`, the AGENTS.md title and its preflight line, and the validator's `PACKAGE_VERSION`/`PROTOCOL_VERSION`. Two occurrences of `5.14.0` were deliberately left: the 5.14.0 changelog heading, and the historical measurement in the docstring of `validate_context_names_its_keel_scenario`, which records what was observed at that version.
    - M2: pass. `keel/CHANGELOG.md` carries `## 5.15.0 - doctor answers for the repository it names`, stating that the declaration is read from the diagnosed repository with no fallback, that the two versions on the line are now attributed to their sources, that declaring nothing and failing to read are reported as different facts, and that rerooting resolution was declined as a decision rather than omitted — with the reason.
    - M3: pass. The delta is promoted into `openspec/specs/keel-target-surface-diagnostics/spec.md` and `node bin/keel.js openspec validate doctor-answers-for-the-repo-it-names --strict` reports the change valid. `openspec validate --specs --strict` reports `Totals: 21 passed, 0 failed (21 items)` after the promotion, so the promoted requirement satisfies the strict validator it is stored beside — its modal verbs are in the first paragraph, which is the condition the 8 failures recorded in #46 used to violate.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 124 scenarios.` — no failing scenario, no exception, none skipped.
    - Review:
      - Status: pass
      - Acceptance check: the release claims are checked by running what they describe rather than by reading it — the alignment scenario over every marker, the real suite over every scenario, and the OpenSpec validator over the promoted store. M3 asserts an absolute result (21 passed, 0 failed) rather than the differential the previous release had to settle for, because the failures that forced that differential are gone.
      - Scope check: `git status --short` lists 23 modified files, every one of them a Touch entry of 1.1 or 2.1, plus this change's own untracked directory. The Touch list was corrected mid-task and the task reauthorized — see Findings.
      - Findings: one. `.codex/skills/openspec-sync-specs/SKILL.md` was written while it was not in this task's Touch. The version bump was applied by a `python3` heredoc through Bash, which is not a Keel-tool write, so the PreToolUse guard never saw it — the guard binds the host's file-writing tools, and a shell loop writes underneath it. The omission was mine: the Touch list enumerated the `.codex/` sync skill's three siblings and not it, while the `.claude/` side listed all four. It was caught by the semantic Scope check reading `git status`, not by any gate. The contract was corrected and the task reauthorized rather than the write being back-filled into the record: `keel gate task-start --record` reported `Re-recorded over a different contract: was sha256:52e2437d…, now sha256:788bdcf7…` and declared prior evidence stale, so all four checks were re-run under the new contract and the evidence above is from that run. Recording this as resolved would be wrong — the write outside Touch happened and no check proves it could not happen again, since the gap is structural: an enforcement hook on tool writes cannot bind a shell. Durable owner: https://github.com/TanglmChris/keel/issues/53
    - Blocker: none

## Invalidates

- I1: "No lockfile in a published install; there is then nothing to disagree with, which is not the same as agreement and is reported as such." — the `catch` comment in `lockedOpenSpecVersion()`, `bin/keel.js`. It explains the absent-lockfile case as a property of how Keel was installed, which is exactly the misattribution this change removes: after it, absence is a statement about the diagnosed repository and has nothing to do with whether Keel was published. Updated by: 1.1
- I2: "this repository validated against 1.4.1 while its lockfile resolves 1.6.0. `keel doctor` now names the resolved command and both versions" — the 5.11.0 entry in `keel/CHANGELOG.md`. The second version it claims doctor names was Keel's own, not the repository's, so the sentence overstates what 5.11.0 shipped. Discard reason: a changelog entry records what a release did at the time it was written, and correcting it would erase the evidence that #57 was found against. The live correction is the 5.15.0 entry written by 2.1.
- I3: "version=5.14.0" — grep it and you find the `keel:start` managed block in `AGENTS.md`, `CLAUDE.md`, and `assets/bootstrap/AGENTS.md`, plus the eleven `keel:openspec-surface-overlay` markers under `.claude/` and `.codex/`; the same version is written as `"version": "5.14.0"` in `package.json`, `package-lock.json`, and both plugin manifests, in the AGENTS.md title and its preflight line, and in the `PACKAGE_VERSION`/`PROTOCOL_VERSION` constants of `scripts/validate_plugin.py`. Updated by: 2.1

## Expectation Coverage

- E1: The OpenSpec version doctor reports as declared is the one declared by the repository doctor names. Covered by: 1.1
- E2: A repository that declares no OpenSpec version is told so, and is not warned at for the absence. Covered by: 1.1
- E3: Which `openspec` binary Keel resolves and runs is unchanged, so no consumer's validation silently switches programs at upgrade. Covered by: 1.1
- E4: The reporting is proved against a repository other than Keel's own checkout, so the defect cannot reappear under the coverage that hid it. Covered by: 1.1
- E5: A reader of the release notes learns the openspec doctor line changed what it is a statement about. Covered by: 2.1
