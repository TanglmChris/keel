# Tasks

## 1. Vocabulary and enforcement

- [x] 1.1 `push:<glob>`, `issue-close:<owner>/<repo>`, and `cleanup:scratch` are accepted, refused in the wrong form, and reported
  - Covers:
    - keel-standing-authorization / A push authorization may name the branches it reaches / A push scope is reported with its enforcement
    - keel-standing-authorization / A push authorization may name the branches it reaches / A bare push beside a scoped one is refused
    - keel-standing-authorization / Closing an issue and cleaning the scratchpad are named and carried / The new names are carried with their scope
    - keel-standing-authorization / Closing an issue and cleaning the scratchpad are named and carried / A wrong form is refused with the one it needs
    - keel-standing-authorization / A repository declares standing authorization in a closed vocabulary / A declared action is authorized for the whole repository
    - D1
    - D2
    - D6
    - F1
    - F2
  - Read:
    - src/core/config.js
    - bin/keel.js
  - Touch:
    - src/core/config.js
    - bin/keel.js
    - README.md
    - keel/config.yaml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario authorize-push-close-cleanup` runs `keel --doctor` over a repository declaring `push:claude/*`, `push:worktree-*`, `issue-close:acme/widgets`, and `cleanup:scratch` and requires each scoped line and the push enforcement sentence; runs `keel gate task-start` over a task with no boundary there and requires the inherited entry to name all four; and requires `keel --doctor` to exit non-zero naming the entry and its form for `push` beside `push:claude/*`, a bare `issue-close`, `cleanup:runs`, and `push:main?`. Fails with: `authorize-push-close-cleanup:`
    - M2 (regression): `standing-authorization-declaration`, `chat-reply-authorization`, `continuation-docs`, and `continuation-authorization` still pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3bb85a7423550cd76f363a8bb7a7e0fa9610040b7305546b9750b57f0cfb8fc7
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario authorize-push-close-cleanup` reports `authorize-push-close-cleanup scenario passed.`
    - M1.red: fail. Before the change the scenario reported `authorize-push-close-cleanup: doctor's push line lacks ['authorized', 'claude/*', 'worktree-*']: ''`, carrying the declared signature `authorize-push-close-cleanup:`: the whole declaration was refused as unrecognized, so no per-action line was printed.
    - M1.green: pass. With the three forms in the vocabulary, the mixed-push refusal, and the doctor's `push scope: enforced` line, doctor reports each scope, the inherited autonomy entry names all four, and each wrong form exits non-zero naming its form.
    - M2: pass. `standing-authorization-declaration`, `chat-reply-authorization`, `continuation-docs`, and `continuation-authorization` each report `scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario reads real `keel --doctor` output per action line, the real `task-start` capsule's inherited entry, and each refusal's exit code and text.
      - Scope check: `git status --short` lists `src/core/config.js`, `bin/keel.js`, `README.md`, `keel/config.yaml`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/275 — a list item containing a space silently ends the `authorize:` block and drops every later entry while the doctor reports `ok`; found while choosing M1's malformed example.
    - Blocker: none
    - Reauthorizations: M1's malformed-glob example was `push:main branch`; before any evidence was recorded it was changed to `push:main?` and re-recorded, because a space ends the block silently (issue #275) rather than reaching the scope check.

- [x] 1.2 The Claude write guard refuses a `git push` outside the declared branches
  - Covers:
    - keel-touch-write-guard / A push outside the declared branches is refused / A push to a declared branch passes
    - keel-touch-write-guard / A push outside the declared branches is refused / A push to main is refused without a task
    - keel-touch-write-guard / A push outside the declared branches is refused / A push with no refspec uses the branch's push destination
    - keel-touch-write-guard / A push outside the declared branches is refused / An undetermined target is refused with the explicit form
    - keel-touch-write-guard / A push outside the declared branches is refused / Nothing is checked without a push scope
    - keel-touch-write-guard / Guarded write tools outside Touch are denied deterministically / Non-file-edit tools are unaffected
    - keel-touch-write-guard / Guard capability is reported from observed evidence / Unguardable writes are documented
    - D2
    - D3
    - D4
    - D5
    - D7
    - F3
    - F4
    - F5
  - Read:
    - plugins/keel/scripts/pretooluse-guard.js
    - src/core/capabilities.js
  - Touch:
    - plugins/keel/scripts/pretooluse-guard.js
    - plugins/keel/hooks/hooks.json
    - .claude-plugin/plugin.json
    - src/core/capabilities.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario push-branch-guard` feeds the real hook script `Bash` events in a repository with a bare remote and `push:claude/*` declared and no manifest, and requires: `git add -A && git push -u origin claude/fix` allowed; `git push origin HEAD:main` denied naming `main`; a bare `git push` denied on a branch pushing to `origin/main` and allowed on one pushing to `origin/claude/fix`; `git push --all origin` and a push of a shell variable denied naming `git push origin <branch>`; a `push:` typo elsewhere in the block not lifting the check; and with a bare `push` declared, `git push origin HEAD:main` not intercepted. It also requires `hooks.json` to register the hook for `Bash`. Fails with: `push-branch-guard:`
    - M2 (regression): `touch-write-guard`, `touch-guard-record-layer`, `touch-guard-drift`, `touch-guard-surface`, `guard-stale-manifest`, and `guard-keeps-loaded-logic-under-manifest` still pass.
    - M3 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:11e3879f368e0058ce4781c498818a770f200c7bdcb4c695978d8e03a726e013
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario push-branch-guard` reports `push-branch-guard scenario passed.`
    - M1.red: fail. Before the change the scenario reported `push-branch-guard: hooks.json does not register the guard for Bash: ['Edit|Write|NotebookEdit']`, carrying the declared signature `push-branch-guard:`.
    - M1.green: pass. With the `Bash` registration and `checkPushes` in the hook, every case passes against the real script with no manifest: the declared push allowed, `HEAD:main` denied naming `main`, a bare `git push` resolved through `@{push}` both ways, `--all` and `"$BRANCH"` denied naming `git push origin <branch>`, a `deploy` typo leaving the check standing, and a bare `push` intercepting nothing. A hand probe also showed heredoc bodies skipped, `bash -c` pushes refused as undetermined, and `git log --grep push` allowed.
    - M2: pass. In the `npm test` run below, `touch-write-guard`, `touch-guard-record-layer`, `touch-guard-drift`, `touch-guard-surface`, `guard-stale-manifest`, and `guard-keeps-loaded-logic-under-manifest` each report `scenario passed.`
    - M3: pass. `npm test` reports `validation --all passed: baseline plus 247 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario feeds the shipped hook script real `Bash` events in a repository with a bare remote and reads each decision and its reason; `hooks.json` registration is read from the file.
      - Scope check: `git status --short` lists the hook script, `plugins/keel/hooks/hooks.json`, `.claude-plugin/plugin.json`, `src/core/capabilities.js`, `README.md`, `scripts/validate_plugin.py`, this change's directory, and 1.1's files.
      - Findings: Discard reason: a push run by another program — an npm script, a Makefile, a git alias — is not visible in the `Bash` command and is not checked; the capability boundary states that every other `Bash` command stays disciplinary, and following programs is beyond a hook that reads one command line.
    - Blocker: none
    - Reauthorizations: the first `npm test` failed `native-plugin-manifests`, because `.claude-plugin/plugin.json` repeats the hook registrations and lacked the `Bash` entry. That file was added to Touch and the contract re-recorded with `--keep-evidence M1`, since M1's text did not change; M2 and M3 were re-run under the new contract.

## 2. Release

- [x] 2.1 Release and promote the specs
  - Covers:
    - E3
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
    - openspec/specs/keel-standing-authorization/spec.md
    - openspec/specs/keel-touch-write-guard/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1 and 1.2, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the RENAMED, MODIFIED, and ADDED requirements are promoted into both published specs, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:955926f1a04ded67482ec462d57c63d2e1b0ecdd82017dca3542a2225c485fea
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.105.0 on top of `main` at 5.104.0 (#274). With the 5.105.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The RENAMED scope requirement, the MODIFIED vocabulary, Touch-denial, and capability requirements, and the three ADDED requirements are in both published specs; `published-specs-validate-strictly` reports `33 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, both published specs carry the new and renamed requirements with their scenarios, and the changelog names the issue, the owner's decision, and each form.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the two specs, all in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.105.0 reports `validation --all passed: baseline plus 247 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "accepted names: commit, push, release, archive, continuation, issue:<owner>/<repo>, protocol-refresh, chat-reply:<group>" — `README.md` and the matching comment in `keel/config.yaml`, asserted by `scripts/validate_plugin.py`. Updated by: 1.1
- I2: "The eight names above are the whole vocabulary." — `README.md`. Updated by: 1.1
- I3: "Closing an issue is not in scope and does not need to be" — `README.md`. Updated by: 1.1
- I4: "Keel records a scope and does not enforce it" — the doctor's `scope` line in `bin/keel.js`. Updated by: 1.1
- I5: "The guard covers file-edit tools only (Edit, Write, NotebookEdit); Bash and other indirect writes stay disciplinary" — `src/core/capabilities.js`. Updated by: 1.2
- I6: "a `PreToolUse` hook rejects any edit outside the files the task declared it would touch" — `README.md` feature list, which gains the push check. Updated by: 1.2
- I7: "A scope is a declaration Keel carries and never enforces" and "`Bash` and other indirect writes are identified as disciplinary, not guarded" — the published specs. Updated by: 2.1

## Expectation Coverage

- E1: A repository can declare push limited to branches, closing its own issues, and scratchpad cleanup, each refused in the wrong form and reported where the owner reads (D1, D2, D6). Covered by: 1.1
- E2: A Claude session pushing outside the declared branches, or pushing where the target cannot be determined, is stopped before the push runs, with or without a task (D3, D4, D5, D7). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1
