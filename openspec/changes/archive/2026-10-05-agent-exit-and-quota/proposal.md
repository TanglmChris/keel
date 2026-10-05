## Why

Issue #221, from reading nine codex runs in rtl_ppa_prj on 2026-10-05:
- Four runs started in parallel at 17:02, and three hit the usage limit within five minutes. The catalog says codex has a quota, not that parallel runs share one.
- Only one run recorded its exit status. With no status, the only account of whether a run ended normally is the agent's own report, which the delegation rules treat as a claim. A successful run (codex_a2, `exit=0`) read as a failure because it left no `LAST.md`.

## What Changes

- The command `keel agents brief` prints runs the filled template in a subshell and writes its exit status to `<result>.exit`, and the output names that file.
- The codex catalog entry gains a dated pitfall: parallel runs under one account share one quota.

## Capabilities

### Modified Capabilities
- `keel-external-agents`: the brief's printed command records the exit status.

## Impact

`src/core/agents.js`, `scripts/validate_plugin.py`, both READMEs where they describe the brief, the published spec, and the changelog.
