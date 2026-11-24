## 1. Make hook review and output reliable

- [x] 1.1 Label Codex hooks and prove complete JSON output from the public hook executables
  - Covers:
    - D1
    - D2
    - D3
    - keel-codex-hook-runtime / Codex reports distinct Keel hook purposes
    - keel-codex-hook-runtime / Hook JSON survives output backpressure
  - Touch:
    - plugins/keel/hooks/codex.json
    - plugins/keel/scripts/session-start.js
    - plugins/keel/scripts/pretooluse-guard.js
    - scripts/validate_codex_receiving.py
    - docs/updating.md
  - Verify:
    - Strategy: vertical-tdd
    - M1: Assert the manifest lists all four distinct labels and run the native Codex fixture to verify discovery preserves each named command and event. Fails with: `Keel hook labels missing`
    - M2: Invoke the session start and PreToolUse scripts with native input, create a payload larger than an output pipe and delay draining. Assert parsed JSON, complete context and a complete deny decision respectively. Fails with: `hook response truncated`
    - M3 (regression): Run existing Codex receiving and write guard checks and review native trust guidance. Verify official 0.171.0 /hooks render source labels rows with the same field, and preserve live failure diagnosis in #559.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:1a81b23b30229a662125ffe725009b1c720743d79387005d4909e69eb62064b7 (keel 5.231.5)
    - M1: The local manifest and native hooks/list output agree on four distinct labels, original command identities and events. Codex 0.171.0 native test passes and the tagged upstream hooks_browser_status_messages snapshot shows labels as row text.
    - M1.red: The manifest test reported Keel hook labels missing, with all four original commands present and four null labels.
    - M1.green: All labels were found in the real Codex CLI 0.171.0 hooks/list probe. Untrusted hooks stayed inactive, and test mail remained unconsumed.
    - M2: Both actual hook programs returned parseable complete JSON when the reader drained the pipe late. The session projection preserved the final context marker, and the guard preserved the deny decision and last Touch item.
    - M2.red: SessionStart and PreToolUse independently failed with hook response truncated, at 65534 and 65536 decoded characters respectively. The first was fixed before measuring the second.
    - M2.green: python3 scripts/validate_codex_receiving.py reports complete SessionStart projection and PreToolUse verdict.
    - M3: The codex-receiving, touch-write-guard and push-branch-guard scenarios all pass. The native procedure and standalone guidance retain explicit hook review and identify which diagnostic fields to collect.
    - Review:
      - Status: pass
      - Acceptance check: The installed runtime exposes the exact labels and the public hook executables no longer truncate late-drained output, including a denied write. Definitions, matching, timeout, and trust semantics otherwise use the existing Codex runtime.
      - Scope check: Product changes are limited to the Codex manifest, two hook exit sites, the diagnostic guide and the existing validation file. Native tests used temporary homes and a loopback endpoint.
      - Findings: Resolved here: M2 proves complete hook responses under backpressure. Durable owner: https://github.com/TanglmChris/keel/issues/559 — the recurring live account symptom still needs an attributable native event.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Four distinct names appear in native review (D1). Covered by: 1.1
- E2: JSON remains whole under backpressure (D2). Covered by: 1.1
- E3: Report repeated live failures with provenance (D3). Durable owner: https://github.com/TanglmChris/keel/issues/559
