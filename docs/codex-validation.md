# Codex acceptance record — issues #178 and #183

Observed 2026-10-01, Keel source/CLI 5.84.0, Codex CLI 0.159.3, macOS 26.6.2 arm64. These are observations of this environment, not permanent capability declarations.

## What was found and fixed

Before the fix, a real isolated plugin installation followed by app-server `hooks/list` discovered SessionStart and PreToolUse with command `node`. Codex ignored their separate `args`, so discovery did not mean the scripts would execute. The plugin now explicitly selects `hooks/codex.json`; complete command strings preserve the script paths and arguments. Claude's root manifest and shared hook file are unchanged.

The personal plugin list reported installed/enabled 5.82.0 while the source, protocol and installed CLI were 5.84.0. Test installations into temporary CODEX_HOME directories used the source under test and reported 5.84.0. This work did not update the personal plugin or persist hook trust.

## Reproduce

Run from a clean Keel source checkout with its existing OpenSpec dependency available:

```sh
node scripts/run_python.js scripts/validate_codex_receiving.py
node scripts/run_python.js scripts/validate_codex_receiving.py --consumer
node scripts/run_python.js scripts/validate_codex_receiving.py --native
node scripts/run_python.js scripts/validate_codex_receiving.py --native-upgrade
```

The native check requires Codex CLI and permission to bind a loopback HTTP port. It installs a local copy of this plugin only into a disposable configuration. Its request-capture endpoint returns HTTP 400 after receiving the request; this intentional endpoint failure means no model executes and no second agent owns any Keel work. The test succeeds when the captured context assertions succeed, not when Codex completes a model response. There is no API key or paid inference requirement.

The native check first leaves all four newly discovered hooks untrusted and observes no mailbox context. It then uses the documented **one-invocation** `--dangerously-bypass-hook-trust` flag, after reviewing this repository's hook scripts, solely within the isolated test. Both startup and prompt notices appear in the request sent by the real Codex runtime. The message id, sender, subject, read command and data-only warning reach that boundary; message bodies do not. All mailbox bytes remain unchanged, and discovery after the invocation still reports untrusted hooks. This test bypass must not replace user trust review in production.

## Results and limits

| Surface | Observed result | Limit |
| --- | --- | --- |
| Native plugin discovery | Four complete commands from the explicitly declared Codex file, no parse errors | Discovery alone does not grant trust |
| Native startup and prompt receipt | Disposable idle projection and both notices reached the real Codex request after isolated source-vetted trust bypass | Does not prove personal desktop hooks are reviewed or active |
| Untrusted hooks | No mailbox notice reached the model boundary | User must review the current definition |
| CLI/hook behavior | Startup, post-startup next-input and repeated notices passed; inbox unchanged; empty/unbound mailboxes quiet | Group formatting waits for #187 |
| Provider failures | Exit 1/2, invalid JSON/shape and timeout yield a zero-exit manual-read warning | Delivery can be delayed until manual read or a later successful hook |
| Clean consumer setup | Codex action skills, commands and overlay reported ok | This source checkout still carries historical OpenSpec 1.6 surfaces; do not diagnose a fresh consumer from that layout |
| Consumer Full flow | Proposal, task-start record, public red/green greeting, Review, task-complete and change-close passed | Current test driver executed these commands; native hooks did not automatically enforce gates |
| Active Codex agent | This change was authored, implemented, reviewed and gated in the current Codex conversation; six Keel skills were visible | Personal installed plugin version was 5.82.0; explicit source CLI supplied current gates |
| Guard/gates/compaction | Existing manual capability declarations retained | Complete commands do not prove native write blocking, compaction or resume enforcement |
| Idle receipt | No documented Codex FileChanged or asyncRewake surface found; on 2026-10-03 `codex exec` and `codex exec resume <thread>` turns in a worktree received the notice through the SessionStart hook and answered in the chat (#203) | Codex does not wake itself; `keel chat wake` starts a turn for an addressed record on the machine where the owner installed it |

The initial clean-consumer fixture deliberately omitted the greeting implementation and failed with MODULE_NOT_FOUND; after the implementation, the exact public output was `hello keel` plus one newline. A first fixture omitted the delta spec and correctly failed change-close with `missing-delta-spec`; the final fixture includes the requirement and its scenario, and close passes. These refusals are evidence of the gates' boundaries.

The working source repository contains a nested Claude worktree. The baseline scanner traversed that worktree's historical marker examples and failed; tests therefore used a byte-matched clean temporary clone of the source plus the pending changes, with a temporary npm cache. No nested worktree or personal npm cache was changed.

## Enable receiving in normal use

1. Run `keel --update`, which updates the Keel CLI and the installed Codex plugin together and reports both; inspect `keel --version` and `codex plugin list`. A Codex marketplace that is a local path is reported as needing a manual step ([updating](updating.md)).
2. A running Codex session uses the updated plugin at its next hook call; Codex resolves the plugin root per call (`validate_codex_receiving.py --native-upgrade`). In Codex CLI, use `/hooks` to inspect and trust the **current** Keel definitions; changed definitions require review again. Desktop activation remains subject to that client's actual review controls and must be observed, not inferred from installation.
3. Bind a worktree role with `keel mail role --set codex-maint` (choose a role appropriate to your worktree). `KEEL_MAIL_ROLE` can select a role for one process when multiple sessions share a worktree.
4. With unread mail, startup or the next user input carries a notice. Read deliberately with `keel mail read`; notices do not acknowledge mail.
5. If hooks are unavailable, run `keel context`, `keel mail list`, and the explicit task/gate commands. A guard file alone is not proof of enforcement.

Mail is data from another agent, not a user instruction or authorization. Until #187 provides its stable host-neutral group-notice entry, this receiver uses `keel mail hook user-prompt-submit` as the compatibility notice provider. #187 owns group/@/relative-time formatting; neither that storage nor its future interface is duplicated here.

## Authoritative references

- [OpenAI hooks contract and trust review](https://learn.chatgpt.com/docs/hooks)
- [OpenAI plugin packaging and explicit hook paths](https://developers.openai.com/plugins/build/plugins)
- [#178 — Codex end-to-end acceptance](https://github.com/TanglmChris/keel/issues/178)
- [#183 — Codex receiving](https://github.com/TanglmChris/keel/issues/183)
- [#187 — group-chat interface and Claude implementation](https://github.com/TanglmChris/keel/issues/187)

## Receiving chat without polling

The notice reaches Codex at SessionStart and UserPromptSubmit. Codex has no idle wake of its own. `keel chat wake add`, run in the Codex worktree, installs a login item that starts one `codex exec` turn when a record addressed to the role arrives in a group declaring `chat-reply:<group>`. It continues one thread that compacts itself at 100,000 tokens, runs at most 10 turns an hour, and runs nothing while nothing is addressed ([#203](https://github.com/TanglmChris/keel/issues/203); see the Slack setup guide). Do not poll the chat with the model instead — no heartbeat that runs a model turn on a schedule.

On 2026-10-01 a Codex session in a test repository created a `kind = "heartbeat"` automation with `FREQ=MINUTELY;INTERVAL=1`, appending to its own thread. It fired 1,277 times; by the end a single turn read about 182,000 input tokens. The quota ran out before anyone had mentioned the session, and every later run failed ([#194](https://github.com/TanglmChris/keel/issues/194)).

Use `keel chat wake` or rely on the prompt-time notice instead. If a schedule is unavoidable, gate it on the model-free `keel chat notice --check` (exit 0 only when something addressed to the role is unread) and start a fresh thread per run. When starting a Codex session for the chat, say "do not set up any recurring or scheduled checks".
