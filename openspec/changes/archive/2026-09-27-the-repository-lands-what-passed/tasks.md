# Tasks

## 1. The workflow

- [x] 1.1 `publish.yml`'s concurrency group declares `queue: max`, and a copy without it is refused
  - Covers:
    - keel-validation-runner / A pending publish waits instead of being cancelled / A group without a queue is refused
    - D1
    - F1
  - Read:
    - .github/workflows/publish.yml
    - scripts/validate_plugin.py
  - Touch:
    - .github/workflows/publish.yml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: the `a-publish-waits-for-the-one-before-it` scenario asserts the real `publish.yml` declares `queue: max` in its concurrency group and refuses a copy with that line removed — the exact state 5.70.0 shipped. Fails with: `a pending publish would be cancelled by the next one`
    - M2 (regression): the scenario's existing refusals — no group, no `cancel-in-progress: false`, a per-run group — still fire on their planted copies
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the docs' `queue` semantics cannot be confirmed from GitHub's own documentation, because the fix would then rest on recall.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:061b72065964a400c6e7fabdff0e0a369cc0f367e6db6602bcf86917646c44da
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario a-publish-waits-for-the-one-before-it` reports the scenario passing. The real `publish.yml` declares `queue: max`, and a copy with that line removed — byte-for-byte what 5.70.0 shipped — is refused. The semantics were confirmed from GitHub's documentation before the change, per the Stop Rule: "By default, any existing `pending` job or workflow in the same concurrency group will be canceled", and `queue: max` allows up to 100 pending runs, forbidden only with `cancel-in-progress: true`.
    - M1.red: fail, for the declared reason. `a-publish-waits-for-the-one-before-it: a pending publish would be cancelled by the next one — \`queue: max\` could not be located to remove, so the real file keeps at most one pending run and cancels the rest.` Carries the declared signature `a pending publish would be cancelled by the next one`.
    - M1.green: pass. Same command after `publish.yml` gained `queue: max` and `publish_serialization_problem` required it. The workflow comment that called `cancel-in-progress: false` the load-bearing half was rewritten to name both settings and what each protects.
    - M2: pass. The scenario's existing planted copies — no `concurrency:` block, no `cancel-in-progress: false`, `group: publish-${{ github.ref }}` — are still each refused, and `npm test` reports `validation --all passed: baseline plus 183 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the defect is mine from 5.70.0, and what let it through is worth stating: the one real burst after it shipped had exactly two releases — one running, one pending — which is the only shape `queue: single` handles without loss, so it looked like proof of serialization. The new refusal is asserted on a planted copy of the shipped configuration, not on reasoning about it. `queue: max` is checked separately from `cancel-in-progress: false` because a group keeping one pending run is indistinguishable from a queue until the third event.
      - Scope check: `git status --short` shows `.github/workflows/publish.yml` and `scripts/validate_plugin.py` — this task's two Touch entries — plus this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 `publish.yml` gains a `land` job that merges an owner's pull request into `main` once its head passed `full-gate`, checking out nothing, and the `publish` job publishes the landed version before tagging it — all in one run
  - Covers:
    - keel-validation-runner / The repository lands only what passed / A merge without the check is refused
    - keel-validation-runner / The repository lands only what passed / Checking out pull request code is refused
    - keel-validation-runner / The repository lands only what passed / Tagging before publishing is refused
    - D2
    - D3
    - D4
    - D5
    - D6
    - D7
    - D8
    - F2
    - F3
    - F4
    - F5
  - Read:
    - .github/workflows/publish.yml
    - .github/workflows/test.yml
    - scripts/validate_plugin.py
  - Touch:
    - .github/workflows/publish.yml
    - scripts/validate_plugin.py
    - keel/config.yaml
  - Verify:
    - Strategy: vertical-tdd
    - M1: a new `the-repository-lands-what-passed` scenario asserts the real `publish.yml` has a `land` job triggered by `workflow_run` on `Full gate` and by `pull_request_target`, which reads the `full-gate` check-run and merges with `--match-head-commit`, and refuses copies with either removed. Fails with: `merges without confirming full-gate`
    - M2: the same scenario refuses a copy whose `land` job gains an `actions/checkout` step, and copies dropping the owner filter or the same-repository filter. Fails with: `pull request code could run with a write token`
    - M3: the same scenario asserts that in the `publish` job `npm publish` precedes `gh release create`, and refuses a copy with the two steps swapped. Fails with: `a failed publish would be left tagged and never retried`
    - M4 (regression): `npm test` reports no failing scenario, and `keel context` in this repository reports `Merge: repository` naming `full-gate`
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if the landing job needs a stored secret, because D2 exists so that none does.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:96ea3702aa2414e173a245c0006aaecb4b1d87b2226e91f6078ff8fda9b43298
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario the-repository-lands-what-passed` reports the scenario passing. The real `publish.yml` has a `land` job triggered by `workflow_run` on `Full gate` (ignoring `main`) and by `pull_request_target`; it reads `check-runs?check_name=full-gate` on the head commit and merges with `--match-head-commit`. Copies with either removed are refused. Beyond the scenario, the workflow was parsed with the repository's transitive `yaml` package (triggers, concurrency `{group: publish, queue: max, cancel-in-progress: false}`, both jobs with their permissions and step order as intended), every `run:` script passed `bash -n`, and both jq filters were run against the live API: the open-owner-PR lookup returned nothing for #156's now-closed head and `156` with the state filter relaxed; the gate query returned `success` on `e7faef7` and `absent` for a check that does not exist.
    - M1.red: fail, for the declared reason. `the-repository-lands-what-passed: merges without confirming full-gate — .github/workflows/publish.yml has no \`land\` job, so nothing lands a pull request that passed.` Carries the declared signature `merges without confirming full-gate`.
    - M1.green: pass. Same command after the `land` and reworked `publish` jobs were written and `landing_problem` checked the check-run read and the head-commit pin — and only those, so M2 and M3 could still go red on their own.
    - M2: pass. A copy whose `land` job gains `actions/checkout` is refused, as are copies with the owner filter or the same-repository filter removed from the pull-request lookup.
    - M2.red: fail, for the declared reason. `the-repository-lands-what-passed: pull request code could run with a write token — a \`land\` job with a checkout step was accepted.` Carries the declared signature `pull request code could run with a write token`. A real red: the rule at that point checked M1's properties only.
    - M2.green: pass. Same command after the rule refused a checkout in `land` and required both filters.
    - M3: pass. The real `publish` job runs `npm publish` before `gh release create`, and a copy with the two steps swapped is refused.
    - M3.red: fail, for the declared reason. `the-repository-lands-what-passed: a failed publish would be left tagged and never retried — a \`publish\` job that creates the release before \`npm publish\` was accepted.` Carries the declared signature `a failed publish would be left tagged and never retried`. Also a real red, against the rule as it stood after M2.
    - M3.green: pass. Same command after the rule compared the two steps' positions in the `publish` job.
    - M4: pass. `npm test` reports `validation --all passed: baseline plus 184 scenarios, 1 skipped: output-survives-the-pipe.` With `merge: repository:full-gate` declared, `keel context` in this repository prints `Merge: repository — the default branch merges when full-gate passes; no human reviews before merge, so that check is the last gate`.
    - Review:
      - Status: pass
      - Acceptance check: all three reds in this task were produced against the rule as it actually stood, one slice at a time, rather than by removing code afterwards. What the suite cannot prove is the run on GitHub: `workflow_run` and `pull_request_target` execute only from the default branch, so the first pull request after this lands is the first real execution, and E5 records that honestly rather than claiming it. What is established before landing is every piece that can be: YAML structure, shell syntax, both API filters against live data, and the changelog extraction producing the 5.71.0 section and title. Branch protection (verified: `full-gate` required, strict) means a logic error here produces a refused merge, not an untested one.
      - Scope check: `git status --short` shows `.github/workflows/publish.yml`, `scripts/validate_plugin.py`, and `keel/config.yaml` — this task's three Touch entries — plus this change's own directory. The Stop Rule held: the only token is `GITHUB_TOKEN`; no secret is referenced.
      - Findings: none
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
    - I3
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
    - openspec/specs/keel-validation-runner/spec.md
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
    - Reason: this task's whole effect is version markers, documentation, a changelog entry, and a promoted spec. The behavior was proven red-green in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes, with the 5.72.0 section written into the stub
    - M2: `keel/CHANGELOG.md` corrects the 5.70.0 claim that `cancel-in-progress: false` was the load-bearing half, and records why one workflow run needs no secret
    - M3: `README.md` "Who merges" describes the landing job rather than only GitHub auto-merge
    - M4: the delta is promoted, `node node_modules/.bin/openspec validate the-repository-lands-what-passed --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:40e02825e961ae9e1cf90438b1f5a4f315e79bf449228775307afe9550d9b13b
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes; every marker moved 5.71.0 to 5.72.0 via `node scripts/bump_version.js minor`, and the 5.72.0 section was written into the stub. The Stop Rule held.
    - M2: pass. `keel/CHANGELOG.md` `## 5.72.0 - the repository lands what passed` opens with the correction to 5.70.0 — that `cancel-in-progress: false` protects only the running publish, what the default queue does to pending ones, and why the two-release burst looked like proof — before describing the change. It records why one run needs no secret (events made with `GITHUB_TOKEN` start no new run, so a chain breaks at each hand-off) and that the same rule is what prevents a double publish.
    - M3: pass. `README.md` "Who merges" now names both repository-side shapes, auto-merge and a workflow job that merges what passed, and says Keel's own repository uses the second.
    - M4: pass. The delta is promoted into `openspec/specs/keel-validation-runner/spec.md`. `node node_modules/.bin/openspec validate the-repository-lands-what-passed --strict` reports valid, and `npm test` reports `validation --all passed: baseline plus 184 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the correction leads the entry rather than trailing it, because a reader of the 5.70.0 section needs to find that it was wrong, and the fix is otherwise only visible to someone reading the workflow file. The 5.70.0 section itself is left as written: the changelog is history, and rewriting it would hide that the claim shipped.
      - Scope check: `git status --short` shows the version markers, `AGENTS.md`, `CLAUDE.md`, `assets/bootstrap/AGENTS.md`, `keel/CHANGELOG.md`, `README.md`, and the promoted spec, plus the files 1.1 and 1.2 declared complete and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "`cancel-in-progress: false` is the load-bearing half" — the 5.70.0 section of `keel/CHANGELOG.md`
  and the comment above `concurrency:` in `.github/workflows/publish.yml`. Half of it: without
  `queue: max` a pending publish is still cancelled. The changelog is history and is corrected by the
  5.72.0 entry; the workflow comment is rewritten.
  Updated by: 1.1, 2.1
- I2: "Undeclared here: this repository has not turned auto-merge on (#155)." — the `merge` comment in
  `keel/config.yaml`. This change declares `merge: repository:full-gate`.
  Updated by: 1.2
- I3: "A repository can still merge without a person, on a rule of its own: GitHub auto-merge behind a
  required status check." — `README.md` "Who merges". This repository merges through a workflow job,
  not GitHub's auto-merge setting, and the section should name both.
  Updated by: 2.1

## Expectation Coverage

- E1: A burst of releases publishes every version, because pending runs queue (D1, F1). Covered by: 1.1
- E2: A pull request lands only if it is the owner's, from this repository, into `main`, and its head
  passed `full-gate`, with no pull-request code run under a write token (D3, D4, D5). Covered by: 1.2
- E3: A landed version publishes and releases in the same run with no stored secret, and a failed publish
  is retried rather than left tagged (D2, D6, D7). Covered by: 1.2
- E4: The 5.70.0 claim is corrected and the merge declaration is true in this repository (I1, I2).
  Covered by: 2.1
- E5: End-to-end proof on GitHub. Discard reason: not obtainable before landing — the workflow runs only
  on GitHub from the default branch, so the first pull request after this lands is the first real run.
  That run is observed and reported as the end-to-end evidence rather than claimed here.
