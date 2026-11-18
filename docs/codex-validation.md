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

## Managed team acceptance — 2026-11-17

The selected change `codex-host-team-support` records sanitized real-host results in `evidence/real-host.json`. This exercise used the installed managed Codex **0.167.2** binary listening on an explicitly selected isolated Unix WebSocket endpoint, two distinct temporary Git worktrees, and actual model turns. It did not adopt desktop chats. This is separate from the registered `codex-managed-host` scenario, which uses a stand-in WebSocket server and native hook payloads.

- worker-a: thread `01a1e709-ec67-75a0-9002-dc0b90e391d2`, addressed record `20261117T010558596Z-owner-78babf`, completed turn `01a1e70a-0fc0-7511-b5f9-1f21b001b36e`, final `KEEL_REAL_WORKER_A_OK`.
- worker-b: thread `01a1e709-ecd9-7ff0-9248-6e761582235e`, addressed record `20261117T010558598Z-owner-e02726`, completed initial turn and follow-up `01a1e70a-d090-7d12-a3e7-30f9252050d9`, final `KEEL_REAL_WORKER_B_OK`.
- Repeating drain returned already-delivered and the same original turn IDs. Idle worker-a handed over to `01a1e70a-3cb5-7bc0-ace5-0bd3eec36230`; its completed turn `01a1e70a-d007-72b1-97b2-0df23979f948` returned `KEEL_REAL_HANDOVER_NOTE` after receiving the retained note.

The system daemon accepted role creation and turn RPCs, but inherited an old localhost:7890 proxy. Its scoped logs showed `Connection failed: error sending request`; accepting a turn therefore did not prove a model result. Only the exercise's stuck probes were interrupted. The existing daemon was not restarted. Teams need a reachable model backend as well as a reachable control socket; use an explicit service started with the intended environment when required.

An isolated **CLI 0.164.0** invocation, with known inline hook definitions enabled only for that invocation, emitted SessionStart and denied the only native Bash `pwd` call with `KEEL_ISOLATED_DENIAL`. The shipped guard now parses native patch source and move destination paths and matches Bash for existing push policy. Script tests prove that policy, not production trust or activation. Native shipped-plugin denial, compaction reinjection, and approval automation remain unverified/manual; the adapter never grants approvals itself. Current hooks must still be reviewed in the native hook interface after an update.

The final isolated native policy probe used this repository's actual guard on CLI 0.164.0 (session `01a1e719-5c7e-74a2-8f82-73afd84e28b1`). The measured patch payload is `tool_input.command`. An allowed patch created `allowed.txt` containing `accepted`; an out-of-Touch patch was blocked and created no `forbidden.txt`; Bash `git push origin main` was blocked under `push:codex/*` before execution (the fixture had no remote). This was repeated after correcting the initial field mismatch that had failed closed for allowed files too. Sanitized results live in the change's `evidence/native-policy.json`. It verifies isolated native policy behavior, while production plugin trust/activation and compaction remain manual.

## Default daemon repair — 2026-11-17

The owner subsequently authorized the local rollout and old-proxy repair. Immediately before restart the default managed daemon reported no loaded threads. It was restarted with the current working environment; all uppercase/lowercase HTTP_PROXY, HTTPS_PROXY and ALL_PROXY variables were absent in the replacement process. The installed managed binary remained Codex 0.167.2.

A real turn through the default `~/.codex/app-server-control/app-server-control.sock` completed with `KEEL_DEFAULT_HOST_OK` (thread `01a1e73f-05a4-74c0-8157-d2a092fd4482`, turn `01a1e73f-0613-7803-a123-abf0f494f40e`). The probe used the verified 5.229.0 source adapter and was archived after completion. This supersedes the earlier stale-proxy limitation for this machine; the earlier isolated-host measurements remain historical evidence. Other desktop chats were not adopted or interrupted, and hook trust/compaction capabilities were not promoted by the network repair.

### Published and installed rollout

GitHub `v5.229.0` and npm `@christang/keel@5.229.0` were verified after PR #529 passed both exact-head Full gates and repository automation landed it. The global Keel CLI, enabled Claude Keel plugin and enabled Codex Keel plugin were independently verified as 5.229.0, including their installed manifests. The installed global CLI then completed another default-host turn (`01a1e742-d77e-7fb2-b12c-28138229465f`) with `KEEL_DEFAULT_HOST_OK`; its probe was archived. Changed native hooks retain the host's normal review requirement; installation did not grant trust, and current skill snapshots may require the host's normal reload/new-session boundary.

## Owned unload recovery — issue #531

New delivery to an identity-verified managed notLoaded thread now calls thread/resume for the recorded thread on the same connection, revalidates id/cwd/state and starts work only when idle. Delivered claims return before load-state checks without resume; unknown claims refuse without replay. Active-after-resume waits, invalid recovery refuses, and no replacement thread or permission override is introduced. The default cold-load deadline is 15 seconds; explicit --timeout is honored. Other RPC defaults remain five seconds and the model-free drain child has a 40-second bound.

Real Codex 0.167.2 acceptance on 2026-11-17 completed PM's first turn, observed notLoaded, received an execution role's actual AND truth-table file and GATE_OK test, then completed PM's second result turn on the same identity. PM thread `01a1e76a-0424-7912-aa02-3431a7412571` completed second turn `01a1e76b-f2a3-78a2-bcfe-6d0f52df46a3` with `PM_RESULT_ACK_0001`; PM had two turns and execution role one. Duplicate records started no extra work. The second model turn took 61.827 seconds, exceeding the initial observer window; read-only verification confirmed completion without a second start. Test probes were archived. This is actual host evidence, distinct from the stand-in CLI checks.

### Blank managed initialization (5.229.2 / #537)

A fresh Codex 0.167.2 thread can disappear after its creation connection closes before its first turn: read reports `thread not loaded` and same-id resume reports `no rollout found`. Native `thread/name/set` materializes the blank thread. Keel uses that operation with the role name and rechecks identity before successful start or successor hand-over, retaining the created id on uncertain initialization. No model warm-up, permission override or substitute thread is used; already-lost registrations require explicit owner disposition.

Real public-CLI acceptance created `01a1e794-ffe7-7c90-9ac3-c78395a02fea`, closed the creation connection for at least190 seconds, observed notLoaded, then completed its first actual turn `01a1e797-f6ba-7451-8d27-27044dbc6509` with `FIRST_READY` on the identical thread. It had exactly one turn, and duplicate delivery created none. The probe was archived; isolated name/archive controls and the failed unnamed baseline are retained in the change evidence. This is actual host evidence, separate from the stand-in CLI regression.


## Shared App, reviewer and owned cwd — 2026-11-17

Keel 5.230.0 adds explicit thread reviewer creation/persistence and same-id
`codex recover`. Public CLI/native-boundary tests cover original claims and
unknown/policy/writer failures. Real native 0.167.2 creation used zero model turns,
retained auto_review/on-request/workspace-write through cold recovery and first
App input. Real recover restored the original worktree and subsequent actual pwd
execution, without rewriting the role record or replacing the thread.

Linux App 26.1023.51421 was launched with two explicitly approved disposable
profile/home runs connected to the existing native 0.167.2 backend; the original
App and all production registrations stayed untouched. Real foreground work made
backend CLI delivery wait, then backend work completed on the same id. In reverse,
the rendered native Guide action submitted input to the same busy turn. An actual
item/started sleep notification preceded that input; one command completed
normally (14965ms), then INFLIGHT_NATIVE_SERIAL_DONE was returned. Native Guide
updates a current turn; this does not prove a separate queued task.

Private thread 01a1e9ad-eaaf-71f1-9052-6d7e331d10ba completed
NATIVE_BACKEND_WITH_APP_CLOSED while its App was normally closed and backend
identity stayed unchanged. The second actual App UI showed that reply and the
in-flight result. All original history ids, cwd, auto_review/on-request/
workspaceWrite and delivery claim were retained; duplicate delivery started none.
Both App runs ended normally and their loopback diagnostic ports were closed.

Opening the test project added one native backend trust section despite private
frontend home. Testing paused; the owner separately approved that sole temporary
entry and its exact deletion, restoring the pre-test config hash. Three production
registries and original App/backend identities matched throughout. This is not a
claim of global-config isolation, an atomic original-App Quit barrier, macOS
acceptance or Kaiwu production deployment. The earlier expired global idle window
remains a negative historical result. Full native evidence and failed preliminary
probes are owned by [#541](https://github.com/TanglmChris/keel/issues/541); deployment
is [Kaiwu #546](https://github.com/TanglmChris/kaiwu-ip/issues/546).

## Owned onboarding candidate (#546/#547, 2026-11-18)

The source candidate adds explicit original-frontend registration and owned
endpoint migration. Public CLI boundary tests cover original identity, complete
paginated history, exact claim preservation, effective native policy, busy/input
refusal, competing registrations, writer rejection, uncertain acquisition/final
commit and explicit reconciliation. They are stand-ins, not model acceptance.

Real isolated **0.167.2** processes with a shared **empty unauthenticated Codex
home**, zero model turns and no copied credentials proved public original-id
read-only registration, writer refusal while the original subscriber remained,
explicit source unsubscribe/target owner rejoin, reconciliation and a subsequent
direct migration. Both test processes exited. Native approval drift on a blank
thread was also measured and correctly refused. Effective-policy-preserving
built-in profile representation is normalized; changed approval is not.

Actual authenticated nonempty-history/model receipt and read-only filesystem
refusal remain a release prerequisite tracked in Keel #546/#547. Automatic
approval review rejected existing-auth real-model testing; the exact incremental
human confirmation is pending. No production migration, new App experiment,
native hook trust promotion or macOS acceptance is claimed by these checks.
