## Context
F1 — Keel5.229.3 managed delivery checks recorded thread/worktree/endpoint, persists claims and refuses unknown outcomes. Basis: src/core/codex-host.js and archived #531/#537 evidence.
F2 — Downstream reports App stdio runtime0.165.0-alpha.1.2 and Unix daemon0.167.2 are distinct execution instances; shared history does not prove shared writer. App input has encountered active-writer refusal, and chief/PM/flow now report cwd mismatch against original bound worktrees. Basis: https://github.com/TanglmChris/keel/issues/541 and its comments; locally unverified production report.
F3 — Official documentation says last-subscriber unsubscribe unloads after an inactivity grace period and documents thread_unload_delay_secs. Basis: https://learn.chatgpt.com/docs/app-server . Docs alone do not establish actual installed release timing or cross-process handoff.
## Goals / Non-Goals
Preserve owned id/history/claims and actual thread-level policy while enabling verifiable serial App/background work. Do not force a particular socket, adopt arbitrary desktop threads, weaken cwd checks, mutate production registrations or bypass native writer protection.
## Decisions
D1 — Start with read-only inspection and isolated owned fixture diagnosis under the existing protocol. Inspect installed schemas/help, native lifecycle configuration, writer refusal/release and supported cwd/reviewer overrides; obtain actual foreground/background evidence before authoring implementation. Basis: verified user request in kaiwu PM chat to progress #541/#546, issue contract, prior user authorization for real managed-team validation. Only private fixture sessions may be created, used and cleaned up.
D2 — Default review behavior stays unchanged unless explicitly requested at thread scope; on-request and workspace-write stay intact and no global reviewer configuration is edited. Basis: issue #541 explicit requirement.
## Hidden Knowledge / Assumptions
Q1 — Which installed native APIs/configuration safely release or queue writer ownership between App and background processes? Resolve by:1.1; no product implementation until measured.
Q2 — Which native cwd restore and policy-preservation operations are supported without changing owned id/history/claims? Resolve by:1.1; production drift remains refused until a safe explicit procedure exists.
## Coupled Iteration Contract
None.
## Risks / Trade-offs
Reading shared metadata cannot establish remote writer inactivity. Idle grace and writer lock lifetimes require measurement. No daemon bootstrap is run, only help/status/schema are read. A failed capability test is evidence, not authority to replace a thread or disable protection. #535 goals are finalized, with implementation owned by #544; they do not activate new execution rules here.
## Open Questions
Q1 and Q2 above; unresolved implementation or deployment choices return to authoring.

## Diagnostic checkpoint (task 1.1 complete)
F4 — Native queues were consumed by actual busy and idle App execution on the
same owned fixture thread; duplicate client UUID queue/add calls create duplicate
entries. Claims and history reconciliation are still required in a product adapter.
F5 — A backend-owned active turn caused immediate real App input to fail with
active-writer refusal. Per-thread idle unload does not establish a shared execution
endpoint or a persistent App-side connection to the backend.
F6 — Native resume with explicit cwd/runtimeWorkspaceRoots restored actual pwd
execution on the same owned fixture id. No production project attachment was tested.
F7 — Explicit native thread/settings/update persisted auto_review on a blank
thread without a model turn; cold resume and the first actual App turn retained
auto_review/on-request/workspace-write. This resolves the initialization mechanism
question without hidden warm-up.
Basis for F4–F7: evidence/diagnosis.md and its recorded JSON fixtures; public
checkpoint https://github.com/TanglmChris/keel/issues/541#issuecomment-6944250292 .

Q3 — App-only execution with backend queue producers avoids the demonstrated
two-writer contention, but does not provide independent execution after the App
runtime exits. This is a material acceptance change, not an implementation detail.
Owner: human project owner; structured choice requested. Until explicit acceptance,
retain the existing foreground communication plus persistent backend requirements.
Chief clarified that its own authority does not downgrade these requirements.

F8 — Official OpenAI documentation describes SSH connections configured through
the desktop Connections UI and remote CLI/TUI app-server connections. These are
candidate native shared-host routes, not proof that this installed Linux App is
already attached to the current backend. No SSH configuration, remote-control
pairing, bootstrap or daemon start/restart was performed. Sources (2026-11-17):
https://learn.chatgpt.com/docs/remote-connections and
https://learn.chatgpt.com/docs/developer-commands .

Implementation and release remain owned by issue 541. Diagnostic task completion
does not approve App-only execution, activate issue 535/544 policies, or prove
production deployment. Official release notification responsibility is recorded at
https://github.com/TanglmChris/keel/issues/541#issuecomment-6944100669 .

D3 — Continue original-acceptance shared-endpoint investigation using installed
public CLI help, official documentation and isolated read-only protocol probes.
Native app-server proxy is a candidate: determine its protocol and whether the
installed Linux App exposes a supported route to it. No App connection, SSH,
production configuration or daemon lifecycle mutation is authorized by this
slice. User acceptance of App-only execution is not a prerequisite for this
read-only investigation, nor inferred from it. Basis: original issue 541 goals
and existing isolated diagnosis authorization; chief's scope clarification.

D4 — Human owner explicitly approved the idle-window experiment in this chat:
all local chats/tools idle and work preserved; normal App exit and a one-time
process-local CODEX_APP_SERVER_WS_URL connection to the existing Unix daemon;
no daemon restart, SSH or global configuration change; rollback via original
launcher without the variable. This approval is not App-only acceptance. Only
private fixture validation precedes product implementation or production recovery.
An independent bounded relaunch helper may wait for normal App exit, preserve
logs and launch once; it must never kill the App or restart a daemon. The App
must be exited through a supported normal user action if no tool exposes one.


D5 — Owner explicitly requested checking the controlled switch, continuing issue
541, committing and pushing local evidence/task state, and preparing Mac takeover.
Publish a portable checkpoint of this change only, preserving task 1.3 as pending
until actual evidence closes it. No production source changes, window reset, issue
closure or release can ride along with this checkpoint; issue 527 remains deferred.
The commit/push request is explicit; repository standing authorization also names
commit and push. Linux-only runtime evidence must be distinguished from portable
repository state, and unrelated chat/account metadata is omitted from publication.

F9 — The bounded Linux window ended at 2026-11-17T11:28:14.519Z with
`Idle window expired; App untouched`. No Quit/relaunch or background test turn
ran. The helper is inactive; all three production registry hashes match their
pre-window values. Basis: evidence/window-final-state.json and
https://github.com/TanglmChris/keel/issues/541#issuecomment-6946769610 .
The diagnostic attempt is complete with a negative outcome; shared-App behavior
acceptance and the whole issue remain open. Do not restart the expired window.

D6 — Implement the independently verified reviewer part of issue 541 first:
`keel codex start --approvals-reviewer user|auto_review` explicitly sets only that
managed thread's native reviewer. Existing calls with no flag keep their current
behavior. Preserve on-request and workspace-write, persist explicit reviewer via
native thread/settings/update before managed start/successor success, and retain
it in owned role state and later resume/delivery/handover. Native explicit policy
mismatch or unsupported persistence must fail closed with the created id retained;
no hidden model warm-up, global reviewer edit, replacement thread, implicit socket
migration or production repair. Invalid values and unrelated-action use of the
start flag fail before stateful RPCs. Basis: issue 541's explicit thread-level
reviewer requirement, D2 and measured zero-turn persistence F7. This slice does not
need a global App restart and does not resolve the remaining shared-host goals.

D7 — Keep docs/cli-team.zh-CN.md aligned with the accepted explicit reviewer
interface and error/recovery semantics in docs/cli-team.md. Full regression
reported docs-zh-match-english (8 vs 6 code fences), also failing the dependent
release-evidence-classes scenario. This is a necessary bilingual documentation
repair within the owner's complete issue-541 delivery instruction, not a new
product or permission choice. Preserve all runtime/authorization semantics.


D8 — Continue the existing native handoff diagnosis against the actual App
execution domain before another global experiment. Inspect installed request
surfaces, normal-Quit source, original window terminal evidence and current
App activity; distinguish foreign-daemon read results from actual App tool
terminal state. Record a precise measured capability gap and failure exit if
safe admission/drain cannot be proved. This diagnostic slice does not authorize
Quit/relaunch, Goal changes, production repair, a new executor or a reset window.
Historical Goal re-entry is historical; current Goal state must be reverified.
Basis: original D1/D4 acceptance, owner instruction to continue #541, and the
specific coordination evidence published by kaiwu-ip #555.

D9 — The owner's current request explicitly includes committing/pushing local
work, evidence and task state for Mac takeover. Publish the completed D6/D7
source/tests/bilingual docs plus this change's evidence and continuation state
on the existing codex branch, under a repo-action task. Verify exact staged
scope and remote commit, preserve the default branch, avoid force push, and
claim neither formal release nor complete #541 acceptance. This authorization
extends the prior evidence-only checkpoint D5 to the implemented source slice;
#527 remains deferred and #544 implementation stays separate.


D10 — Turn the safe-handoff findings into a reviewable operational route under
existing D4 authority before any new executor. Separate a naturally quiet actual
App (no authority change) from approving normal Quit with explicitly handed-off
coordination turns still active (requires owner decision and named scope), and
from the conditional case requiring a new native execution-domain admission/drain
facility. Evaluate normal Quit/Cancel source semantics and current actual App
turn/tool provenance without equating foreign backend state to App state. A plan
may identify an authorization delta but never grants it, halts IECC work, changes
Goals/configuration, interrupts tools or starts an experiment. The original owner
request to continue #541 authorizes this planning; chief's message is coordination,
not new human authorization. Existing D9 commit/push covers its portable record.


D11 — Complete the original owned-worktree recovery requirement independently
of global App switching. Add explicit `keel codex recover --role <owned-role>`
on the role's already recorded endpoint only. Verify the recorded role under
its existing operation lock and native thread id; refuse unknown native state,
return waiting for active state without resume, and use native thread/resume
with recorded cwd/runtimeWorkspaceRoots for an idle or notLoaded original id.
Native writer protection remains authoritative; no force, replacement, endpoint
migration, production rewrite or model warm-up. Check returned original id/cwd,
on-request/workspaceWrite and any explicitly recorded reviewer. Preserve the
role record, history, claims and unknown outcomes byte-for-byte; errors report
unverified recovery and require inspection, never replay a delivery. A subsequent
explicit delivery proves actual execution cwd. This is the public mechanism for
issue 541's existing explicit same-id cwd recovery goal, not authority to repair
production registrations or migrate live writers.

D12 — An isolated concurrent native App window is a new proposed alternative to
the original all-idle restart. Installed bootstrap supports a process-local
userData path selected before the instance lock; actual isolation/acceptance is
unverified. evidence/isolated-window-proposal.md defines the exact temporary
profile/home, native shared socket, fixture-only use, optional loopback-only UI
diagnostic port, bounded launches and normal-shutdown failure exits. Owner
approved this exact proposal through the structured reply in the current chat
(2026-11-17). This grants the bounded isolated experiment, not production migration,
original App restart, global changes or permanent multi-instance deployment.


D13 — During D12 the native flow added only the private fixture project trust
section to the backend's global config. The isolated App was normally closed
before further stateful testing; removing exactly this section in memory restores
the pre-experiment SHA256. The human explicitly approved temporarily retaining
that sole test entry, completing the final second launch/normal close and deleting
only that section with exact-original-hash verification. If necessary, only the
remaining reopen/close may finish within ten minutes after that reply, with no
additional launch. Use the conservative deadline 2026-11-17T13:59:21Z (ten minutes
from a pre-reply evidence timestamp, so no later than the approved limit). No
other global edit, credential copy, force kill, production/Goal/tool interruption
or new daemon is authorized. Preserve current config if it has unrelated changes;
never overwrite concurrent owner edits. This explicitly reauthorizes task 2.5's
bounded extension and exact cleanup; it does not reset any historical window.


D14 — Prepare Keel 5.230.0 under the owner's explicit instruction to continue
issue 541 through publication and notify Kaiwu afterward. This is a minor release
for the new explicit reviewer/recover CLI plus documented opt-in native shared
App connection; defaults and the original App remain unchanged. Actual D12/D13
fixtures validate Linux App 26.1023.51421/native 0.167.2, native busy Guide semantics,
in-flight tool completion, closed-App execution, original-id/history/policy/claim
reopen, and exact authorized test-trust cleanup. Publish those facts and limits,
not a universal global-Quit fence, macOS claim or production-deployment success.
Document backend-owned trust, native writer refusal, unknown outcomes and rollback.
Use the repository's version alignment script, current exact OpenSpec dependency,
full regression evidence, installed-package clean/updater proof and full-gate CI;
commit/push the candidate and open a PR for repository-owned auto-merge/publish.
The agent must not merge or hand-tag. No production role migration or permanent
App/service deployment rides along. Chief/flow own Kaiwu #546 production acceptance;
formal release notification includes published version/commit, evidence and the
upgrade/rollback entry. No additional package is introduced and #527 is untouched.
