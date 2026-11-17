## Context

- F1 — Keel 5.229.0's `src/core/chat/notice.js` `resumeCli` invokes `claude agents` and `claude --bg --resume`; the Codex receiving hook only projects notices on start or prompt.
- F2 — Local Codex CLI 0.164.0 generated `/tmp/keel-codex-host-schema`; `ClientRequest.json` contains `thread/list`, `thread/read`, `thread/resume`, and `turn/start`. A generated schema is interface evidence, not evidence that an existing desktop session can be safely resumed or messaged.
- F3 — The Codex plugin declares SessionStart, UserPromptSubmit and PreToolUse hooks; `keel capabilities --target codex` reports manual until runtime activation, trust, and actual blocking are verified.
- F4 — At baseline 8e43cdb5, `docs/host-contract.md` stated Codex had no automated wake or hand-over; this change invalidates that statement for explicitly managed roles.
- F5 — On 2026-11-16, an isolated `codex app-server --stdio` initialized successfully and `thread/list` filtered to this repository returned two threads, including this active desktop chat. An attempt through `codex app-server proxy` returned no initialization response within eight seconds. A further metadata-only `thread/read` of this actively running chat through that isolated server returned `notLoaded`, whereas the desktop app reported it active. Thus isolated-server status is not authoritative for active desktop work. Neither result proves safe resume, delivery, or deduplication.

- F6 — The shared app-server daemon reports running version 0.167.2 while the CLI is 0.164.0. A read-only `codex app-server proxy` initialization received no response in eight seconds; directly sending line-oriented JSON to its control socket closed the connection. These observations do not establish that the daemon cannot support a correct client.

## Goals / Non-Goals

**Goals:** Make an explicitly configured Codex role discoverable, deliver only addressed work, prevent duplicate active turns, hand over with a durable note, and report only measured hook and host capabilities. Prove the end-to-end workflow with two real Codex roles where the host permits it.

**Non-Goals:** Rework #527, modify kaiwu, infer hook enforcement from files alone, or change existing Claude semantics.

## Decisions

- D1 — Extend Keel's existing role, presence, chat, shift and capability mechanisms rather than create a parallel team system. Basis: current Keel architecture and owner's scope, 2026-11-16.
- D2 — Keep host/provider identity explicit; never send a role's work to a different provider or create a replacement session merely because the host cannot be reached. Basis: preventing duplicate work and loss of continuity.
- D3 — Probe the installed Codex app-server and native hooks with isolated fixtures before selecting an adapter and making behavioral claims. Basis: F2 and F3.

## Hidden Knowledge / Assumptions

- A1 — The installed app-server permits a separate Keel process to discover and resume the same desktop thread. Resolve by: an isolated two-role host probe before finalizing the host transport and runnable implementation tasks.
- A2 — Codex's hook configuration, trust and matching expose reliable edit and shell push denial in this host. Resolve by: a real trusted-hook probe before claiming enforcement; retain manual capability when not verified.

## Coupled Iteration Contract

Not required unless a task explicitly declares coupling.

## Risks / Trade-offs

An untrusted or unactivated hook must not be represented as enforced. Delivery retries can duplicate work unless persisted identity, claim and host state are checked together. An unavailable host must remain visible and leave the intended work pending. Actual host availability, provider mismatch and approval behavior are not yet proven.

## Open Questions

- Q1 — Whether the local daemon and desktop share a usable, stable control endpoint, and how it reports busy, removed and archived threads. Basis: F2; resolve with an isolated host probe, not inference from the schema.
- Q2 — How lifecycle events, trust and hook denial behave on this installed Codex desktop and CLI, including compaction and shell execution. Basis: F3; resolve with an isolated native-hook probe.

## Host transport findings (2026-11-16)

- F7 — The daemon control socket accepts a WebSocket HTTP Upgrade (101), not line-oriented JSON. Masked WebSocket frames successfully initialized and performed metadata-only `thread/read`.
- F8 — The CLI 0.164.0 and managed binary 0.167.2 proxies both timed out when fed newline JSON because the proxy forwards raw socket bytes. This was a transport mismatch, not evidence the daemon is unusable.
- F9 — The running managed daemon is Codex 0.167.2 and owns the control socket. Through its verified WebSocket connection, the current active desktop chat still reports `notLoaded`; shared persisted history therefore does not establish shared live ownership. Existing desktop chats must not be resumed automatically on that evidence.
- Q3 — Should Keel create and own team-role sessions on the managed Codex daemon, or must it control existing desktop chats through an additional desktop bridge? Basis: F7-F9 expose distinct runtime ownership and a duplicate-execution risk. Resolve by: owner choice requested in this chat before executable host-adapter tasks are finalized. Closed by D4: owner accepted the managed-daemon route.

- D4 — Owner chose the managed-daemon route on 2026-11-16: Keel starts and manages Codex team roles on the shared service. Existing desktop chats are not implicitly adopted. This resolves Q3; the host adapter must verify managed role identity before delivery.

## Native probe and adapter completion

- F10 — Codex 0.164.0 ran an isolated SessionStart hook and denied the only Bash pwd call through PreToolUse with KEEL_ISOLATED_DENIAL (2026-11-17). Inline known scripts were enabled for that invocation only; production trust was unchanged. This proves the interface, not the shipped plugin's activation or compaction.
- D5 — The managed adapter drains only waking unread records from the existing chat store through keel tick or an explicit drain command. Claimed records deduplicate in the role registry, active roles wait, and uncertain results require inspection rather than replay. The successor receives the retained handover note with its next delivery. Native patch paths (including moves) use the same Touch evaluator; shell events use existing push authorization. No capability is promoted on script tests alone.

- F11 — Real turns on the existing 0.167.2 daemon retried with Connection failed: error sending request. Its inherited proxy pointed to localhost:7890, while successful current CLI invocations had no proxy. The same managed binary on an explicit isolated socket with the current environment completed the two-role acceptance. Existing daemon and desktop sessions were not restarted or adopted. This is host-environment evidence, not a product fallback that starts another server on connection failure.
- F12 — Real acceptance completed two roles and successor context on 2026-11-17; sanitized identifiers and results are in evidence/real-host.json. Native production hook trust and compaction remain manual.

- F13 — The native 0.164.0 patch event uses tool_input.command, not the patch/input fields assumed by the stand-in. The preliminary script correctly failed closed but denied allowed files too. Task 4.1 must accept the measured field and retain all source/move checks. Native Bash push to main was actually blocked under push:codex/* in the same isolated invocation.

## Resolved investigation questions

A1 and Q1 were resolved by F7-F9 and D4: persisted desktop metadata is not live ownership; the supported adapter owns newly started managed roles instead. A2 and Q2 have bounded evidence: F10 and the final isolated native policy probe prove startup and actual patch/push denial on CLI 0.164.0; current production plugin trust and compaction remain manual, rather than inferred from those probes. Q3 is closed by the owner's D4 decision.
- F14 — The final native probe after the F13 correction created the allowed file and blocked the forbidden file and main push; evidence/native-policy.json records the session, measured field and limits.
