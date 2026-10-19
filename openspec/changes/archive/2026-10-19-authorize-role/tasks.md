# Tasks

## 1. A scoped authorization may name the roles it applies to

- [x] 1.1 Accept `@<role pattern>` on every scoped entry; filter by the session's role; enforce it on push; list grants per role
  - Covers:
    - keel-standing-authorization / A scoped authorization may name the roles it applies to / Grants follow the role
    - keel-standing-authorization / A scoped authorization may name the roles it applies to / A malformed role pattern is refused
    - keel-standing-authorization / A protected branch is pushed only with the user's approval of that push / A protected branch is reported
    - D1
    - D2
    - D3
    - D4
  - Read:
    - src/core/config.js
    - plugins/keel/scripts/pretooluse-guard.js
    - bin/keel.js
    - scripts/validate_plugin.py
  - Touch:
    - src/core/config.js
    - plugins/keel/scripts/pretooluse-guard.js
    - bin/keel.js
    - scripts/validate_plugin.py
    - README.md
    - keel/config.yaml
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario authorize-role-scoped` declares `commit`, `push:design-*@rtl`, `push:review-*@ver*`, `issue:acme/widgets@rtl`, `chat-reply:soc@verify` and `push-protected:main@rt*` with `rtl` and `verify` bound, then runs the real `keel --doctor` in each worktree: rtl's reports `issue` authorized and `chat-reply` not authorized, verify's the reverse, and both print a `roles` line per bound role naming its entries. The real guard hook allows `git push origin design-x` from rtl and refuses it from verify naming `rtl`; allows `review-x` from verify; refuses `design-x` for `KEEL_CHAT_ROLE=spec`; asks for `main` from rtl and refuses it from verify. `issue:acme/widgets@Not A Role` makes `keel --doctor` exit non-zero naming the entry. Fails with: `issue:acme/widgets@rtl`
    - M2 (regression): `npm test` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:87a284c2910876dcf22f23163c1403ea0411d352f0a3b06ce427ac1cb01704de (keel 5.160.0)
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario authorize-role-scoped` reports `authorize-role-scoped scenario passed.`
    - M1.red: fail. With the scenario written first and the code unchanged: `authorize-role-scoped: rtl's doctor does not report issue authorized: …`, whose doctor output reads `authorize: failed - keel/config.yaml declares unrecognized actions: push:design-*@rtl, push:review-*@ver*, issue:acme/widgets@rtl, chat-reply:soc@verify, push-protected:main@rt*`, carrying the declared signature.
    - M1.green: pass. With `@<role pattern>` split off every scope and checked, `readStandingAuthorization` filtering by the session's role (`otherRoles` for the rest, `push-protected` kept as before), the guard's `push:<glob>@<role>` and role-glob `push-protected`, and doctor's `roles` lines, the scenario passed. Two mutations each turned it red: no role filter in `readStandingAuthorization` (`rtl's doctor reports chat-reply, another role's grant`), and a guard that ignores the role (`verify pushing rtl's design branch was {'permissionDecision': 'pass'}, not deny.`). With kaiwu-ip's real `authorize:` block, plus `@kaiwu-design-*` on `push:worktree-*` and `@kaiwu-review-*` on `push:cbb_dmc_iecc-review-r*`, the real hook let only the matching role push each of those branches, let every role push the unlimited `flow-*`, and refused `kaiwu-flow` on both limited ones.
    - M2: pass. `npm test`: `validation --all passed: baseline plus 303 scenarios, 1 skipped: output-survives-the-pipe.` (exit 0), run after the last code edit.
    - Review:
      - Status: pass
      - Acceptance check: through the real doctor and the real guard hook: each bound role sees only its own `issue` / `chat-reply` grants and both `roles` lines; a design branch limited to `rtl` is allowed for rtl and refused for verify naming `rtl`; a `ver*` pattern grants verify; a role no entry names stays limited; `main@rt*` asks rtl and refuses verify; a malformed role pattern voids the declaration naming the entry.
      - Scope check: `git status --short` lists `README.md`, `bin/keel.js`, `keel/config.yaml`, `plugins/keel/scripts/pretooluse-guard.js`, `scripts/validate_plugin.py`, `src/core/config.js`, and this change's directory, all in Touch (as reauthorized) or the record layer.
      - Findings:
        - Discard reason: unscoped actions (`commit`, `archive`, …) take no role, as #378 asked only for the scoped ones; `commit@x` stays an unknown action, so it fails closed instead of being read as a grant.
    - Blocker: none
    - Reauthorizations:
      - 2026-10-19: added `keel/config.yaml` to Touch. Its comment lists the accepted forms, which gain `[@<role>]` (I1), and `continuation-docs` pins that comment; it was missed when Touch was authored.

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
    - openspec/specs/keel-standing-authorization/spec.md
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
    - M2: the delta requirements are promoted into `keel-standing-authorization`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:672b77e5c2b08914ca648a06d6c31ec19a5b720aa2197c93ed0ceb07dfc1cbd9 (keel 5.160.0)
    - M1: `node scripts/bump_version.js minor` moved every marker 5.160.0 → 5.161.0; with the "a scoped grant may name the roles it applies to" section written, `version-alignment scenario passed.` (exit 0).
    - M2: the delta requirements were promoted into `keel-standing-authorization`; `published-specs-validate-strictly scenario passed: 35 published specs validate strictly against openspec 1.14.0.` (exit 0).
    - Review:
      - Status: pass
      - Acceptance check: E2 — version markers, the changelog section and the published spec carry the change; both validator scenarios pass.
      - Scope check: changed files beyond task 1.1's are the version markers, `keel/CHANGELOG.md` and the published spec, all in Touch.
      - Findings: none.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I1: "accepted names: commit, push, push:<branch glob>, … push-protected:<branch glob>[@<role>]" — README.md, the `authorize:` example's comment, and the accepted forms `src/core/config.js` prints and `keel/config.yaml`'s comment, which gain `[@<role>]` on every scoped form. Updated by: 1.1
- I2: "Keel carries that scope to `keel --doctor` and to the compiled capsule" — README.md's standing-authorization section, which gains how a role pattern limits a grant. Updated by: 1.1

## Expectation Coverage

- E1: A capability's grants reach only that capability's sessions, and a push outside a session's grants is refused (#378; D1, D2, D3, D4). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
