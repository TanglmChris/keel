# A running session keeps the plugin state it started with, so a marketplace switch leaves the write guard off

Date: 2026-07-27. Found while implementing the `record-allows-reauthorization` change.

## Finding

`~/.claude/settings.json` was migrated from the old `relay@relay-marketplace` plugin to `keel@keel-marketplace` earlier in the same session. The file is correct:

```json
"enabledPlugins": { "keel@keel-marketplace": true },
"extraKnownMarketplaces": {
  "keel-marketplace": { "source": { "source": "directory", "path": "...\\skill_v3" } }
}
```

But the session that performed the migration had already loaded its plugins at start, and it kept them. Two observable symptoms confirmed it, both after the settings write:

- the SessionStart hook still injected `Relay hook fallback: the relay CLI is missing or incompatible with this plugin`, which is the *relay* plugin's hook, not keel's;
- the agent type listing still offered `relay:relay-single-task-goal-claude` and `relay:relay-single-task-goal-codex`.

The consequence that matters: keel's PreToolUse write guard is a plugin hook, so during that session `keel gate task-start` wrote a valid `keel/guard.json` and **nothing enforced it**. The gate reported `Guard: started` truthfully — the manifest was written — while no tool call was ever checked against it.

Scope for the affected task was proved instead by `keel gate task-complete --base HEAD`, which attributes working-tree paths against Touch and does not depend on the hook.

## Why this is worth recording

This is not a keel defect: a plugin host loading plugins once per session is ordinary. It is a **gap between what `Guard: started` claims and what an author can conclude from it.** The guard status reports whether the manifest was written, which is a keel-side fact, and says nothing about whether the runtime hook that consumes it is live — a target-side fact. `keel --doctor` already treats unverified runtime activation as `manual` rather than assuming it from the target name; the guard's own status line does not carry the same caution.

Two candidate directions, neither decided:

- have `keel guard status` state plainly that enforcement depends on a runtime hook it cannot observe, so `started` is never read as `enforcing`;
- have `keel --doctor` report when the enabled-plugin declaration in the host's settings names a marketplace whose hooks are not the ones currently resident, which is detectable only from the target side and may not be reachable at all.

## Durable owner

GitHub issue: https://github.com/TanglmChris/keel/issues/14

## Why this file exists rather than a bare issue link

`keel gate task-complete` does not accept a GitHub issue URL as a Review `Findings` owner; `findingOwnerIsDurable` (`src/core/gates.js`) accepts a `Discard reason:`/`Discard rationale:` prefix, a `keel/archive/…` path, or an existing `openspec/changes/…` artifact. This file is the gate-recognized pointer; the issue owns the substance. The mismatch is issue #12, and the operational rule is in the Project Conventions section of `AGENTS.md`.
