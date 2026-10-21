## Purpose

Define Keel's managed overlay for the OpenSpec-generated target surfaces of every action in the managed set — propose, apply, archive, and sync — and the one neutral sentence it says about subagents.
## Requirements
### Requirement: Keel overlays every action in the managed set

Keel MUST maintain a managed overlay on the OpenSpec-generated skills of every action in the managed set — `propose`, `apply`, `archive`, and `sync` — for each supported target, except where a target has no surface for an action, and on any OpenSpec command entry for those actions that a repository still holds. The overlay MUST state that Keel rules take precedence over conflicting generic OpenSpec instructions.

The requirement MUST name the set rather than a subset of it. Each action's overlay content is stated by its own requirement below; this one states which actions have an overlay at all, and a statement that names two of four leaves the file disagreeing with itself.

#### Scenario: Claude surfaces receive the overlay for every managed action

- **WHEN** `keel --init --target claude` runs in a repository
- **THEN** the `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, and `openspec-sync-specs` skills under `.claude/skills/` each contain the Keel overlay marker
- **AND THEN** no file exists under `.claude/commands/opsx/`

#### Scenario: Codex surfaces receive the overlay for every managed action

- **WHEN** `keel --init --target codex` runs with `CODEX_HOME` set
- **THEN** the same four skills under `.codex/skills/` each contain the Keel overlay marker
- **AND THEN** `<CODEX_HOME>/prompts/opsx-propose.md`, `opsx-apply.md`, `opsx-archive.md`, and `opsx-sync.md` each contain the Keel overlay marker
- **AND THEN** the user's real `.codex/prompts` directory is not required for verification

#### Scenario: OpenCode surfaces receive the overlay for the actions it has

- **WHEN** `keel --init --target opencode` runs in a repository
- **THEN** the `openspec-apply-change`, `openspec-archive-change`, and `openspec-sync-specs` skills under `.opencode/skills/` each contain the Keel overlay marker
- **AND THEN** no `opsx-*.md` file exists under `.opencode/commands/`
- **AND THEN** no authoring overlay is written for `propose`, which this target does not receive

#### Scenario: A command file a repository still holds keeps its overlay

- **WHEN** a repository holds `.claude/commands/opsx/apply.md` from an earlier `both` delivery and `keel --install --target claude` runs
- **THEN** that file carries the Keel overlay marker alongside the skills

### Requirement: Keel refreshes existing overlays idempotently

Keel MUST replace an existing managed overlay block instead of duplicating it, and MUST skip missing OpenSpec files during `keel --install` instead of creating incomplete generated surfaces.

#### Scenario: Install refreshes an existing overlay

- **WHEN** an initialized target has an OpenSpec file for a managed action with an outdated Keel overlay block
- **AND WHEN** `keel --install --target <target>` runs
- **THEN** the file contains exactly one current Keel overlay block
- **AND THEN** other OpenSpec-generated content remains present

#### Scenario: Install skips missing OpenSpec files

- **WHEN** `keel --install --target <target>` runs before OpenSpec has generated the files for a managed action
- **THEN** Keel does not create placeholder OpenSpec files for that action
- **AND THEN** `keel --doctor --target <target>` reports the missing overlay or missing surface with remediation

### Requirement: Apply surface binds work to the task contract

The apply overlay MUST direct the agent through the unchecked tasks of an approved `tasks.md` in order, each started by `keel gate task-start` and completed by `keel gate task-complete`, with every stop trigger still halting. It MUST route confirmations to the repository's standing authorization without removing an undeclared one, and MUST NOT restrict what a subagent may do.

#### Scenario: Apply overlay continues through an approved task list

- **WHEN** a target apply skill or command entry is inspected
- **THEN** the overlay says the agent works through the unchecked tasks of an approved `tasks.md` in order, each through its own `task-start` and `task-complete`
- **AND THEN** it says a stop trigger still halts

#### Scenario: Apply overlay routes confirmation to the declaration

- **WHEN** a target apply skill or command entry is inspected
- **THEN** the overlay says a standing-authorized action proceeds without a per-occurrence confirmation
- **AND THEN** the overlay says an undeclared action still requires the confirmation it requires today
- **AND THEN** the overlay says a standing authorization never substitutes for a gate, evidence, or Review

### Requirement: Archive surface binds archiving to its gate

The archive overlay MUST state that archiving is gated by `keel gate change-close` and `keel-review-checklist`, and that follow-up ownership is verified before it. The overlay MUST direct the agent to consult the repository's standing authorization for the archive action rather than repeat a confirmation the owner already declared, and MUST NOT remove any confirmation the repository has not declared. It MUST NOT restrict what a subagent may do.

#### Scenario: Archive overlay names its gate

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay names `keel gate change-close` and `keel-review-checklist`
- **AND THEN** it contains no sentence limiting subagents to assessment or barring them from archiving

#### Scenario: Archive overlay routes confirmation to the declaration

- **WHEN** a target archive skill or command entry is inspected
- **THEN** the overlay says a repository that standing-authorizes `archive` does not need the per-occurrence archive confirmation
- **AND THEN** the overlay says the completion gate and follow-up ownership checks still run unchanged

### Requirement: Subagents are the model's choice and are treated as the main agent is

Keel's resident protocol, consumer bootstrap, and generated overlays MUST state that a subagent is the model's choice and is treated as the main agent is, and that the gates, the `Touch` write guard, and the evidence rules apply to whoever runs a step. They MUST NOT require activation, a brief, a guard manifest, a tier declaration, or a rerun by another agent before a subagent may act. They MUST NOT encourage or discourage subagent use, parallelism, number, or a concrete model.

#### Scenario: The neutral sentence is all the surfaces say
- **WHEN** the protocol, the bootstrap, or a generated apply, archive, or sync surface is read
- **THEN** it states that a subagent is the model's choice and is treated as the main agent is
- **AND THEN** it names no helper/delegate split, mandatory brief, refusal without a guard manifest, or rerun duty

### Requirement: Keel overlays Codex and Claude propose authoring surfaces
Keel MUST add one managed authoring overlay to OpenSpec propose surfaces for Codex and Claude that invokes expectation alignment before specs and executable tasks finalize while preserving official OpenSpec artifact order, paths, and templates.

#### Scenario: Codex propose surface receives alignment overlay
- **WHEN** Keel initializes or refreshes the Codex target after this change
- **THEN** the installed OpenSpec propose skill and applicable Codex command entry contain exactly one current Keel alignment overlay
- **AND THEN** the overlay routes material ambiguity through `keel-align-expectations`

#### Scenario: Claude propose surface receives alignment overlay
- **WHEN** Keel initializes or refreshes the Claude target after this change
- **THEN** the installed OpenSpec propose skill and applicable Claude command entry contain exactly one current Keel alignment overlay
- **AND THEN** the overlay routes material ambiguity through the same portable skill authority

#### Scenario: OpenCode receives no v4 authoring overlay
- **WHEN** Keel handles an OpenCode compatibility target during v4
- **THEN** existing portable OpenSpec artifacts remain readable and manual
- **AND THEN** Keel does not create a new OpenCode-specific alignment overlay, discovery file, or automation path

### Requirement: Apply returns newly discovered expectations to alignment
The existing apply overlay MUST require the current agent to stop and return to authoring alignment when implementation exposes a material expectation, acceptance boundary, or user-owned decision absent from durable authority.

#### Scenario: Implementation discovers missing product authority
- **WHEN** implementation encounters a material behavior or boundary not covered by the task capsule and OpenSpec artifacts
- **THEN** apply stops before accepting or implementing that choice
- **AND THEN** the current agent reruns alignment and reauthors affected proposal/design/spec/task authority

#### Scenario: Implementation discovers a factual detail
- **WHEN** implementation discovers a repository fact that does not change accepted behavior or scope
- **THEN** the current agent may record the fact and continue within the existing task boundary
- **AND THEN** it does not invoke a product interview unnecessarily

### Requirement: Thin CLI owns OpenSpec initialization and overlays only
After native plugin migration, `keel --init/--install` MUST use official OpenSpec 1.5.0 to initialize or refresh action skills, install Keel schema and managed authoring/apply/archive/sync overlays, and merge minimal bootstrap guidance. It MUST NOT copy Keel plugin skills, hooks, adapters, or full protocol assets into target-specific project trees.

#### Scenario: Codex init uses plugin plus official OpenSpec
- **WHEN** a Codex project with the Keel plugin runs `keel --init --target codex`
- **THEN** OpenSpec action skills/prompts, Keel schema/overlays, and minimal bootstrap are ready
- **AND THEN** Keel skills/hooks remain supplied by the installed plugin

#### Scenario: Claude init uses plugin plus official OpenSpec
- **WHEN** a Claude project with the Keel plugin runs `keel --init --target claude`
- **THEN** OpenSpec action skills, Keel schema/overlays, AGENTS bootstrap/import, and plugin diagnostics are ready
- **AND THEN** no `.claude/skills/keel-*`, `.claude/hooks/keel-*`, or adapter copy is created by the CLI

#### Scenario: Plugin is missing
- **WHEN** init succeeds for schema/OpenSpec/bootstrap but the native plugin is absent
- **THEN** doctor reports the partial state and native plugin install remediation
- **AND THEN** explicit Keel Core commands remain available

### Requirement: Overlay refresh preserves official and user content
The thin CLI MUST update one managed overlay block in each supported official OpenSpec surface, preserve other generated/user content, and diagnose missing surfaces without manufacturing incomplete OpenSpec files.

#### Scenario: OpenSpec update changes generated content
- **WHEN** OpenSpec 1.5.0 or later refreshes an action skill or command
- **THEN** Keel reapplies exactly one current overlay without replacing the official content

#### Scenario: Surface is missing
- **WHEN** install runs before OpenSpec generated an overlay target
- **THEN** Keel skips that target and doctor reports the official init/update remediation

### Requirement: Keel makes openspec invocable for skill-driven agents

Keel MUST provide a `keel openspec` passthrough that forwards its arguments to
Keel's resolved openspec command, and Keel's overlays MUST direct skill-driven
agents to use it in place of a bare `openspec` command that may not be on PATH.

#### Scenario: Passthrough invokes the resolved openspec

- **WHEN** `keel openspec` runs with arguments
- **THEN** Keel forwards the arguments to its resolved openspec command
- **AND THEN** the passthrough works even when bare `openspec` is not on PATH

#### Scenario: Overlays direct agents to the passthrough

- **WHEN** an apply or archive overlay references invoking openspec directly
- **THEN** it directs the agent to `keel openspec` rather than a bare `openspec` that may be unavailable

### Requirement: Archive overlay skips already-promoted specs and reminds to clear the guard

The archive overlay MUST sequence the `openspec-sync-specs` skill before archive and direct the
archive to pass `--skip-specs` so a delta already promoted by sync is not
re-applied, and MUST remind the current agent to run `keel guard clear` after
archiving. The gate itself remains read-only and writes nothing.

#### Scenario: Archive after sync skips specs

- **WHEN** the archive overlay guides a change whose delta was promoted through the `openspec-sync-specs` skill
- **THEN** it directs the archive to pass `--skip-specs`
- **AND THEN** it explains this avoids re-applying the already-promoted delta, which upstream openspec rejects

#### Scenario: Archive reminds to clear the guard

- **WHEN** the archive overlay guides a completed archive
- **THEN** it reminds the current agent to run `keel guard clear`
- **AND THEN** the gate performs no guard deletion itself, preserving the read-only guard invariant

### Requirement: The consumer bootstrap names the record-write exemption

The bootstrap is the whole resident protocol a consumer repository receives, and
it is the only place many consumers will ever read what Touch bounds. Saying
Touch is the write boundary "for product files" is accurate but relies on the
reader inferring what the qualifier excludes; the inference that actually gets
made is that the task's own `tasks.md` must be declared in Touch, which is the
misreading that produced a reported defect.

The bootstrap MUST name the exemption outright: a task's own change directory is
writable without being declared in Touch. Because the block is under a byte
budget, the room MUST be found by dropping lower-value content rather than by
raising the budget — the budget exists so resident context stays cheap, and
raising it to fit each addition removes the pressure that keeps it short.

#### Scenario: A consumer learns the exemption from the bootstrap alone

- **WHEN** a consumer repository's installed bootstrap is read
- **THEN** it states that Touch bounds product writes and that the change's own directory is exempt
- **AND THEN** a reader does not have to infer the exemption from a qualifier

#### Scenario: The block stays within its budget

- **WHEN** the bootstrap block is measured after the exemption is named
- **THEN** it is still under the byte and line budgets, which are unchanged
- **AND THEN** the content dropped to make room is named in the change that dropped it

### Requirement: The sync surface carries the overlay that governs it

Keel MUST project its OpenSpec surface overlay onto the sync surface on every target that receives the overlay for propose, apply, and archive. A surface that performs a gated action MUST state the gate that governs it, because the agent performing the action reads that surface and may not be reading the protocol file at the same moment.

The sync overlay MUST state that `keel gate change-close --action sync` and `keel-review-checklist` run before it completes, and that OpenSpec is invoked through `keel openspec`. It MUST also state that sync promotes the change's spec delta, so an archive that follows one uses `--skip-specs`. It MUST NOT restrict what a subagent may do.

Keel MUST NOT add `sync` to the standing-authorization vocabulary as part of covering this surface. Naming the gate that governs an action and deciding whether a repository may authorize it once are separate.

#### Scenario: Installing projects the overlay onto the sync surface
- **WHEN** Keel installs its OpenSpec surface overlay into a repository
- **THEN** the sync command surface and the sync skill carry the overlay marker, alongside propose, apply, and archive
- **AND THEN** uninstalling removes it from the sync surface as it does from the others

#### Scenario: The sync overlay names the gate and the delta consequence
- **WHEN** the sync overlay is read
- **THEN** it names `keel gate change-close --action sync` and `keel-review-checklist`
- **AND THEN** it states that sync promotes the spec delta and that a following archive uses `--skip-specs`

#### Scenario: Explore is deliberately uncovered
- **WHEN** the overlay is projected
- **THEN** the explore surface receives none, because it reaches no gate and changes no state

### Requirement: Uninstalling removes the overlay it installed

The overlay is written into files OpenSpec owns, and every line of it is about Keel — the gate to run, the checklist to run, how to invoke OpenSpec, where standing authorization is declared. Once Keel is removed those instructions name commands that no longer exist, in files that were never Keel's. `keel --uninstall` and `keel --clear` MUST therefore remove the overlay block from every surface that installing projects it onto, on every target, driven by the same surface list that writes it so that a surface added to one direction cannot be missed by the other.

The removal MUST take the overlay block and the whitespace separating it from the content before it, and nothing else. The file MUST be preserved: the bytes that preceded the overlay MUST be unchanged, and a surface MUST NOT be deleted or emptied because its Keel block was removed. Removing the block is the whole obligation — restoring the file to its pristine upstream state is `openspec update`'s concern, not uninstall's.

A `--dry-run` uninstall MUST report each surface it would clean and MUST write nothing, because a plan that reports nothing for a run that writes is the failure mode this surface has already produced once on the install side.

A surface carrying no overlay, and a surface whose file does not exist, MUST be counted rather than treated as an error, so that uninstalling twice, or uninstalling a repository that never received the overlay, succeeds.

#### Scenario: Uninstalling removes the overlay from every surface installing wrote it to
- **WHEN** a repository is installed and then uninstalled on any target
- **THEN** no surface that received the overlay still carries the marker, including surfaces outside the repository such as the Codex prompt directory
- **AND THEN** the surfaces are the ones the shared surface list names, not a second list written beside it

#### Scenario: The surrounding OpenSpec content survives
- **WHEN** the overlay is removed from a surface
- **THEN** the file still exists and its content is exactly the bytes that preceded the overlay
- **AND THEN** the blank line the install side inserted before the block is removed with it, so the file does not end in trailing blank lines

#### Scenario: A dry run reports the removal without performing it
- **WHEN** `--uninstall` runs with `--dry-run` against an installed repository
- **THEN** each surface that would be cleaned is named in the output
- **AND THEN** every surface still carries its overlay afterwards

#### Scenario: Uninstalling twice is not an error
- **WHEN** uninstall runs against a repository whose surfaces carry no overlay, or whose surface files are absent
- **THEN** it succeeds, reporting nothing removed rather than failing

### Requirement: Every overlay summary names the managed action set

Keel reports the overlay from more than one direction — refreshing it during `--init`, `--install`, and `--check`, removing it during `--uninstall` and `--clear`, and reporting its health from `--doctor`. Each of those lines names the actions it covers, and every one of those names MUST be derived from the managed action set rather than written beside it. A summary MUST NOT state its action list as a literal, because a literal is correct only until the set changes and then becomes wrong silently, while still reporting a healthy count.

Two summaries produced by the same installed repository MUST name the same actions. They describe one surface list, and a reader comparing them is entitled to conclude that a difference between them means a difference in what was covered.

The derived label MUST continue to exclude the authoring action, which governs authoring rather than a state-changing command, so that the actions named are the ones whose command surfaces are counted.

This capability's own specification is a summary of the managed set in the same sense, and MUST be checked against it. The `## Purpose` line and the requirement that states which actions carry an overlay MUST each name every action in the managed set, and a verification check MUST fail and name the location when either stops doing so. The check MUST read the managed set from the code that owns it rather than restating it, and MUST assert those two named locations rather than scanning the file: three statements in the published specs name a proper subset of the set correctly — the doctor's command-surface label, the archive requirement's description of what the current agent owns, and a spelling of the full set that writes `propose` as authoring — and a check that refused them would cost more than the drift it catches.

A capability's `## Purpose` MUST be maintained by direct edit to the published spec. OpenSpec's delta operations are Requirement-scoped, so no change can carry a Purpose edit, and the line is written once when the capability is created. This is why a drifted Purpose survives a sweep of the requirements around it, and why the check above covers it explicitly.

#### Scenario: The refresh summary names the derived set

- **WHEN** `keel --init`, `keel --install`, or `keel --check` refreshes the overlay and reports its summary
- **THEN** the actions named in that line are the managed set the overlay covers
- **AND THEN** an action added to that set appears in the line without the line being edited

#### Scenario: Refresh and removal agree on one repository

- **WHEN** one repository is installed and then uninstalled
- **THEN** the refresh summary and the removal summary name the same actions
- **AND THEN** the health line from `--doctor` on that repository names those same actions

#### Scenario: A drifting summary is a failing check

- **WHEN** a summary line stops naming the managed set, whether by being written as a literal or by an action joining the set without reaching it
- **THEN** a verification check fails and names the line that drifted
- **AND THEN** the check distinguishes a summary that disagrees from a summary that is absent, so a line that was never printed is not reported as a line that printed the wrong thing

#### Scenario: The capability's own Purpose names the managed set

- **WHEN** the `## Purpose` line of this capability's published spec names a proper subset of the managed set
- **THEN** a verification check fails and names the Purpose line
- **AND THEN** the check reads the managed set from the code rather than from a literal of its own

#### Scenario: The requirement that states the set names all of it

- **WHEN** the requirement stating which actions carry an overlay names a proper subset of the managed set
- **THEN** a verification check fails and names that requirement
- **AND THEN** the check fails rather than passing silently when it cannot find that requirement at all


### Requirement: The overlay states the invocation that resolves

Every Keel OpenSpec surface overlay MUST state that the OpenSpec CLI is invoked through Keel in a
repository where a bare `openspec` may not resolve, and MUST point at the Keel diagnostic that
reports which case a given installation is.

Keel MUST state this in its own overlay block and MUST NOT edit the OpenSpec-authored body of the
file the overlay is appended to.

#### Scenario: An installed surface names the working invocation

- **WHEN** Keel installs or updates an OpenSpec command or skill surface
- **THEN** its Keel overlay names `keel openspec` as the invocation to use
- **AND THEN** it points at `keel --doctor` for whether a bare `openspec` resolves

#### Scenario: The upstream body is untouched

- **WHEN** Keel writes an overlay into an OpenSpec-authored file
- **THEN** the text outside the overlay block is unchanged

### Requirement: Project init never downgrades OpenSpec surfaces

`keel --init` MUST read the highest `generatedBy` version among the repository's OpenSpec skill surfaces before its OpenSpec rewrite. When that version is strictly newer than the OpenSpec Keel would run, it MUST skip `openspec init --force` and `openspec update --force` and MUST say which version wrote the surfaces and which it declined to run. It MUST still refresh the managed protocol and Keel's overlays. When the surfaces are the same version or older, or carry no stamp, init MUST behave as it did before.

#### Scenario: Newer surfaces are left alone
- **WHEN** the repository's OpenSpec skills carry a `generatedBy` newer than Keel's OpenSpec and `keel --init` runs
- **THEN** those files keep their content, and init reports that it skipped the OpenSpec rewrite and why

#### Scenario: Older surfaces are still refreshed
- **WHEN** the repository's OpenSpec skills carry an older `generatedBy`
- **THEN** `keel --init` rewrites them with Keel's OpenSpec as before

### Requirement: Codex overlays follow the OpenSpec layout the repository carries

Keel MUST place and remove Codex OpenSpec overlays, and count Codex OpenSpec surfaces, in the layout the repository actually carries. When the repository has OpenSpec skills under `.codex/skills` and none under `.agents/skills`, that is the OpenSpec 1.6 layout: skills under `.codex/skills`, commands as `CODEX_HOME` prompts. Otherwise it MUST use the OpenSpec 1.13 layout: skills under `.agents/skills`, with no command files.

#### Scenario: A new Codex repository gets the 1.13 layout
- **WHEN** `keel --init --target codex` runs in a new repository with the pinned OpenSpec
- **THEN** the Keel overlays are on `.agents/skills/openspec-*/SKILL.md`, and doctor reports the full Codex surface there

#### Scenario: A 1.6-era Codex repository keeps its layout
- **WHEN** a repository carries OpenSpec skills only under `.codex/skills`
- **THEN** the overlay refresh writes there and to the `CODEX_HOME` prompts, exactly as before


### Requirement: OpenSpec update restores every installed target overlay

After a successful `keel openspec update`, Keel MUST replay its managed overlays on existing OpenSpec surfaces for every target installed in that repository. It MUST preserve upstream content, avoid duplicate overlays, and create no absent surface. Other OpenSpec commands MUST retain passthrough behavior. A failed update MUST preserve its exit status and MUST NOT replay overlays.

#### Scenario: A multi-target update restores overlays
- **WHEN** Claude and Codex surfaces exist and an OpenSpec update replaces them
- **THEN** the successful Keel update restores exactly one current overlay on each managed surface in the resulting layout
- **AND THEN** another update retains exactly one overlay and upstream body content

#### Scenario: An update fails
- **WHEN** upstream update exits nonzero
- **THEN** Keel returns that status without replaying overlays

#### Scenario: An absent target remains absent
- **WHEN** a repository has only one installed target
- **THEN** updating does not create another target's files

### Requirement: Doctor reports overlays for all repository-installed targets

Doctor MUST report separately attributable overlay health for every repository-installed target, including targets other than the selected one. Discovery MUST use repository surfaces rather than unrelated global prompts. It MUST retain legacy Codex and .agents layout support and name remediation for incomplete coverage.

#### Scenario: Codex overlay is missing while Claude is healthy
- **WHEN** doctor selects Claude in a mixed repository with missing Codex overlays
- **THEN** Claude health remains attributable to Claude and an additional Codex report identifies the missing coverage and Codex remediation

#### Scenario: Global prompts belong to another repository
- **WHEN** global Codex prompts exist but the repository has no Codex surface
- **THEN** doctor does not infer an installed Codex target from those prompts

### Requirement: A protocol refresh brings every installed target's overlays forward

`keel --install` and `keel --init`, whatever `--target` selects, MUST refresh Keel's overlays on the existing OpenSpec surfaces of every target installed in the repository, discovered from repository surfaces as doctor discovers them. They MUST create no surface for a target the repository does not carry. Doctor MUST report an overlay whose version marker differs from the running CLI as stale, attributed to its target, with the refresh command, rather than as healthy.

#### Scenario: A Claude refresh also refreshes Codex overlays
- **WHEN** a repository carries Claude and Codex surfaces whose overlays are at an older version and `keel --install --target claude` runs
- **THEN** every Claude and Codex overlay carries the running version, with exactly one overlay per surface and upstream content unchanged

#### Scenario: An absent target stays absent
- **WHEN** a repository carries only Claude surfaces and `keel --install --target claude` runs
- **THEN** no Codex or OpenCode surface is created

#### Scenario: Doctor names a stale overlay
- **WHEN** a Codex overlay's version marker is older than the running CLI
- **THEN** doctor's Codex overlay line reports it stale, names the refresh command, and does not report `ok`

### Requirement: An archive keeps the files the change tracked

`keel openspec archive <change>` MUST, after OpenSpec archives the change successfully, re-add to the Git index each file that Git tracked under the change before the move and that an ignore rule matches at its archived path, and MUST report how many it re-added. `keel gate change-close --action archive` MUST warn, without changing its verdict, about tracked files under the change that an ignore rule matches, naming them and `keel openspec archive` as the archive that keeps them.

#### Scenario: Tracked evidence the change ignores survives the archive
- **WHEN** a change's own `.gitignore` ignores `evidence/**`, a file under `evidence/` was force-added and committed, and `keel openspec archive <change>` runs
- **THEN** the file's archived path is in the Git index and the output says one file was re-added

#### Scenario: The close warns before the move
- **WHEN** `keel gate change-close --action archive` runs on that change before it is archived
- **THEN** a warning names the tracked evidence file and `keel openspec archive`

### Requirement: Keel generates OpenSpec workflows as skills only

Every OpenSpec `init` and `update` Keel runs — from `keel --init` and from `keel openspec init|update` — MUST use the user's global OpenSpec configuration with `delivery` replaced by `skills`. Keel MUST NOT write the global configuration, and other `keel openspec` subcommands MUST run against it unchanged.

#### Scenario: A global both delivery still yields skills only

- **WHEN** the user's global OpenSpec configuration declares `delivery: both` and `keel --init --target claude` runs
- **THEN** the five workflow skills exist under `.claude/skills/`, no file exists under `.claude/commands/opsx/`, and no generated skill names an `/opsx:` command
- **AND THEN** the global configuration file is byte-for-byte unchanged

#### Scenario: Command files from a both delivery are removed

- **WHEN** a repository holds `.claude/commands/opsx/apply.md` and `keel --init --target claude` runs
- **THEN** that file no longer exists

#### Scenario: A pass-through update generates skills only

- **WHEN** a repository holds `.claude/commands/opsx/apply.md` and `keel openspec update --force` runs in it
- **THEN** that file no longer exists and the skills carry the Keel overlay
- **AND THEN** `keel openspec config list` still reports the user's own `delivery`

### Requirement: Shipped guidance names the OpenSpec workflows by skill

The archive overlay, `README.md`, `README.zh-CN.md`, the Keel skills, and the Keel OpenSpec schema MUST name the OpenSpec workflows by their skill names — `openspec-propose`, `openspec-apply-change`, `openspec-sync-specs`, `openspec-archive-change`, `openspec-explore` — and MUST NOT name an `/opsx:` command, since Keel generates none.

#### Scenario: No shipped guidance names an opsx command

- **WHEN** the archive overlay text, both READMEs, every `SKILL.md` under `src/skills/` and `plugins/keel/skills/`, and `assets/openspec/schemas/keel-spec-driven/schema.yaml` are read
- **THEN** none contains `/opsx:`
- **AND THEN** the archive overlay names `openspec-sync-specs`
