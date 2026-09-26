# Tasks

## 1. The declaration

- [x] 1.1 `keel/config.yaml` may declare `merge: human` or `merge: repository:<check>`; `keel context` reports a readable declaration with its consequence, `keel --doctor` reports it or its absence, and an unreadable one claims nothing
  - Covers:
    - keel-merge-declaration / A repository declares who merges / A repository merge is reported with its consequence
    - keel-merge-declaration / A repository declares who merges / An absent declaration adds nothing
    - keel-merge-declaration / A merge claim names its basis / A bare repository claim is refused
    - keel-merge-declaration / The declaration is not a permission / authorize merge stays unknown
    - D1
    - D2
    - D3
    - D4
    - D5
    - F3
  - Read:
    - src/core/config.js
    - src/core/context.js
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/config.js
    - src/core/context.js
    - bin/keel.js
    - scripts/validate_plugin.py
    - keel/config.yaml
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `a-merge-names-who-makes-it` scenario asserts that a fixture declaring `merge: repository:full-gate` gets a `Merge:` line from `keel context` naming `full-gate` and stating that no human reviews before merge, that `merge: human` is reported as such, that an undeclared fixture prints no `Merge:` line, and that `keel --doctor` reports all three including the absence. Fails with: `no merge declaration reported`
    - M2: `merge: repository` with no check, and `merge: robots`, each produce no `Merge:` claim and a warning naming the value and the accepted forms. Fails with: `accepted a merge claim with no basis`
    - M3 (regression): a fixture listing `merge` under `authorize:` still reports it as an unrecognized action that authorizes nothing, so the new key cannot be read as agent permission
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario a-count-is-derived-from-what-it-counts` and `--scenario delegation-resident-text` pass with `merge` in the exported declaration list and named in the header
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if reporting the declaration requires reading GitHub settings, because D6 records that Keel stays local and offline and the declaration is the owner's claim.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:66d08c0b5f62c5ee881ef53937e629268b3189e4a61c9d89b81c46e007717074
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-merge-names-who-makes-it` reports the scenario passing. `merge: repository:full-gate` gets `Merge: repository — the default branch merges when full-gate passes; no human reviews before merge, so that check is the last gate`; `merge: human` gets a line saying a person merges; an undeclared fixture gets no `Merge:` line; and `keel --doctor` reports all three — `repository:full-gate`, `human`, and `undeclared`. The consequence is asserted on its own (`no human`), because a line that echoed the value would leave the reader to infer the thing the declaration exists to say.
    - M1.red: fail, for the declared reason. `a-merge-names-who-makes-it: no merge declaration reported — a repository that declared its default branch merges on \`full-gate\` is told nothing about it where the session starts.` Carries the declared signature `no merge declaration reported`.
    - M1.green: pass. Same command after `readMergeDeclaration` was added to `src/core/config.js`, `resolveContext`/`renderContext` reported a declared value, and `printMergeSurface` joined the doctor sequence.
    - M2: pass. `merge: repository` and `merge: robots` each produce no `Merge:` line, and the projection's warning names the value and `human, repository:<check>`. The bare case additionally says why a check is required.
    - M2.red: fail, for the declared reason, and a revealing one. `a-merge-names-who-makes-it: accepted a merge claim with no basis — \`merge: repository\` produced ['Merge: repository — the default branch merges when null passes; no human reviews before merge, so that check is the last gate'].` Carries the declared signature `accepted a merge claim with no basis`. "merges when null passes" is exactly the claim the refusal exists to prevent: that no person reviews, stated with nothing named in their place.
    - M2.green: pass. Same command after an unrecognized value returned `unknown` with a message and no claim.
    - M3: pass. A fixture listing `merge` under `authorize:` gets `authorize: failed - keel/config.yaml declares unrecognized action: merge; …` from the doctor. The assertion was first written as "`merge` and `unrecognized` both appear in the doctor output", which would have been satisfied by the new `Merge:` section plus any other refusal on the page; it was tightened to the exact phrase `unrecognized action: merge` after checking which line actually satisfied it.
    - M4: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-count-is-derived-from-what-it-counts` and `--scenario delegation-resident-text` both pass with `merge` as the eighth name in `CONFIG_DECLARATIONS` and the header naming it. `npm test` reports `validation --all passed: baseline plus 183 scenarios, 1 skipped: output-survives-the-pipe.` Adding `merge` to the list did **not** at first make either scenario fail — see Findings.
    - Review:
      - Status: pass
      - Acceptance check: the Acceptance is that a declaration reaches the session with its consequence, that a claim without a basis claims nothing, and that the key grants the agent nothing. Each is asserted on the real projection and doctor output. The decision worth naming is D3: an undeclared repository gets no line, because Keel cannot know how it merges and a default `human` would be the same unfounded assertion this change stops the protocol making.
      - Scope check: `git status --short` shows `src/core/config.js`, `src/core/context.js`, `bin/keel.js`, `scripts/validate_plugin.py`, and `keel/config.yaml` — this task's five Touch entries — plus this change's own directory. The Stop Rule held: nothing reads GitHub.
      - Findings: the derived header rule shipped in 5.66.0 never checked the header. Both callers passed the whole of `keel/config.yaml`, so any declaration name appearing anywhere in the file satisfied "the header names it". Adding `merge` to the export should have turned both scenarios red and did not, because the triage section's comment "It also never authorizes a merge" already contained the word. The check that exists to catch an undocumented declaration was satisfied by an unrelated sentence — a vacuous pass that would have hidden any future declaration whose name is an ordinary English word. Resolved here: M4, via `config_header_paragraph`, which reads only the opening paragraph containing `independent declarations live here` up to the first bare `#`. Both callers and the miscount mutation now pass raw file text through it, and a new assertion plants a name mentioned only in the body and requires it to be refused — that assertion was red before the fix. Once the rule read the header, it reported `keel/config.yaml's header does not name 'merge'`, which is the red M4 should have shown in the first place.
    - Blocker: none
    - Reauthorizations: none

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1
    - E2
    - E3
    - E4
    - I1
    - I2
  - Read:
    - keel/CHANGELOG.md
    - README.md
  - Touch:
    - package.json
    - package-lock.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - README.md
    - openspec/specs/keel-merge-declaration/spec.md
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
    - Reason: this task's whole effect is version markers, documentation, a changelog entry, and a promoted spec. The behavior was proven red-green in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, with the 5.71.0 section written into the stub
    - M2: `AGENTS.md` `## Unattended runs` states that the agent never merges and that a repository may, by a rule its owner declared in `merge:`; `README.md` documents both forms and why a bare `repository` is refused
    - M3: `keel/CHANGELOG.md` records why the declaration is not an `authorize:` entry and why Keel does not verify it against GitHub
    - M4: the delta is promoted, `node node_modules/.bin/openspec validate a-merge-names-who-makes-it --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ee9d830d552950fabf797644f10ac52b39fcde86f8835ca24b5b41f73d4f70bc
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes; every marker moved 5.70.0 to 5.71.0 via `node scripts/bump_version.js minor`, and the 5.71.0 section was written into the stub, which the 5.69.0 rule checks. The Stop Rule held.
    - M2: pass. `AGENTS.md` `## Unattended runs` keeps "It may not merge one" and adds that a repository may merge on its own rule, that `merge:` says so in `human` or `repository:<check>` form, that the declaration grants the agent nothing, and that `keel context` reports it so a reader does not assume a person reviewed what only the check did. `README.md` gains "Who merges" beside the routing section, with the example, the bare-`repository` refusal and its reason, and the not-a-permission rule.
    - M3: pass. `keel/CHANGELOG.md` carries `## 5.71.0 - a merge names who makes it`. It records why the declaration is not an `authorize:` entry, that Keel reads the claim and never GitHub and therefore cannot verify it, that this repository declares nothing because turning auto-merge on is the owner's act, the "merges when null passes" red, and the 5.66.0 header rule that never read the header.
    - M4: pass. The delta is promoted into the new `openspec/specs/keel-merge-declaration/spec.md` with a `## Purpose` section. `node node_modules/.bin/openspec validate a-merge-names-who-makes-it --strict` reports valid, and `npm test` reports `validation --all passed: baseline plus 183 scenarios, 1 skipped: output-survives-the-pipe.`, which includes `published-specs-validate-strictly`.
    - Review:
      - Status: pass
      - Acceptance check: M1 reads every version marker, and this release is judged by the stub rule like the two before it. M2 and M3 carry the distinction a reader most needs and most easily loses — the agent still never merges, and the declaration is a description of the repository rather than a grant. The protocol sentence was extended rather than rewritten, because it remains exactly true about the agent and a reader searching for it should still find it.
      - Scope check: `git status --short` shows the version markers, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `README.md`, and the promoted spec, plus the files 1.1 declared complete and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "It may not merge one: merging is where an unreviewed decision becomes the project's history,
  and no Keel declaration authorizes it." — `AGENTS.md` `## Unattended runs`. It stays true about the
  agent and stops being the protocol's whole statement about merging, which a reader took to mean
  every merge is human.
  Updated by: 2.1
- I2: "Seven independent declarations live here" — the header of `keel/config.yaml`. An eighth is
  added, and the enumeration is the checked part.
  Updated by: 1.1

## Expectation Coverage

- E1: A repository can declare who merges, and a repository merge is reported with the plain
  consequence that no human reviews first (D2, D4). Covered by: 1.1
- E2: A merge claim without its basis claims nothing and is named (D2, D5, F3). Covered by: 1.1
- E3: The declaration grants the agent nothing; `authorize: merge` stays unknown (D1). Covered by: 1.1
- E4: The protocol states that the agent never merges and a repository may by a declared rule (I1).
  Covered by: 2.1
- E5: Whether Keel verifies the claim against GitHub (D6, A3). Discard reason: deliberately not done.
  The projection and gates are local and offline, and that property is what their verdicts rest on;
  the declaration is the owner's claim, reported where Review can see it.
