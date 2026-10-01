## 1. Codex hook execution and receiving

- [x] 1.1 Declare executable Codex hooks and deliver non-consuming mail notices
  - Covers:
    - keel-native-plugin-package / Codex declares executable host-compatible hook commands
    - keel-codex-receiving / Codex receives a non-consuming mailbox notice
    - D1
    - D2
  - Touch:
    - plugins/keel/.codex-plugin/plugin.json
    - plugins/keel/hooks/codex.json
    - plugins/keel/scripts/codex-mail-hook.js
    - scripts/validate_codex_receiving.py
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: `node scripts/run_python.js scripts/validate_codex_receiving.py` exercises startup, next-input, repeated notices, empty/unbound worktrees, provider failure/invalid output/timeout and unchanged inbox bytes through real CLI and hook subprocesses.
    - M2 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario native-plugin-manifests` preserves Claude packaging.
    - M3 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario mailbox-cli` preserves mailbox behavior.
    - M4 (regression): `node scripts/run_python.js scripts/validate_plugin.py --scenario mailbox-claude-hooks` preserves Claude receiving.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:4ec49f9f31008efb709bebde7dbe3a54ea4e74364450e734de4ae52fc15ceef1
    - M1: Passed real CLI/hook subprocess checks; native Codex 0.159.3 hooks/list also discovered four complete commands from hooks/codex.json, all untrusted after isolated install.
    - M1.red: Exit 1 before implementation, AssertionError: Codex still uses the args-only shared hooks. M1 was unchanged by command-name reauthorizations.
    - M1.green: Exit 0; startup/next-input, repeated non-consuming notices, quiet inboxes and failure fallback passed. All mailbox bytes preserved until explicit read.
    - M2: Exit 0, native-plugin-manifests scenario passed in byte-matched clean /private/tmp/keel-codex-validation with npm_config_cache=/private/tmp/keel-codex-npm-cache; root nested Claude worktrees otherwise pollute baseline scanning.
    - M3: Exit 0, mailbox-cli scenario passed in the same clean snapshot.
    - M4: Exit 0, mailbox-claude-hooks scenario passed in the same clean snapshot.
    - Review:
      - Status: pass
      - Acceptance check: Real CLI sends and explicit reads, hook subprocesses and native discovery prove non-consuming notices, supported event/context shape, executable paths and trust preservation. Provider boundary failures include invalid JSON, invalid shape, exit 1/2 and timeout. No mail bodies are injected.
      - Scope check: Product diff limited to the five Touch paths. Claude manifests/shared hooks, mailbox storage/CLI and capability declarations are unchanged. Memory searched by Codex hook/receipt/default-discovery symptoms; no matching stale memory was found.
      - Findings: Resolved here: M1 proves complete Codex script commands and receiving hooks. Eventual group notice provider and @ formatting remain owned by https://github.com/TanglmChris/keel/issues/187.
    - Blocker: none
    - Reauthorizations: Corrected scenario names and split invocations after inspecting the actual validator CLI; acceptance and Touch unchanged. All green checks rerun under the new fingerprint; M1 red belongs to the unchanged M1 check before implementation.

## 2. Real runtime and Full-mode acceptance

- [x] 2.1 Exercise isolated Codex delivery and consumer Full flow, then document bounded evidence
  - Covers:
    - keel-codex-receiving / Codex runtime acceptance distinguishes discovery from execution
    - F1
    - F2
    - F3
    - D3
    - D4
    - D5
  - Touch:
    - README.md
    - docs/codex-validation.md
    - scripts/validate_codex_receiving.py
  - Verify:
    - Strategy: evidence-first
    - Reason: This slice records native runtime and consumer workflow evidence plus instructions; the receiving implementation is proved by 1.1's red-green check.
    - M1: `node scripts/run_python.js scripts/validate_codex_receiving.py --native` installs into a scratch CODEX_HOME, verifies native discovery/trust skip and context delivery at the deterministic model boundary without another agent owning Keel.
    - M2: `node scripts/run_python.js scripts/validate_codex_receiving.py --consumer` creates a clean consumer and exercises proposal, task-start, a real behavior assertion, Review, task-complete and change-close through the real Keel CLI.
    - M3: `npm test` and `keel openspec validate codex-receiving-and-validation --strict` preserve the full regression suite and validate the delta.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:34f042554be28a502c8a241f9ad8e724559eedf26332d83f801f68d9622a1fd2
    - M1: Exit 0 on Codex CLI 0.159.3. Native discovery reported four complete commands and untrusted definitions; untrusted execution had no mailbox context; isolated source-vetted invocation delivered disposable idle projection plus both notices to a local captured Codex request. Inbox bytes and persisted trust unchanged; no model executed.
    - M2: Exit 0. Clean Codex init and doctor passed, then proposal/spec/tasks, recorded task-start, MODULE_NOT_FOUND red, exact hello keel green, semantic Review, task-complete and change-close passed. No Codex guard was automatically written.
    - M3: Final clean-snapshot npm test exit 0: baseline plus 198 scenarios, 1 skipped output-survives-the-pipe (macOS F_SETPIPE_SZ). Delta strict validation exit 0. Initial nested-worktree scan, unstaged packed-file and sandboxed dependency-install failures were isolated, staged or rerun with temporary network-enabled configuration; no product acceptance weakened.
    - Review:
      - Status: pass
      - Acceptance check: Native runtime reached its actual model request boundary with the expected projection and metadata while leaving mail and trust untouched; clean consumer and the current Codex agent exercised the complete specified flow. Documentation clearly separates discovery, source-vetted execution and personal activation, and retains manual enforcement claims.
      - Scope check: Only README.md, docs/codex-validation.md and the test harness changed in this slice; disposable installations, clones, caches and local request capture were temporary. No personal host configuration, other session worktree or security capability declaration was modified.
      - Findings: Group/@/relative-time notice provider remains owned by https://github.com/TanglmChris/keel/issues/187. Discard reason: This delivery deliberately does not alter the baseline scanner's handling of nested worktrees or validator multi-scenario argument parsing; the clean snapshot and separate invocations supplied complete evidence without changing that unrelated behavior.
    - Blocker: none
    - Reauthorizations: none

## 3. Reviewable repository snapshot

- [x] 3.1 Commit the verified Codex adaptation on its review branch
  - Mode: repo-action
  - Covers:
    - E5: Commit the verified #178/#183 implementation and evidence on codex/codex-receiving-and-validation for pull-request review; do not merge or release in this task.
  - Touch:
    - none
  - Verify:
    - Strategy: evidence-first
    - Reason: This is a repository commit of already verified behavior, not a new behavior that can fail first.
    - M1: `git log -1 --format=%s` names the Codex hook/receiving commit; `git show --name-only --format= HEAD` includes the receiving adapter, explicit configuration, behavior checks and durable acceptance record.
    - M2: `git diff --exit-code HEAD -- README.md docs/codex-validation.md plugins/keel/.codex-plugin/plugin.json plugins/keel/hooks/codex.json plugins/keel/scripts/codex-mail-hook.js scripts/validate_codex_receiving.py scripts/validate_plugin.py` proves the verified product snapshot is committed.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8a8787629c5b952293cdee12da318c36964177b72a45b6a5b916bbe99fe1e482
    - M1: git log prints Fix Codex hook execution and add mailbox receiving; git show lists the adapter, Codex hook configuration, public-interface checks, docs/codex-validation.md and OpenSpec authority/evidence.
    - M2: Exit 0; git diff HEAD for every verified product path is empty.
    - Review:
      - Status: pass
      - Acceptance check: The review branch carries the verified implementation and acceptance record in a commit; public Git commands prove the product snapshot is unchanged.
      - Scope check: Repository action only; no product files changed during this task. Task evidence is the permitted record layer. No merge or release executed.
      - Findings: none
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- I4: "codex manifest declares an unsupported hooks field; default discovery must load hooks/hooks.json" — scripts/validate_plugin.py. Updated by: 1.1
- I1: "Codex also loads" and "declares only SessionStart and PreToolUse" — historical default discovery wording in the plugin package spec. Durable owner: https://github.com/TanglmChris/keel/issues/187 (its accepted task group 7 updates the shared mailbox/plugin/protocol wording; this change adds an explicit Codex override requirement).
- I2: "Codex's receiving hooks" as a non-goal — historical #180 design. Discard reason: Historical source describes #180's scope correctly; #183 is this change's explicit receiving owner.
- I3: "skills and hooks" without explaining Codex trust/reload — README.md. Updated by: 2.1

## Expectation Coverage

- E1: Native complete command execution with retained continuity and guard declarations (F1, D1). Covered by: 1.1, 2.1
- E2: Non-consuming startup/next-input mail delivery and failure fallback (D2). Covered by: 1.1, 2.1
- E3: Bounded runtime/version/trust/manual and consumer Full-flow evidence (F2, F3, D3, D4). Covered by: 2.1
- E4: Group/@/relative-time notice interface and semantics (D5). Durable owner: https://github.com/TanglmChris/keel/issues/187
- E5: Reviewable committed snapshot for #178/#183. Covered by: 3.1
