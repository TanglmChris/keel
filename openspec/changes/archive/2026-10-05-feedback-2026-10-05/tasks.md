# Tasks

## 1. Collected feedback

- [x] 1.1 Wording and catalog fixes from the sessions' feedback
  - Covers:
    - keel-chat-slack-bridge / The bridge runs unattended but stays visible and controllable / The session learns to mention the owner
    - D1
    - D2
    - D3
    - D4
    - D5
    - F1
    - F2
    - F3
    - F4
  - Read:
    - src/core/chat/notice.js
    - src/core/context.js
    - src/core/gates.js
    - src/core/agents.js
  - Touch:
    - src/core/chat/notice.js
    - src/core/context.js
    - src/core/gates.js
    - src/core/agents.js
    - assets/lenses/hardware.md
    - plugins/keel/skills/keel-tdd-or-test-first/SKILL.md
    - src/skills/keel-tdd-or-test-first/SKILL.md
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario chat-owner-mention` additionally requires the session-start notice to say a risk or decision goes in `its own message`. Fails with: `chat-owner-mention:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario a-coverage-claim-is-compared` additionally requires the close of an entry citing no identifier to warn with `D<n>, F<n>, A<n>, or Q<n>`. Fails with: `a-coverage-claim-is-compared:`
    - M3: `node scripts/run_python.js scripts/validate_plugin.py --scenario context-names-the-protocol-refresh` additionally requires the authorized Protocol line to say `committing it is a separate action`. Fails with: `M2 context`
    - M4: `node scripts/run_python.js scripts/validate_plugin.py --scenario collected-feedback-is-recorded` requires `keel agents codex` to show a pitfall naming the result file and a non-zero exit, the general pitfalls to name `pkill -f`, the bundled hardware lens to name tools that silently accept a missing signal, and the tdd skill to advise a `Fails with:` literal every red shares. Fails with: `collected-feedback-is-recorded:`
    - M5 (regression): `npm test` passes the baseline and every registered scenario.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:dad210064dbe85dc0feedc7a74ede04a31ca792050d19250357fed8bcb499c3e
    - Blocker: none
    - Reauthorizations: 2026-10-05 re-recorded after adding `src/skills/keel-tdd-or-test-first/SKILL.md` to Touch: the skill's canonical source lives there and the plugin copy is its projection, which the baseline compares. No evidence had been recorded yet.
    - M1: pass. `chat-owner-mention` reports `chat-owner-mention scenario passed.`
    - M1.red: fail. Before the change it reported `chat-owner-mention: the notice does not say a risk or decision goes in its own message: …`.
    - M1.green: pass. With the sentence added to `OWNER_RULE`, the scenario passes.
    - M2: pass. `a-coverage-claim-is-compared` reports `a-coverage-claim-is-compared scenario passed.`
    - M2.red: fail. Before the change it reported `a-coverage-claim-is-compared: the uncompared-entry warning does not name the identifiers that count; 'Expectation Coverage: compared 0 of 2 … 2 cited no expectation identifier and were not compared.'`.
    - M2.green: pass. With the report naming `D<n>, F<n>, A<n>, or Q<n>` and an example, the scenario passes.
    - M3: pass. `context-names-the-protocol-refresh` reports `context-names-the-protocol-refresh scenario passed.`
    - M3.red: fail. Before the change it reported `context-names-the-protocol-refresh M2 context does not say committing the refresh is a separate action: ['Protocol: … standing-authorized (authorize: protocol-refresh); run it before other work and leave the diff for the owner to commit']`.
    - M3.green: pass. With the line reading `leave the diff uncommitted: the authorization covers the refresh, and committing it is a separate action`, the scenario passes.
    - M4: pass. `collected-feedback-is-recorded` reports `collected-feedback-is-recorded scenario passed.`
    - M4.red: fail. Before the change it reported `collected-feedback-is-recorded: \`keel agents codex\` does not mention 'result file'.`
    - M4.green: pass. With the codex and general pitfalls, the hardware-lens sentence, and the tdd-skill paragraph (canonical `src/skills` copy and its plugin projection), the scenario passes, and `external-agent-catalog` still passes.
    - M5: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: each check reads the surface a session reads — the SessionStart notice, the change-close warning, the `keel context` Protocol line, and `keel agents codex` — plus the lens and skill files a session loads.
      - Scope check: `git status --short` lists the seven Touch paths plus `src/skills/keel-tdd-or-test-first/SKILL.md`, added to Touch by reauthorization, and this change's own directory.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/239 — whether `E<n>` should itself count as a compared identifier is left there.

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
    - openspec/specs/keel-chat-slack-bridge/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and the spec promotion. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/bump_version.js patch` moves every marker to 5.96.1, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes with the 5.96.1 section written.
    - M2: the MODIFIED requirement is promoted into `openspec/specs/keel-chat-slack-bridge/spec.md`, and `node scripts/run_python.js scripts/validate_plugin.py --scenario published-specs-validate-strictly` passes.
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:ee4cdf6e31529982db34a5b7e59c7f26d89f327176edc0c72447df002dbb9f82
    - Blocker: none
    - Reauthorizations: none
    - M1: pass. `node scripts/bump_version.js patch` moved every marker to 5.96.1. With the 5.96.1 section written, `version-alignment` reports `version-alignment scenario passed.`
    - M2: pass. The MODIFIED requirement replaces its published copy, keeping its seven scenarios; `published-specs-validate-strictly` reports `30 published specs validate strictly against openspec 1.14.0.`
    - Review:
      - Status: pass
      - Acceptance check: the markers agree, the promoted requirement carries the risk-in-its-own-message clause, and the changelog lists each fix with its issue.
      - Scope check: the bump touched the version-marker files in Touch, plus `keel/CHANGELOG.md` and the promoted spec, both in Touch.
      - Findings: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario.

## Change Evidence

- C1: pass. `npm test` after the bump reports `validation --all passed: baseline plus 236 scenarios, 1 skipped: output-survives-the-pipe.`

## Invalidates

- I1: "leave the diff for the owner to commit" — `src/core/context.js` protocol-refresh line. Updated by: 1.1

## Expectation Coverage

- E1: What the sessions reported on 2026-10-05 that Keel can fix by wording or catalog is fixed (D1, D2, D3, D4, D5). Covered by: 1.1
- E2: The release carries it. Covered by: 2.1
