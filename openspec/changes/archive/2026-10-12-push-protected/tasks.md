# Tasks

## 1. Protected branches

- [x] 1.1 `push-protected:` is accepted, refused in the wrong form, and reported
  - Covers:
    - keel-standing-authorization / A protected branch is pushed only with the user's approval of that push / A protected branch is reported
    - keel-standing-authorization / A protected branch is pushed only with the user's approval of that push / A malformed protected entry is refused
    - D1
    - D4
    - F1
  - Read:
    - src/core/config.js
    - bin/keel.js
  - Touch:
    - src/core/config.js
    - bin/keel.js
    - keel/config.yaml
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario push-protected-declaration` requires `keel --doctor` over `push:claude/*` and `push-protected:main@iecc-pm` to report `push-protected` scoped to `main@iecc-pm` and that each push is asked, and to exit non-zero naming the entry for `push-protected:main@Not` (a malformed role) and for a bare `push` beside `push-protected:main`. Fails with: `push-protected-declaration:`
    - M2 (regression): `authorize-push-close-cleanup`, `standing-authorization-declaration`, `authorize-block-reads-every-line`, and `continuation-docs` still pass.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ea59506fa9fbe59e3a59b3fdc2db10a6e46167079de9f23266e64cad3ed7ef30
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario push-protected-declaration` reports `push-protected-declaration scenario passed.`
    - M1.red: fail. Before the change the scenario reported `push-protected-declaration: doctor's push-protected line is ''.`, carrying the declared signature `push-protected-declaration:`: the entry was refused as unrecognized, so no line was printed.
    - M1.green: pass. With `push-protected` in the vocabulary, its form and note, the extended mixed-push refusal, and the doctor's `protected push: asked` line, doctor reports `main@iecc-pm` and that each push is asked, and both malformed declarations exit non-zero naming the entry.
    - M2: pass. `authorize-push-close-cleanup`, `standing-authorization-declaration`, `authorize-block-reads-every-line`, and `continuation-docs` each report `scenario passed.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario reads real `keel --doctor` lines and exit codes for the accepted and both refused declarations.
      - Scope check: `git status --short` lists `src/core/config.js`, `bin/keel.js`, `keel/config.yaml`, `README.md`, `scripts/validate_plugin.py`, and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

- [x] 1.2 The write guard asks for a protected push, denies another role's and a mode that cannot ask
  - Covers:
    - keel-touch-write-guard / A push to a protected branch is asked, not refused / The coordinator is asked, once per push
    - keel-touch-write-guard / A push to a protected branch is asked, not refused / Another role is refused
    - keel-touch-write-guard / A push to a protected branch is asked, not refused / A mode that cannot ask is refused
    - keel-touch-write-guard / A push to a protected branch is asked, not refused / Other branches are unchanged
    - D2
    - D3
    - F1
    - F2
    - F3
    - F4
  - Read:
    - plugins/keel/scripts/pretooluse-guard.js
  - Touch:
    - plugins/keel/scripts/pretooluse-guard.js
    - README.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario push-protected-guard` feeds the real hook script `Bash` events in a repository declaring `push:claude/*` and `push-protected:main@iecc-pm` with chat roles bound, and requires: `git push origin HEAD:main` from the `iecc-pm` worktree in `default` mode to return `ask` naming `main` on two consecutive events with the chat store unchanged; the same from the `rtl` worktree to be denied naming `iecc-pm`; the `iecc-pm` push with `permission_mode` `bypassPermissions` and `dontAsk` each denied naming the mode; `claude/fix` allowed and `release` denied; and, with only `push-protected:main` declared, `release` denied and `main` asked. Fails with: `push-protected-guard:`
    - M2 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:df5a6cae7e3d3d97dabc89dbba5cc37d97368ef4459279a622366758ae293801
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario push-protected-guard` reports `push-protected-guard scenario passed.`
    - M1.red: fail. Before the change the scenario reported `push-protected-guard: the coordinator's push to main (attempt 1) was {... 'permissionDecision': 'deny' ...}, not ask.`, carrying the declared signature `push-protected-guard:`.
    - M1.green: pass. With `push-protected:` read by the hook, `sessionRole`, and the `ask` output, the coordinator's push to main returns `ask` naming `main` twice with the chat store unchanged, the `rtl` session is denied naming `iecc-pm`, `bypassPermissions` and `dontAsk` are each denied naming the mode, `claude/fix` passes, `release` is denied, and with only `push-protected:main` declared `release` is denied and `main` asked.
    - M2: pass. `npm test` reports `validation --all passed: baseline plus 256 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: the scenario feeds the shipped hook real `Bash` events with `permission_mode`, from two worktrees with real chat role bindings, and reads each decision and reason.
      - Scope check: `git status --short` adds the hook script to 1.1's files; `README.md` and `scripts/validate_plugin.py` are in this task's Touch.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/280 — what the host does with `ask` in `default`, `acceptEdits`, and `plan` is the documented prompt but was not observed here, and `bypassPermissions`/`dontAsk` are refused rather than measured, because the headless `claude -p` probe could not authenticate (F2). The issue stays open until a live session confirms the prompt.
    - Blocker: none
    - Reauthorizations: none

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
    - M2: the ADDED requirements are appended to both published specs, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f33cbfc8c12b6a5ab1ee3222788b40f95d864d9583f3ceb67dfc348888b71bdd
    - M1: pass. `node scripts/bump_version.js minor` moved every marker to 5.110.0 on top of `main` at 5.109.0 (#283). With the 5.110.0 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. Both ADDED requirements are appended to their published specs; `published-specs-validate-strictly` reports `34 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, both published specs carry their requirement with its scenarios, and the changelog names the issue, the decision, the refused modes, and what is still unobserved.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the two specs, all in Touch.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump to 5.110.0 reports `validation --all passed: baseline plus 256 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "accepted names: commit, push, push:<branch glob>, release, archive, continuation, issue:<owner>/<repo>, protocol-refresh, chat-reply:<group>, issue-close:<owner>/<repo>, cleanup:scratch" — `README.md` and `keel/config.yaml`, asserted by `scripts/validate_plugin.py`. Updated by: 1.1
- I2: "The ten names above are the whole vocabulary." — `README.md`. Updated by: 1.1

## Expectation Coverage

- E1: A repository can name a protected branch, optionally for one role, refused in the wrong form and reported (D1, D4). Covered by: 1.1
- E2: A push to it reaches the user as a per-command confirmation, never silently and never in a mode that cannot ask (D2, D3). Covered by: 1.2
- E3: The release carries it. Covered by: 2.1
