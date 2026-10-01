## Context

The owner authorized #178 and #183 in this conversation on 2026-10-01. #187 is being implemented on Claude's side and retains `keel mail` compatibility. This change owns Codex receiving and observed Codex acceptance only.

## Goals / Non-Goals

**Goals:** real Codex discovery and delivery at startup/next prompt, unchanged mail state, a reproducible consumer/full-flow record, and explicit trust/manual boundaries.

**Non-Goals:** idle wake-up without a verified native event, personal Codex configuration changes, automatic trust, group semantics, Slack, #186, changes to the existing guard's claimed enforcement.

## Decisions

- F1 — Codex CLI 0.159.3 on this machine exposes SessionStart and UserPromptSubmit; native `hooks/list` after an isolated 5.84.0 plugin install reports the existing handlers' command as `node`, omitting the separate `args`. Basis: local app-server JSON-RPC probe, 2026-10-01.
- F2 — Official [hooks documentation](https://learn.chatgpt.com/docs/hooks) documents additionalContext for both events, exact-definition trust review, and no FileChanged event. The [plugin packaging reference](https://developers.openai.com/plugins/build/plugins) supports a relative explicit `hooks` path in `.codex-plugin/plugin.json`, replacing default discovery. Basis: fetched 2026-10-01. Documentation proves contract availability, not activation on the user's session.
- F3 — The personal Codex plugin list reports enabled Keel 5.82.0, while this checkout and installed CLI report 5.84.0; the isolated installation reports 5.84.0. Basis: local CLI output, 2026-10-01.
- D1 — Give Codex `hooks/codex.json` through its existing manifest, with complete shell command strings. Keep the shared file and root Claude manifest unchanged. Basis: F1/F2 and #178's mandate to fix confirmed host-specific gaps; this avoids interfering with #187.
- D2 — A Codex-only adapter invokes the existing `keel mail hook user-prompt-submit` notice provider for either event and emits only the supported event name and additionalContext. It never calls `read`, injects bodies, registers watchPaths, or propagates exit 2. Provider failure yields a non-blocking fallback warning naming `keel mail list`. Basis: #183's minimum next-input receipt and existing data-not-authority requirement.
- D3 — No capability is globally promoted from manual after one local probe. Tests distinguish plugin discovery, untrusted skip, native execution, and actual context reaching the runtime's model boundary. Isolated test hooks may use the documented one-invocation trust bypass only after their source is reviewed; they never change personal trust. Basis: #178 and F2.
- D4 — The current agent performs all Keel execution and Review. Native tests exercise Codex as the system under test; any model endpoint is a local deterministic boundary fixture, not a delegated agent executing Keel. Basis: AGENTS execution ownership.
- D5 — Group/@/relative-time formatting and the eventual host-neutral notice entry belong to #187. Until they exist, reuse the documented `keel mail` compatibility notice without inventing future flags. Basis: #183's owner comment. Durable owner: https://github.com/TanglmChris/keel/issues/187.

## Hidden Knowledge / Assumptions

None. No assumption that plugin installation implies hook trust or execution.

## Risks / Trade-offs

- No supported idle event was found; receipt is on startup/next prompt. This is #183's authorized minimum, not a downgrade of Claude's wake-up.
- An explicit Codex hook file must retain continuity and guard declarations; regression tests and native discovery check this.
- Hooks run on each prompt. Empty/unbound mailboxes emit no notice. Failed providers warn without blocking user work.
- #187 will need to replace only the notice-provider call once its interface is specified; its own issue already owns that shared output requirement.

## Open Questions

None for the selected compatibility implementation. Group-chat formatting remains owned by #187.
