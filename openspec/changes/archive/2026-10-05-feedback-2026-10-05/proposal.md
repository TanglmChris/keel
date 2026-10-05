## Why

On 2026-10-05 the owner asked me to collect how the sessions use Slack and external models and to improve the workflow from it. rtl_ppa_flow gathered feedback from eight rtl_ppa_prj sessions. This change takes the items that are wording or catalog fixes. Larger asks are owned by issues #236, #240, #241, #242, #243, and work for rtl_ppa_prj itself goes back to rtl_ppa_flow.

## What Changes

- The Slack owner rule adds: a risk or decision goes in its own message with `@owner`, not inside a status update (PM's question).
- `keel context`'s protocol-refresh line says the authorization covers the refresh, not the commit (#238).
- The Expectation Coverage report names the identifiers that make an entry compared and shows where to cite one (#239).
- The tdd skill advises declaring a `Fails with:` literal that every red of the check shares, such as a scenario or test label, rather than one exception type (#237, owner chose guidance only).
- The codex catalog adds a pitfall: have the brief write its result file before tidying up, and on a non-zero exit read the products before calling it a failure (design's run hit its quota while tidying up). General pitfalls add: kill a delegate by PID or its own output directory, never `pkill -f <pattern>`, which killed other sessions' processes twice.
- The hardware lens adds: tools that silently accept a broken reference (Verilator binds an SVA to a missing signal as a constant) need a check of their own, since a passing run proves nothing about them.

## Capabilities

### Modified Capabilities
- `keel-chat-slack-bridge`: the owner rule separates risks and decisions from status.

## Impact

`src/core/chat/notice.js`, `src/core/context.js`, `src/core/gates.js`, `src/core/agents.js`, `assets/lenses/hardware.md`, `plugins/keel/skills/keel-tdd-or-test-first/SKILL.md`, `scripts/validate_plugin.py`, the published spec, and the changelog.
