# Tasks

## 1. Say registry lag plainly, and release only what the registry serves

- [x] 1.1 Report a version the registry does not serve yet as `pending`, and name the registry's latest on the CLI line
  - Covers:
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / A version the registry does not serve yet is pending, not failed
    - keel-native-plugin-package / One owner-run update covers every installed Keel component / An E404 the registry cannot explain stays a failure
    - D1
    - D2
    - D3
  - Read:
    - openspec/changes/registry-lag/design.md
    - bin/keel.js
  - Touch:
    - bin/keel.js
    - scripts/validate_plugin.py
    - docs/updating.md
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario update-registry-lag`: with a fake claude whose `plugin update` exits 1 writing `Could not resolve @christang/keel@5.2.0 from the npm registry: E404 No match found for version 5.2.0` and a fake npm whose `view @christang/keel version` prints 5.1.0, `keel --update` prints a Claude line reading `pending` that names 5.2.0, 5.1.0 and rerunning in a few minutes and does not read `failed`, a CLI line naming 5.1.0 as the registry's latest, a Codex line reporting `5.0.0 -> 5.1.0`, and exits 0; with `npm view` printing 5.2.0, and again with `npm view` exiting 1, the Claude line reads `failed` and the exit is nonzero. Fails with: `update-registry-lag:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario update-covers-installed-hosts`, `--scenario update-host-query-timeout`, `--scenario update-host-query-retry`, `--scenario update-claude-refresh-retry`, `--scenario update-codex-refresh-retry`, and `--scenario update-codex-from-disk` pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:663a7f569331c0e9cafd092dd88fa61732e04deca7dd92d59e22fa2a8dcf60af (keel 5.177.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario update-registry-lag` reports `update-registry-lag scenario passed.` (exit 0): with the fake claude's `plugin update` exiting 1 on the #421 E404 text and `npm view` printing 5.1.0, the Claude line read `pending - the npm registry here does not serve 5.2.0 yet (its latest is 5.1.0); rerun keel --update in a few minutes`, the CLI line named `the npm registry's latest here is 5.1.0`, Codex still reported `5.0.0 -> 5.1.0`, and the exit was 0; with `npm view` printing 5.2.0, and with `npm view` exiting 1, the Claude line was the `failed` line carrying the E404 and the exit was nonzero.
    - M1.red: fail. Before the change: `update-registry-lag: a version the registry does not serve yet was not reported pending: 'keel update: claude plugin: failed - \`claude plugin update keel@keel-marketplace\` exited 1: ✘ Failed to update plugin "keel@keel-marketplace": Could not resolve @christang/keel@5.2.0 from the npm registry: E404 No match found for version 5.2.0'` (exit 1) — the #421 symptom.
    - M1.green: pass. With `registryLag()` in `bin/keel.js` (match `E404 No match found for version X` in the plugin update's output, then `npm view @christang/keel version --prefer-online` under the host-query limit, lag only when X is newer), `updateClaudePlugin` reporting `pending` and returning success in that case, and `updateGlobalCli` naming the registry's latest for the default source, the scenario passed.
    - M2: pass. `update-covers-installed-hosts`, `update-host-query-timeout`, `update-host-query-retry`, `update-claude-refresh-retry`, `update-codex-refresh-retry`, and `update-codex-from-disk` each report `scenario passed.`; the first asserts the exact host call list, so a normal update runs no `npm view`.
    - Review:
      - Status: pass
      - Acceptance check: through the real `keel --update` with stub npm, claude and codex, registry lag reads `pending` with both versions and a rerun hint and exits 0, an E404 the registry's answer does not explain stays `failed` and exits nonzero, and the CLI line names the registry's latest. `docs/updating.md` (I1) now lists `pending` and no longer tells the reader a `failed` line is expected after a release.
      - Scope check: `git status --short` lists `bin/keel.js`, `docs/updating.md`, `scripts/validate_plugin.py`, and this change's directory.
      - Findings: `bin/keel.js` declares `compareVersions` twice (near the Codex cache helpers and again before `printProtocolVersionDrift`); the later, three-part numeric one wins, so pre-release suffixes compare as NaN. Discard reason: pre-existing on origin/main and out of this task's scope; every version compared here is a plain x.y.z release, and the duplicate is reported to the owner as a candidate issue rather than filed, per the session's instruction that new issues go to the owner first.
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 Wait in the publish job until the registry serves the version
  - Covers:
    - keel-native-plugin-package / A release completes only once the registry serves its version / The wait ends when the registry serves the version
    - keel-native-plugin-package / A release completes only once the registry serves its version / A version the registry never serves fails the wait
    - keel-native-plugin-package / A release completes only once the registry serves its version / The release waits for the registry
    - D4
    - D5
    - D6
  - Read:
    - openspec/changes/registry-lag/design.md
    - .github/workflows/publish.yml
  - Touch:
    - scripts/await_registry.js
    - .github/workflows/publish.yml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario publish-awaits-registry`: `scripts/await_registry.js @christang/keel 5.2.0 --interval-seconds 0` against a fake npm whose `view @christang/keel@5.2.0 version` exits 1 with E404 twice and then prints 5.2.0 polls three times and exits 0; against one that never prints it, with `--timeout-seconds 1`, it exits nonzero naming 5.2.0 and the limit; and `publish.yml` runs it for the planned version in a step after `Publish` and before `Tag and release the landed version` with the `Publish` step's skip condition, while a planted copy with that step moved after the tag step is refused. Fails with: `publish-awaits-registry:`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario release-notes-name-the-directory-branch` and `--scenario validation-runner` pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:04b542d4eae5bc22321debbe15551584cdd325d2db59e7d204e0266709c59cc5 (keel 5.177.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario publish-awaits-registry` reports `publish-awaits-registry scenario passed.` (exit 0): against a fake npm that exits 1 with E404 twice and then prints 5.2.0, the script asked for `view @christang/keel@5.2.0 version`, polled three times and exited 0; against one that never serves it, `--timeout-seconds 1` exited nonzero naming 5.2.0 and `1 s`; `publish.yml` passes `registry_wait_problem`, and a planted copy with the wait step moved after the tag step is refused. Smoke against the real registry (`/opt/homebrew/bin/npm`): `node scripts/await_registry.js @christang/keel 5.177.0 --timeout-seconds 60` printed `the registry serves @christang/keel@5.177.0 after 1 s and 1 poll(s)` (exit 0); `... 9.9.9 --interval-seconds 2 --timeout-seconds 5` printed `the registry did not serve @christang/keel@9.9.9 within 5 s (2 poll(s)); re-run the job to wait again` (exit 1).
    - M1.red: fail. Before the change: `publish-awaits-registry: scripts/await_registry.js is missing.` (exit 1).
    - M1.green: pass. With `scripts/await_registry.js` (polls `npm view <package>@<version> version --prefer-online` every 15 s for at most 15 minutes by default, a nonzero view counting as not yet) and a `Wait until the registry serves the version` step in `publish.yml` between `Publish` and `Tag and release the landed version` under `if: steps.plan.outputs.skip != 'true'`, the scenario passed.
    - M2: pass. `release-notes-name-the-directory-branch` and `validation-runner` each report `scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: the script's behavior is exercised through its command line against a stub npm and the real registry, both arms; the workflow's ordering and skip condition are asserted by reading it, with a planted wrong order refused, because the workflow runs only on GitHub.
      - Scope check: `git status --short` adds `scripts/await_registry.js`, `.github/workflows/publish.yml`, and `scripts/validate_plugin.py` to task 1.1's files; `scripts/directory_tree.js` keeps only the scripts the shipped code runs, so the new development script stays out of the directory tree.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [ ] 2.1 Release and promote the spec
  - Covers:
    - E4
  - Touch:
    - package.json
    - npm-shrinkwrap.json
    - .claude-plugin/marketplace.json
    - .claude-plugin/plugin.json
    - plugins/keel/.claude-plugin/plugin.json
    - plugins/keel/.codex-plugin/plugin.json
    - scripts/validate_plugin.py
    - AGENTS.md
    - CLAUDE.md
    - assets/bootstrap/AGENTS.md
    - keel/CHANGELOG.md
    - openspec/specs/keel-native-plugin-package/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the delta is promoted into `keel-native-plugin-package`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: pending
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "the Claude plugin line may read `failed` with `E404 No match found for version` (#421). Nothing is wrong with the install: run `keel --update` again a few minutes later." — `docs/updating.md`, and its status list, which names no `pending`. Updated by: 1.1.
- I2: "The exit status MUST be nonzero only when a step that ran failed." with no `pending` clause before it — `keel-native-plugin-package`. Updated by: 2.1.
- I3: "confirm a publish from the job log, not the registry" — the owner's native Claude memory for this repository (`keel-moved-from-windows-to-mac.md`). Discard reason: native memory lives outside the repository and no task can own it; the session checks and updates it after the change lands, as the Project Conventions require.

## Expectation Coverage

- E1: Right after a release, a Claude plugin update the registry cannot serve yet reads `pending` with a rerun hint, not `failed`, and does not fail `keel --update`; an E404 the registry cannot explain still fails (#421 option 1; D1, D2). Covered by: 1.1
- E2: The CLI line says which version the registry served as its latest (#421 owner decision; D3). Covered by: 1.1
- E3: The publish job tags and releases only after registry.npmjs.org serves the version (#421 option 2; D4, D5, D6). Covered by: 1.2
- E4: The release carries it. Covered by: 2.1
