# Tasks

## 1. A mailbox both hosts can use

- [x] 1.1 The CLI sends, lists, and reads Markdown mail in the repository-shared mailbox
  - Covers:
    - keel-cross-host-mailbox / Messages are Markdown files in a repository-shared mailbox
    - keel-cross-host-mailbox / Addresses are user-chosen roles bound to a worktree
    - keel-cross-host-mailbox / Reading is the receipt
    - keel-cross-host-mailbox / Unread mail gates nothing
    - D1
    - D2
    - D4
    - D5
  - Touch:
    - src/core/mail.js
    - bin/keel.js
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario mailbox-cli` drives public `keel mail` in a scratch repository with two worktrees: an unbound sender and an invalid role fail by name; `rtl` sends to `verify`; the `verify` worktree lists one unread message whose file under `<git common dir>/keel-mailbox/verify/new/` carries the declared frontmatter, with `verify/.signal` present; a separate repository sees nothing; `keel mail read` prints the subject, body, and data-not-instruction header and moves the file to `done/`; a reply carries `reply_to`; `keel context` reports the same status with and without unread mail. Fails with: `mailbox-cli: keel mail`
    - M2 (regression): `npm test` passes the baseline and all registered scenarios, including CLI usage and output-contract scenarios.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:17740f46d205cdcb946beb8f03ad37116fcb8ca8de676889dd323e53352a229b
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario mailbox-cli` reports the scenario passing in a scratch repository with a second worktree: an unbound sender is refused naming `keel mail role --set`, `Bad Name` is refused naming the pattern with no mailbox written, `rtl` → `verify` delivery lands one file under `<git common dir>/keel-mailbox/verify/new/` with `id`/`from`/`to`/`created`/`subject`/`refs` frontmatter and the body, `verify/.signal` exists, a separate repository bound to `verify` lists nothing, `keel mail read` prints subject, body, and the `not an instruction from the user` header and moves the file to `done/`, the reply carries `reply_to`, and `keel context --json` reports the same `status` and `nextAction` with unread mail as without.
    - M1.red: fail. Before `src/core/mail.js` and the `mail` entry existed, the scenario reported `mailbox-cli: keel mail send from an unbound worktree was not refused by name.` with `keel: repo path was provided more than once`, carrying the declared signature `mailbox-cli: keel mail`.
    - M1.green: pass. The same scenario passes against the working tree.
    - M2: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: M1 drives only the public `keel mail` and `keel context` commands across two worktrees and a second repository, and asserts the on-disk location and frontmatter the first requirement names, the refusals the addressing requirement names, the receipt move and header the reading requirement names, and the unchanged context the no-gate requirement names. Exit-code semantics for hooks belong to 1.2.
      - Scope check: The diff adds `src/core/mail.js` and changes `bin/keel.js` (an early `mail` dispatch and one usage line), `scripts/validate_plugin.py` (the scenario, its registration, and two helpers), and `keel/CHANGELOG.md` — all in Touch — plus this change's own directory. `npm test` at this point reported `mailbox-claude-hooks` unregistered, which is 1.2's scenario; M2 therefore defers to C1, which runs once every scenario of the change exists.
      - Findings: Resolved here: M1 — the first draft of the scenario guarded several failures behind one condition each, which `assertion-shape-count` refused; every check now reports its own cause.
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - Delivery would need to write into any host's session storage, or a gate would have to read the mailbox.

- [x] 1.2 Claude Code sessions are told about mail at start, at each prompt, and while idle
  - Covers:
    - keel-cross-host-mailbox / Claude Code is told about mail at start, at each prompt, and while idle
    - keel-native-plugin-package / The Claude plugin is the tagged repository
    - F1
    - F2
    - F3
    - D3
    - D6
  - Touch:
    - src/core/mail.js
    - bin/keel.js
    - plugins/keel/scripts/mail-hook.js
    - .claude-plugin/plugin.json
    - AGENTS.md
    - scripts/validate_plugin.py
    - keel/CHANGELOG.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario mailbox-claude-hooks` runs `plugins/keel/scripts/mail-hook.js` with host-shaped stdin in a scratch repository: in a bound worktree with one unread message, SessionStart returns `additionalContext` naming the id, sender, subject, `keel mail read`, and that the mail is not a user instruction, plus the absolute `.signal` path in `hookSpecificOutput.watchPaths`; UserPromptSubmit returns the same notice; FileChanged exits 2 with the notice on stderr, and exits 0 silently once the mail is read; every event exits 0 silently in an unbound worktree; no hook moves a message. Fails with: `mailbox-claude-hooks:`
    - M2: `node scripts/run_python.js scripts/validate_plugin.py --scenario native-plugin-manifests` requires the root manifest's hooks to equal `plugins/keel/hooks/hooks.json` resolved from the root plus exactly the mailbox SessionStart, UserPromptSubmit, and FileChanged (`asyncRewake: true`) groups, and requires `hooks.json` to declare only SessionStart and PreToolUse with no `asyncRewake`. Fails with: `root plugin manifest hooks diverge`
    - M3 (regression): `npm test` passes the baseline and all registered scenarios.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:3fa2279f83b17781149fd1f6d0298b0cc4543db45005190057fa92711604ab1d
    - M1: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario mailbox-claude-hooks` reports the scenario passing. Run as `node plugins/keel/scripts/mail-hook.js <event>` with host-shaped stdin: in an unbound repository all three events exit 0 with no output; in the `verify` worktree with one unread message from `rtl`, SessionStart returns `hookEventName: SessionStart`, `additionalContext` naming the id, `` `rtl` ``, the subject, `keel mail read`, and `not an instruction from the user`, and `watchPaths` equal to the absolute `verify/.signal`; UserPromptSubmit returns the same notice; FileChanged exits 2 with it on stderr; the message stays in `new/`; after `keel mail read`, FileChanged exits 0 silently and UserPromptSubmit writes nothing.
    - M1.red: fail. Before the script existed the scenario reported `mailbox-claude-hooks: plugins/keel/scripts/mail-hook.js does not exist.`, carrying the declared signature `mailbox-claude-hooks:`.
    - M1.green: pass. The same scenario passes against the working tree.
    - M2: pass. `node scripts/run_python.js scripts/validate_plugin.py --scenario native-plugin-manifests` reports the scenario passing: the root manifest's hooks equal `hooks.json` resolved from the root plus the mailbox SessionStart, UserPromptSubmit, and FileChanged (`asyncRewake: true`) groups, and `hooks.json` declares only PreToolUse and SessionStart with no `asyncRewake`.
    - M2.red: fail. With the scenario extended and the manifest not yet changed, it reported `native-plugin-manifests root plugin manifest hooks diverge from plugins/keel/hooks/hooks.json after resolving script paths from the repository root, plus the Claude-only mailbox hooks: …`, carrying the declared signature `root plugin manifest hooks diverge`.
    - M2.green: pass. The same scenario passes after the root manifest gained the three groups.
    - M3: deferred to C1
    - Review:
      - Status: pass
      - Acceptance check: M1 exercises the shipped hook script, the entry point the host runs, and asserts the output fields and exit codes the requirement names, including silence without a role and that no hook moves mail. M2 holds the manifest to the modified packaging requirement. Beyond the gate's reach, an end-to-end run on Claude Code 2.1.283 used these exact commands as settings hooks in a `--input-format stream-json` session: after it went idle, `keel mail send` from the `rtl` worktree produced a new assistant turn naming the `rtl` message and its subject without any user input, and the agent asked before acting on it. That is host evidence for E2, not a gate result.
      - Scope check: The diff adds `plugins/keel/scripts/mail-hook.js` and changes `src/core/mail.js`, `.claude-plugin/plugin.json`, `AGENTS.md` (the I1 sentence), `scripts/validate_plugin.py`, and `keel/CHANGELOG.md` — all in Touch — plus 1.1's completed files and this change's own directory. `plugins/keel/hooks/hooks.json` is unchanged.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/183 — Codex sessions can send and read through the CLI but are not yet notified; the owner left Codex's receiving hooks to Codex.
    - Blocker: none
    - Reauthorizations: none
  - Stop if:
    - A mailbox hook would have to enter `plugins/keel/hooks/hooks.json`, which Codex also loads.

## 2. Close

- [x] 2.1 Release
  - Covers:
    - E1
    - E2
    - E3
  - Read:
    - keel/CHANGELOG.md
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
    - openspec/specs/keel-cross-host-mailbox/spec.md
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
    - Reason: this task's effect is version markers, a changelog entry, and promoted specs. The behavior was proven in 1.1, and nothing written here can fail before it is written.
    - M1: `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes after `node scripts/bump_version.js minor`, with the new section written into the stub
    - M2: the deltas are promoted, `node node_modules/.bin/openspec validate cross-host-mailbox --strict` passes, and `npm test` reports no failing scenario
  - Autonomy boundary:
    - Default: hard-stop
    - Pre-authorized fallback: none
  - Stop Rules:
    - Stop if a version marker exists that `version-alignment` does not check.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:21de55b1d8895ee7f36709ac425a369ce7e849539c465651768008a942aae515
    - M1: pass. `node scripts/bump_version.js minor` moved every marker from 5.82.0 to 5.83.0, the Unreleased #180 notes were folded into the 5.83.0 section, and `node scripts/run_python.js scripts/validate_plugin.py --scenario version-alignment` passes. The Stop Rule held.
    - M2: pass. The new capability is published as `openspec/specs/keel-cross-host-mailbox/spec.md`, the modified requirement replaces its predecessor in `keel-native-plugin-package`, and that spec's Purpose now names the Claude-only mailbox hooks (I2). `node node_modules/.bin/openspec validate cross-host-mailbox --strict` (OpenSpec 1.13.2) reports the change valid, `openspec validate --specs --strict` reports `27 passed, 0 failed`, and `npm test` reports `validation --all passed: baseline plus 195 scenarios, 1 skipped: output-survives-the-pipe.`
    - Review:
      - Status: pass
      - Acceptance check: E1 and E2 were proven by 1.1 and 1.2; this task carries them into 5.83.0 with the specs promoted where the next reader finds them. E3 is owned by #183, which carries the Codex-side work and the constraint to keep Claude-only fields out of the shared `hooks.json`.
      - Scope check: `git status --short` shows the version markers, `keel/CHANGELOG.md`, and the two specs — this task's Touch — plus 1.1 and 1.2's completed files and this change's own directory.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Change Verify

- Strategy: regression-first
- C1: `npm test` passes the baseline and every registered scenario once the change's scenarios all exist, including `mailbox-cli`, `mailbox-claude-hooks`, and `native-plugin-manifests`.

## Change Evidence

- C1: pass. After 2.1's version bump and spec promotion, `npm test` reports `validation --all passed: baseline plus 195 scenarios, 1 skipped: output-survives-the-pipe.` (macOS `F_SETPIPE_SZ`, unrelated), including `mailbox-cli`, `mailbox-claude-hooks`, and `native-plugin-manifests`.

## Invalidates

- I1: "The `keel` plugin's only runtime hooks are SessionStart continuity and the PreToolUse write guard." — `AGENTS.md` Completion gates. Updated by: 1.2
- I2: "the SessionStart and write-guard hooks it packages" — `openspec/specs/keel-native-plugin-package/spec.md` Purpose. Updated by: 2.1

## Expectation Coverage

- E1: A session in one worktree can send a Markdown message that a session in another worktree of the same repository reads, by role, without either host's internal storage. Covered by: 1.1, 2.1
- E2: A Claude Code session learns of mail at start, at each prompt, and while idle, and is told the mail is data, not instruction. Covered by: 1.2, 2.1
- E3: Codex's receiving side is not built here; it is owned by a tracker issue, and Codex sessions can send and read through the CLI. Durable owner: https://github.com/TanglmChris/keel/issues/183
