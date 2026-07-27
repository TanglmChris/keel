## Purpose

Define one-way, disposable projection of OpenSpec-owned work into supported native runtime surfaces.
## Requirements
### Requirement: Native projection is one-way and disposable

Keel MUST derive native runtime projection from OpenSpec and MUST NOT treat native goal, task UI, transcript, memory, checkpoint, or subagent state as input authority for OpenSpec selection or completion.

#### Scenario: Missing native state is reconstructed
- **WHEN** a supported native projection is absent after startup, resume, compaction, or UI reset
- **THEN** Keel may recreate it from the current `keel context` result
- **AND THEN** no OpenSpec state is reconstructed from the missing native surface

#### Scenario: Native completion cannot close an OpenSpec task
- **WHEN** a native goal evaluator, task UI, or subagent reports completion
- **THEN** the OpenSpec task remains incomplete until `task-complete` passes and the current agent updates its durable owner

### Requirement: Continuity projection covers startup resume and compaction

Keel target adapters MUST use the strongest verified native behavior to project current context at startup and after resume or compaction, with explicit advisory or manual fallback when reinjection cannot be verified.

#### Scenario: Codex continuity is reinjected
- **WHEN** a Codex thread starts, resumes, or returns from compaction
- **THEN** the adapter projects the current context through a verified Codex lifecycle surface
- **AND THEN** unsupported or untrusted activation is reported as advisory or manual

#### Scenario: Claude continuity is reinjected
- **WHEN** a Claude Code session starts, resumes, or returns from compaction
- **THEN** the adapter projects the current context through a verified Claude lifecycle surface
- **AND THEN** compaction does not make HANDOFF or transcript memory the durable owner

### Requirement: Goal and task-view projection requires explicit activation

Keel MUST require explicit user or selected-task authorization before it MAY project the selected task objective, Acceptance, and next action into native goal or task UI.

#### Scenario: Authorized goal is derived from OpenSpec
- **WHEN** native goal projection is explicitly enabled for a selected task
- **THEN** the projected condition is derived from that task's objective, Acceptance, and Stop boundary
- **AND THEN** goal evaluation remains advisory to Keel completion

#### Scenario: Goal is not enabled implicitly
- **WHEN** no user or task authorization enables a native goal loop
- **THEN** Keel does not start or continue one automatically

#### Scenario: Task UI remains a view
- **WHEN** Keel projects OpenSpec work into native task or todo UI
- **THEN** native updates do not change task checkboxes, Evidence, Review, Acceptance, or follow-up ownership

### Requirement: Worktree movement preserves durable ownership

Keel MUST recompute context in the current checkout and preserve the same OpenSpec owner when a supported runtime resumes or hands work between worktrees of the same repository. Keel MUST NOT infer ownership from a stored checkout path.

#### Scenario: Supported worktree sees the same owner
- **WHEN** a session moves to or resumes in another worktree containing the selected OpenSpec change
- **THEN** Keel resolves that change from the current checkout
- **AND THEN** the native worktree or thread identifier does not become durable owner state

#### Scenario: Divergent worktree blocks safely
- **WHEN** the current worktree does not contain the selected durable owner or contains incompatible OpenSpec state
- **THEN** projection is blocked or manual with a clear reason
- **AND THEN** Keel does not copy hidden state from another checkout to make it appear valid

### Requirement: Subagent projection preserves Keel ownership

Keel MAY use native subagent lifecycle surfaces only when the user or selected task explicitly authorizes bounded delegation. The current agent MUST retain Keel execution, acceptance, fallback, and completion decisions.

#### Scenario: Authorized subagent receives bounded context
- **WHEN** an authorized subagent starts
- **THEN** it receives only the selected task, required Read context, applicable Touch or read-only boundary, and requested evidence contract
- **AND THEN** it is not authorized to change Acceptance, mark tasks complete, sync, archive, or transfer Keel ownership

#### Scenario: Subagent return is evidence only
- **WHEN** an authorized subagent stops
- **THEN** its result is treated as report or evidence for current-agent review
- **AND THEN** native subagent completion does not satisfy `task-complete`

#### Scenario: No implicit delegation
- **WHEN** the user and selected task have not authorized subagent use
- **THEN** Keel does not spawn or activate one merely because the runtime supports it

### Requirement: Native recovery and scheduling remain optional aids

Keel MUST remain correct when native memory, checkpoints, rewind/undo, transcript branching, automation, scheduled loops, channels, agent view, or agent teams are disabled or unavailable.

#### Scenario: Native recovery does not replace Git and OpenSpec
- **WHEN** a user applies a native checkpoint, rewind, undo, or session branch
- **THEN** Keel recomputes from the resulting checkout and OpenSpec artifacts
- **AND THEN** the native recovery record is not accepted as durable task evidence

#### Scenario: Memory is not required
- **WHEN** native memory is disabled, stale, machine-local, or absent
- **THEN** continuity, gates, and native projection continue from OpenSpec and Git

#### Scenario: Scheduling is outside Core
- **WHEN** a runtime offers automations, loops, channels, agent view, or agent teams
- **THEN** Keel does not require or manage those surfaces as part of Core correctness

### Requirement: Native projections consume the fingerprinted task capsule
Every authorized native goal, task view, worktree view, or helper brief MUST be derived from the same freshly compiled `keel-task-capsule/v1` used by Core gates and MUST include the contract fingerprint needed to detect stale views.

#### Scenario: Projection includes executable boundaries
- **WHEN** an authorized projection is requested for a selected task
- **THEN** it includes capsule schema, fingerprint, objective, resolved Acceptance, Read, Touch, verification strategy and checks, stop/autonomy boundary, current-agent owner, helper return authority, and prohibitions applicable to that projection
- **AND THEN** it does not independently parse task Markdown

#### Scenario: Stale projection is rejected
- **WHEN** the current capsule fingerprint differs from the task's recorded start fingerprint or the fingerprint supplied by a returning helper
- **THEN** Keel rejects the projection or helper return as stale
- **AND THEN** native completion cannot update durable OpenSpec state

#### Scenario: OpenCode remains manual-compatible
- **WHEN** OpenCode consumes a v4 task during this change
- **THEN** it may use the compact artifact and explicit Keel CLI manually
- **AND THEN** this capability does not require an OpenCode-specific hook, goal, plugin manifest, or automation path

### Requirement: Native plugin SessionStart projects shared context
Codex and Claude native plugins MUST map their supported SessionStart lifecycle to shared Keel context projection through one plugin script. The script MUST treat OpenSpec/Git and the current task capsule as authority and MUST return only disposable runtime context.

#### Scenario: Codex SessionStart maps to shared Core
- **WHEN** a trusted Codex plugin SessionStart hook fires
- **THEN** the plugin script invokes the shared Keel projection for the current checkout
- **AND THEN** Codex receives concise additional context without a target-local task parser

#### Scenario: Claude SessionStart maps to shared Core
- **WHEN** an allowed Claude plugin SessionStart hook fires
- **THEN** the same plugin script invokes the shared Keel projection for the current checkout
- **AND THEN** Claude receives equivalent concise authority through its supported hook output

#### Scenario: SessionStart never starts execution
- **WHEN** either runtime receives the startup projection
- **THEN** the hook does not select a task among ambiguous owners, record a fingerprint, spawn a helper, create a goal, write evidence, or continue a turn automatically

### Requirement: Plugin projection has a minimal failure contract
The SessionStart script MUST return deterministic, bounded diagnostics for missing repo, missing/incompatible Keel CLI, non-ready context, malformed Core output, timeout, or operational failure and MUST not expose arbitrary command output as trusted instructions.

#### Scenario: Context is ambiguous or idle
- **WHEN** shared Core computes ambiguous, blocked, or idle state
- **THEN** the hook injects only that status, reason, and explicit next command
- **AND THEN** it does not guess an owner

#### Scenario: Core invocation fails
- **WHEN** Keel CLI cannot run or returns malformed/operational failure output
- **THEN** the hook reports a concise manual fallback and exits according to non-blocking SessionStart policy
- **AND THEN** the session remains usable

### Requirement: Authorized goal projection has a disposable lifecycle
Keel MUST create, resume, and retire a native goal only as a disposable view of one durably authorized task and fingerprint.

#### Scenario: Authorized goal resumes with matching authority
- **WHEN** a supported session resumes with an active goal
- **AND WHEN** the durable task authorization, explicit selection, and recomputed fingerprint all match
- **THEN** the current agent may continue the selected task
- **AND THEN** native goal state is not used to infer a different owner or completion

#### Scenario: Missing native goal is reconstructed
- **WHEN** the authorized task is still incomplete after a supported resume or compaction
- **AND WHEN** the same durable fingerprint and activation capability remain valid
- **THEN** the current agent may reconstruct the disposable projection
- **AND THEN** it does not create a new task authorization

#### Scenario: Projection authority drifts
- **WHEN** the task, referenced authority, checkout, or fingerprint no longer matches the authorization
- **THEN** the projection is paused, cleared, or refused before product writes
- **AND THEN** reauthorization is required after the durable task is repaired or reselected

### Requirement: Helper projection cannot transfer Keel ownership
Keel MUST project helper work as a bounded evidence request and MUST keep task implementation, acceptance, and completion in the current agent.

#### Scenario: Helper report returns
- **WHEN** a bounded helper completes its brief
- **THEN** the current agent validates its scope and repository byte stability
- **AND THEN** the report is accepted only as supporting evidence

### Requirement: Change checklist projects as a disposable native tasks view

On the Claude target, `keel project tasks` MUST compile a `keel-native-tasks/v1` payload from the selected change's tasks.md checklist — change name, ordered task ids, titles, checkbox state, and the default-selected task — for the current agent to mirror into host-native task tools. The payload MUST be compiled fresh from OpenSpec state on every invocation, MUST NOT be persisted, and MUST NOT introduce a scheduler, auto-advance, a second writer of OpenSpec state, or a session database.

#### Scenario: View compiles from the checklist
- **WHEN** `keel project tasks --target claude` runs against a change with a parseable tasks.md
- **THEN** the payload lists every checklist task with id, title, and checked state plus the default-selected task
- **AND THEN** nothing is written to the project

#### Scenario: Mirroring is agent-owned
- **WHEN** the payload is produced
- **THEN** reflecting it into native task UI is the current agent's explicit step
- **AND THEN** Keel starts no synchronization loop and updates no host state itself

#### Scenario: Host disagreement never writes back
- **WHEN** host-native task status disagrees with OpenSpec checkboxes or gate state
- **THEN** OpenSpec artifacts and gate results remain the only authority
- **AND THEN** the disagreement is at most recorded as projection evidence, never written into OpenSpec state

#### Scenario: View dies with the change
- **WHEN** the projected change is archived
- **THEN** the view has no surviving artifact to refresh and any mirrored host tasks are abandoned or closed by the agent
- **AND THEN** no Keel surface reports the stale view as authority


### Requirement: Projected session state is reported to the user

SessionStart projection is delivered on a model-only channel, so the agent is
the sole reader unless it speaks. The projection MUST therefore instruct the
receiving agent to state the projected context — status, any selection, and the
next action or fallback reason — to the user in its first response of the
session, without waiting to be asked. The instruction MUST be present on every
branch the projection can take, because the branches a user most needs to see
are the degraded ones. Reporting is a disclosure obligation only: it MUST NOT
select an owner, record a fingerprint, start execution, or turn the projection
into authority, and the projection MUST continue to state that it is
disposable and that OpenSpec and Git remain the durable authority.

#### Scenario: Ready projection is disclosed before work begins
- **WHEN** the SessionStart projection resolves a ready context with a selected change and task
- **THEN** the projected context instructs the agent to state that selection and its next action to the user in the agent's first response
- **AND THEN** the instruction does not authorize implementation, selection, or any write

#### Scenario: Non-ready projection is disclosed rather than silently absorbed
- **WHEN** the SessionStart projection resolves a context that is idle, ambiguous, or otherwise not ready
- **THEN** the projected context instructs the agent to state that status and its reasons to the user in the agent's first response
- **AND THEN** the projection still refuses to guess among candidate owners

#### Scenario: Degraded projection still reaches the human
- **WHEN** the SessionStart script emits its bounded fallback for a missing or incompatible Keel CLI, malformed Core output, or a timeout
- **THEN** the fallback text instructs the agent to tell the user that the projection failed and which manual command replaces it
- **AND THEN** the agent does not silently proceed as though continuity were established

#### Scenario: Resident protocol carries the rule without the plugin
- **WHEN** a repository follows the Keel resident protocol and no native plugin projection runs
- **THEN** the resident Session Start rule still requires the agent to state the context result to the user in its first response
- **AND THEN** continuity does not depend on the plugin being installed or loaded for the user to see where the work stands
