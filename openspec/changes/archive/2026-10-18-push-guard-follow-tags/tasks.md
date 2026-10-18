# Tasks

## 1. A push that carries tags is a tag push

- [x] 1.1 The push guard reads `--follow-tags`, `push.followTags`, and `GIT_CONFIG*` assignments
  - Covers:
    - keel-touch-write-guard / A push that carries tags is a tag push / A granted branch pushed with --follow-tags is refused
    - keel-touch-write-guard / A push that carries tags is a tag push / Config that carries tags is refused the same way
    - keel-touch-write-guard / A push that carries tags is a tag push / Turning tag carriage off restores the branch push
    - keel-touch-write-guard / A push that carries tags is a tag push / The coordinator is asked about main with its tags
    - keel-touch-write-guard / A push that carries tags is a tag push / Environment config is not read past
    - D1
    - D2
    - D3
    - D5
  - Read:
    - plugins/keel/scripts/pretooluse-guard.js
    - scripts/validate_plugin.py
  - Touch:
    - plugins/keel/scripts/pretooluse-guard.js
    - scripts/validate_plugin.py
    - README.md
    - keel/config.yaml
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario push-guard-follow-tags` feeds the real hook script `Bash` events in a real repository: with `push:flow-*`, `git push --follow-tags origin flow-release` is denied naming `--follow-tags` and `--no-follow-tags`; with `push.followTags=true` in the repository config a plain `git push origin flow-release` is denied naming `push.followTags`, and `git -c push.followTags=false push origin flow-release` passes; with it unset, `git -c push.followTags=true push origin flow-release` is denied and `git push --follow-tags --no-follow-tags origin flow-release` passes; `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=push.followTags GIT_CONFIG_VALUE_0=true git push origin flow-release` is denied naming `GIT_CONFIG_COUNT`; with `push-protected:main@iecc-pm` added, `git push --follow-tags origin main` from `iecc-pm` returns `ask` naming `main` and `annotated tags`, and from `rtl` is denied naming `iecc-pm`; with no push scope declared, the `--follow-tags` push is not intercepted. Fails with: `--follow-tags push to a granted branch was allowed`
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario push-branch-guard`, `--scenario push-protected-guard`, and `--scenario push-guard-redirects` still pass.
    - M3 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:a6caa9f636104cdfbbdad9017fbcb1db4f590894dd1e915dbe92d5fa91dc9217
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario push-guard-follow-tags` reports `push-guard-follow-tags scenario passed.`
    - M1.red: fail. With the scenario written first, it reported `push-guard-follow-tags: --follow-tags push to a granted branch was allowed, not deny ('git push --follow-tags origin flow-release'): {'permissionDecision': 'pass'}`, carrying the declared signature `--follow-tags push to a granted branch was allowed`.
    - M1.green: pass. With `pushTargets` reporting tag carriage (`--follow-tags` last wins over `--no-follow-tags`, else `git config --type=bool --get push.followTags` with the command's `-c` pairs), `findPushes` reading assignments through `env` and refusing `GIT_CONFIG*` and a shell-expanded `-c`, and `checkPushes` denying a tag-carrying push unless every target is `push-protected`, the scenario passed.
    - M2: pass. `--scenario push-branch-guard`, `--scenario push-protected-guard`, and `--scenario push-guard-redirects` each report `scenario passed.`
    - M3: pass. `npm test`: `validation --all passed: baseline plus 284 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: the scenario feeds the real hook script real `Bash` events in a real repository and worktrees bound to `iecc-pm` and `rtl`, covering every scenario of the ADDED requirement: `--follow-tags` denied, repository and `-c` `push.followTags` denied, `--no-follow-tags` and `-c push.followTags=false` restore the push, the coordinator is asked naming `main` and annotated tags while `rtl` is denied naming `iecc-pm`, `GIT_CONFIG_COUNT` denied, and nothing is intercepted without a push scope.
      - Scope check: `git status --short` lists `README.md`, `keel/config.yaml`, `plugins/keel/scripts/pretooluse-guard.js`, `scripts/validate_plugin.py`, and this change's directory, all in Touch or the record layer.
      - Findings:
        - Resolved here: M1 — reading assignments only before `env`/`command` prefixes let `env FOO=1 git push origin main` skip the guard entirely (checked against the 5.138.0 guard: allowed; now denied naming `main`). The prefix loop now reads assignments and prefixes interleaved; the scenario asserts it, and `env GIT_CONFIG_COUNT=…` is denied too.
        - Resolved here: M1 — a shell-expanded `git -c "$CFG"` could set `push.followTags` out of sight; it is now denied as undetermined, and the scenario asserts it.
        - Discard reason: after a `cd`, `push.followTags` is read from the event's cwd, the same assumption the guard already makes for reading `keel/config.yaml`; `--follow-tags` on the command line is caught either way, and a guard that refused every `cd … && git push` would break the common form for a rare config.
    - Blocker: none
    - Reauthorizations: none

## 2. Release

- [x] 2.1 Release and promote the spec
  - Covers:
    - E2
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion; the behavior is proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js minor` moves every marker to the next minor version, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with that section written.
    - M2: the ADDED requirement joins `keel-touch-write-guard` and the MODIFIED one replaces its counterpart, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8266ec313ae67499f1ea9d0886799b63077ffc3f4a93e8062cb76103726cb3fb
    - M1: `node scripts/bump_version.js minor` moved every marker 5.138.0 → 5.139.0; with the "The push guard sees tags carried by a branch push" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the ADDED requirement joined `keel-touch-write-guard` after the protected-push requirement, whose MODIFIED text replaced it; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "A target matching a `push:` glob MUST pass;" with no exception for a push carrying tags — `openspec/specs/keel-touch-write-guard/spec.md`. Updated by: 2.1
- I2: "refuses one to any other branch, or one whose target it cannot tell — `--all`, `--mirror`, `--tags`", the README paragraph that says nothing of `--follow-tags` — `README.md`. Updated by: 1.1
- I3: "the Claude write guard refuses a `git push` to any other branch (#257)", the config comment that says nothing of tags — `keel/config.yaml`. Updated by: 1.1

## Expectation Coverage

- E1: A session holding only a `push:` grant cannot publish annotated tags by carrying them on a branch push; the coordinator can still push main with its tags under the user's approval (#327, D2). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
