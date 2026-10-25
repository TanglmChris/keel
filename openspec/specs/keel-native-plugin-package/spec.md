# keel-native-plugin-package Specification

## Purpose
Define how Keel ships as one native plugin for Codex and Claude: one canonical plugin source, the marketplaces that install and update it, how the plugin and its CLI stay compatible (on Claude, as the npm package that carries its own CLI), the SessionStart and write-guard hooks it packages for both hosts and the Claude-only chat hooks (notices, idle wake-up, and SessionEnd presence), and what project setup declares about keeping it current.
## Requirements
### Requirement: Keel has one canonical dual-runtime plugin source
Keel MUST package one plugin at `plugins/keel` with native Codex and Claude manifests, one canonical portable skill/reference tree, and default-discovered hook assets. It MUST NOT generate per-target copies of the same skill or protocol authority.

#### Scenario: Codex manifest is native
- **WHEN** the plugin source is inspected or installed by the supported Codex baseline
- **THEN** `plugins/keel/.codex-plugin/plugin.json` has valid native metadata, name `keel`, the package version, and the canonical skills path
- **AND THEN** it explicitly selects `hooks/codex.json` with complete executable command strings

#### Scenario: Claude manifest is native
- **WHEN** the plugin source is validated or installed by the supported Claude baseline
- **THEN** `plugins/keel/.claude-plugin/plugin.json` has valid native metadata, name `keel`, the package version, and the same canonical skills/hooks inventory

#### Scenario: Skill authority is singular
- **WHEN** the package, repository, or installed plugin inventory is inspected
- **THEN** every Keel skill and reference has one canonical source under `plugins/keel/skills`
- **AND THEN** no `src/skills` or per-target skills copy is current authority
### Requirement: Native marketplaces install and update Keel in isolation
Keel MUST provide valid repo marketplace catalogs for Codex and Claude. The Codex catalog MUST reference the `plugins/keel` source, and the Claude catalog MUST reference the `@christang/keel` npm package at the release version. Keel MUST prove fresh install, update/cache refresh, discovery in a fresh session, disable/remove, and reinstall without mutating the developer's personal marketplace during tests.

#### Scenario: Codex marketplace installs Keel
- **WHEN** an isolated Codex home adds the repo marketplace and installs Keel
- **THEN** Codex lists one Keel plugin with the expected version and skill inventory
- **AND THEN** a fresh task can discover its skills and hook source

#### Scenario: Claude marketplace installs Keel
- **WHEN** an isolated Claude configuration validates the marketplace and installs Keel from the package `npm pack` produces for the tree under test
- **THEN** Claude lists one Keel plugin with the expected version and component inventory
- **AND THEN** an updated plugin applies after `/reload-plugins` or at the next session start

#### Scenario: Development cachebuster is not committed
- **WHEN** a Codex local update smoke needs a cache refresh
- **THEN** a temporary plugin copy receives one `+codex.<cachebuster>` suffix and is reinstalled through its isolated marketplace
- **AND THEN** committed manifests and marketplace entries retain release semver

### Requirement: Plugin and CLI compatibility is explicit
On Claude, Keel's native plugin MUST run the CLI it ships with. On Codex, it MUST treat the separately installed `@christang/keel` CLI and the OpenSpec dependency as executable prerequisites. It MUST diagnose missing, older, newer-incompatible, and matching CLI/plugin versions without installing or upgrading them silently.

#### Scenario: Matching CLI is ready
- **WHEN** plugin base version, Keel CLI base version, OpenSpec minimum, and required capabilities are compatible
- **THEN** skills and hooks may invoke Keel Core commands

#### Scenario: The Claude plugin runs its own CLI
- **WHEN** the SessionStart hook runs from inside the Claude plugin's tree and `KEEL_CLI` is unset
- **THEN** it invokes the package's own `bin/keel.js` rather than the `keel` on PATH

#### Scenario: CLI is missing or incompatible
- **WHEN** the plugin cannot run a compatible `keel --version` and capability preflight
- **THEN** it reports the exact missing/incompatible prerequisite and explicit install or update command
- **AND THEN** hooks do not fabricate context, gates, or completion

#### Scenario: OpenSpec is resolved through Keel
- **WHEN** Keel initializes, validates, or diagnoses OpenSpec
- **THEN** it uses the package-local compatible OpenSpec command before any standalone fallback
- **AND THEN** doctor reports the selected path and version, reading the declared version from `npm-shrinkwrap.json` before `package-lock.json`

### Requirement: Shared SessionStart hook is safe and optional
The plugin MUST package one common command-based SessionStart hook that projects current Keel context when supported and trusted. The hook MUST remain correct to skip and MUST NOT write project/OpenSpec state, start a task/goal, or block unrelated work.

#### Scenario: Trusted hook projects context
- **WHEN** a supported Codex or Claude session starts with the plugin enabled, hook trusted/allowed, and compatible CLI available
- **THEN** the hook invokes shared Keel projection and injects concise current context using that runtime's supported output shape
- **AND THEN** the projection identifies itself as disposable

#### Scenario: Hook is unavailable
- **WHEN** the hook is disabled, untrusted, policy-blocked, unsupported, times out, or lacks a compatible CLI
- **THEN** the session remains usable through the minimal bootstrap and explicit `keel context`
- **AND THEN** no capability is reported as enforced

### Requirement: V4 migration removes only known packaged duplication
Keel MUST remove custom manifest, builder, generated dist, adapters, duplicate protocol/skill copies, and target-copy installer behavior only after native parity is proven. Migration MUST preserve user-modified legacy files and existing OpenCode files.

#### Scenario: Known generated file is retired
- **WHEN** a legacy path matches a known packaged Keel version and its native replacement passes
- **THEN** migration may remove the redundant path and record it in release evidence

#### Scenario: User-modified legacy file is preserved
- **WHEN** a legacy installed or generated path differs from every known packaged version
- **THEN** migration leaves it unchanged and reports its exact path and manual choice

#### Scenario: OpenCode is left outside v4
- **WHEN** migration encounters `.opencode` Keel files
- **THEN** it preserves them and reports compatibility-only status
- **AND THEN** no v4 OpenCode plugin, hook, marketplace, or acceptance path is generated

### Requirement: Continuity projection is compaction-aware
The plugin's session continuity projection MUST distinguish the runtime-reported start source and MUST reinject a recomputed, disposable continuity pointer after a compaction, using only OpenSpec and Git as input.

#### Scenario: Compact source reinjects the task pointer
- **WHEN** a session starts with a compact source while a selection is recomputable
- **THEN** the projection surfaces the recomputed selection, the selected task's recorded Contract fingerprint line when present, and the exact next command
- **AND THEN** the fingerprint is labeled as recorded, not verified, and no drift verdict is claimed

#### Scenario: Unknown source falls back safely
- **WHEN** the start source is absent, unrecognized, or a clear
- **THEN** the projection falls back to the generic startup view
- **AND THEN** the hook still never writes, never blocks, and exits zero

#### Scenario: Projection stays a pointer
- **WHEN** any continuity projection is emitted
- **THEN** it remains line-bounded and contains pointers and commands rather than task authority payloads
- **AND THEN** OpenSpec and Git remain the only durable recovery authority

### Requirement: Pre-compaction preservation is probed, not assumed
Keel MUST NOT claim or rely on a pre-compaction hook ability without behavioral probe evidence, and MUST declare post-compact reinjection as the fallback when the surface is absent or unverified.

#### Scenario: Probed ability is used honestly
- **WHEN** a behavioral probe proves the runtime's pre-compaction surface can carry a continuity instruction
- **THEN** the plugin may use it and the capability reports the observed level
- **AND THEN** the evidence backing the claim is recorded

#### Scenario: Unverified surface stays manual
- **WHEN** the pre-compaction contract is absent, disabled, or unverified
- **THEN** the shipped behavior is post-compact reinjection only
- **AND THEN** doctor reports the pre-compaction capability as manual with the reason

#### Scenario: Unsupported targets document the manual command
- **WHEN** the target has no verified compaction hook surface
- **THEN** guidance documents the manual `keel project --event compaction` reinjection command
- **AND THEN** no native compaction automation is claimed for that target

### Requirement: Installed markers and shipped documentation agree with the package surface
The managed-block marker version MUST have exactly one canonical source in the repository, install code MUST derive its marker from that source, and shipped documentation MUST describe the actual package layout and development flow.

#### Scenario: Marker version is single-sourced
- **WHEN** installation writes or refreshes a managed block
- **THEN** the marker version comes from the one canonical source
- **AND THEN** validation fails if the marker literal is restated elsewhere in the repository

#### Scenario: Detection stays version-agnostic
- **WHEN** installation, upgrade, or uninstall detects an existing managed block
- **THEN** any marker version is recognized
- **AND THEN** conservative upgrade and uninstall semantics are unchanged

#### Scenario: Documentation matches the surface
- **WHEN** shipped documentation describes the repository layout or development flow
- **THEN** it references only surfaces that exist in the package
- **AND THEN** validation fails on references to retired surfaces

### Requirement: Self-update defaults to the published registry package

`keel --update` MUST default its fetch source to the published `@christang/keel`
npm registry package — a registry-type spec — so self-update succeeds in
environments that disable git-type package fetches. An explicit `--source`
argument or the `KEEL_UPDATE_SOURCE` environment variable MAY still select a git
spec for installing an unreleased build, but the shipped default MUST NOT be a
git-type spec.

#### Scenario: Default update packs the registry package
- **WHEN** `keel --update` runs with no explicit `--source` or `KEEL_UPDATE_SOURCE`
- **THEN** the planned pack source is the published registry package `@christang/keel`
- **AND THEN** the default source is not a git-type spec and needs no git-type fetch

#### Scenario: Explicit git source is still honored for development
- **WHEN** a user passes `--source github:TanglmChris/keel` or sets `KEEL_UPDATE_SOURCE` to a git spec
- **THEN** update packs that explicit git spec instead of the registry default
- **AND THEN** the explicit override takes precedence over the registry default

### Requirement: The Claude plugin is the npm package

Keel's Claude plugin MUST be described by a manifest at the repository root, `.claude-plugin/plugin.json`, which declares the canonical skills, the Claude-only command `plugins/keel/commands/shift.md`, and hooks equal to `plugins/keel/hooks/hooks.json` with their script paths resolved from the repository root plus the Claude-only chat hooks — UserPromptSubmit, FileChanged, and SessionEnd groups, and a second SessionStart hook, each running `mail-hook.js` — and whose version is the release version. The Claude-only hooks MUST NOT appear in `plugins/keel/hooks/hooks.json`, while Codex explicitly selects its host-compatible `plugins/keel/hooks/codex.json`. The npm package MUST ship that manifest, so that the package root is the plugin. Keel's Claude marketplace entry MUST take the plugin from the npm package `@christang/keel` at exactly the release version, MUST carry that version, and MUST NOT restate the manifest's components. The package MUST carry an extensionless executable `bin/keel` and its `npm-shrinkwrap.json`, so that the host can put `keel` on the agent's PATH and install the pinned OpenSpec dependency.

#### Scenario: One package carries the plugin and its CLI
- **WHEN** the root manifest, the npm package's file list, and the Claude marketplace entry are inspected
- **THEN** the manifest's skills and command resolve inside the repository, its hooks equal `plugins/keel/hooks/hooks.json` after resolving script paths from the root plus exactly the Claude-only chat hooks, its version is the release version, and `npm pack` includes it
- **AND THEN** the entry's source is `npm` `@christang/keel` at the release version, and the entry declares no skills, agents, or hooks

#### Scenario: The Codex-shared hooks carry no Claude-only event
- **WHEN** `plugins/keel/hooks/hooks.json` is inspected
- **THEN** it declares only SessionStart and PreToolUse and no `asyncRewake` field

#### Scenario: The packaged install carries the pinned OpenSpec
- **WHEN** an isolated Claude configuration installs Keel from the package `npm pack` produces for the tree under test, through the committed entry's shape
- **THEN** the installed plugin lists the Keel skills and both hooks, and its `node_modules/.bin/openspec` reports the version the lockfile pins

#### Scenario: A git-sourced install updates to the npm-sourced one
- **WHEN** a configuration that installed Keel from the git-sourced entry updates after the marketplace names the npm-sourced one
- **THEN** the updated plugin is the npm package's tree and carries the pinned OpenSpec

### Requirement: Each release updates the directory branch

Keel MUST be able to build, from the files its npm package publishes, the plugin tree that Anthropic's plugin directory lists. The tree MUST leave out the scripts only development uses, keeping from `scripts/` exactly the ones the shipped code runs. In that tree, `.claude-plugin/plugin.json` is the root manifest with the name `keel-openspec`, the repository as its `homepage`, and the repository's `PRIVACY.md` as its `privacyPolicyUrl`, and `.claude-plugin/icon.png` is a square PNG. The repository's own root manifest MUST keep the name `keel`. The release job MUST commit that tree to the `claude-directory` branch and push it, and MUST name the resulting commit in the release notes. Building the tree MUST be local, and nothing in Keel MAY submit it to the directory.

#### Scenario: The tree is the package with the directory's name
- **WHEN** `scripts/directory_tree.js` builds into an empty directory
- **THEN** the tree holds exactly the files `npm pack` publishes, less the scripts only development uses, plus `.claude-plugin/plugin.json` and `.claude-plugin/icon.png`
- **AND THEN** its manifest is the root manifest with `name` set to `keel-openspec`, `homepage` set to the repository, and `privacyPolicyUrl` set to the repository's privacy policy, every skill, agent, and hook path in it resolves inside the tree, and the repository's root manifest still names `keel`

#### Scenario: Each release advances the directory branch
- **WHEN** `scripts/directory_branch.js` runs for a version and commit against an origin
- **THEN** origin's `claude-directory` gains one commit whose tree is the directory tree and whose message names the version and commit, starting the branch when it does not exist
- **AND THEN** running it again with an unchanged tree adds no commit

#### Scenario: The release notes name the branch commit
- **WHEN** the release job creates the release for a landed version
- **THEN** it runs `scripts/directory_branch.js` for that version and the tag's commit, and the notes name `keel-openspec`, the `claude-directory` branch, and the commit it printed

### Requirement: Project setup declares Claude plugin auto-update

On the Claude target, `keel --init` and `keel --install` MUST declare auto-update for the Keel marketplace in the project's `.claude/settings.json`. The declaration is an `extraKnownMarketplaces` entry named `keel-marketplace` with the Keel repository as its source and `autoUpdate: true`. The merge MUST preserve every other setting, MUST keep an existing entry's source, and MUST NOT overwrite an `autoUpdate` value the project already states. `keel --uninstall` MUST remove the entry only when it is exactly the one Keel writes. `keel --doctor` MUST report whether auto-update is declared on, declared off, or not declared, and MUST NOT claim to observe whether the host performs updates.

#### Scenario: Init declares auto-update
- **WHEN** `keel --init --target claude` runs in a repository with no `.claude/settings.json`
- **THEN** the file declares `keel-marketplace` with the Keel repository as its source and `autoUpdate: true`

#### Scenario: Existing settings are kept
- **WHEN** `.claude/settings.json` already holds other settings, or a `keel-marketplace` entry with its own source or `autoUpdate: false`
- **THEN** install keeps those settings, that source, and that `false`
- **AND THEN** running install again changes nothing

#### Scenario: Uninstall removes only Keel's entry
- **WHEN** `keel --uninstall --target claude` runs
- **THEN** an entry equal to Keel's is removed, and one the project changed is kept

#### Scenario: Doctor reports the declaration
- **WHEN** `keel --doctor --target claude` runs
- **THEN** a `plugin auto-update` line reports declared on, declared off by the project, or not declared with the command that declares it

#### Scenario: Other targets are untouched
- **WHEN** `keel --init --target codex` runs
- **THEN** no `.claude/settings.json` is written


### Requirement: Codex declares executable host-compatible hook commands

The Codex plugin manifest MUST explicitly select a Codex hook configuration whose command strings include the executable, script path and arguments. It MUST retain continuity and existing guard declarations and add mailbox receiving at SessionStart and UserPromptSubmit. It MUST NOT register FileChanged, watchPaths or asyncRewake; Claude's existing manifest and hook declarations MUST remain unchanged by this Codex-specific adaptation.

#### Scenario: Native Codex discovery preserves script arguments
- **WHEN** Codex discovers the installed plugin's hooks
- **THEN** its reported commands include the declared script paths and event arguments rather than only `node`

#### Scenario: No trust is silently granted
- **WHEN** the plugin is newly installed or a hook definition changes
- **THEN** its non-managed hooks remain subject to Codex's trust review and Keel documents the manual review step

### Requirement: One owner-run update covers every installed Keel component

`keel --update` MUST update the global CLI and then, for each of Claude Code and Codex whose executable resolves and whose `plugin list --json` reports `keel` installed, update that host's Keel plugin through the host's own documented commands. It MUST report exactly one status line per component — the CLI, the Claude plugin, and the Codex plugin — naming the version before and after, when the update takes effect, and any step the owner must still take. A host that is absent or has no Keel plugin MUST be reported `absent` and MUST NOT fail the command. Each `plugin list --json` query MUST be allowed at most 30 seconds, while the update commands keep their longer limit; a query that times out MUST be retried once with the same limit, and a query that times out twice, exits nonzero, or prints no JSON MUST report that component `failed`, naming the command and why — for a timeout, the limit — and MUST NOT report it `absent`, except that when the failed query is Codex's and Codex's own `config.toml` declares the Keel marketplace as a Git source and its plugin cache holds an installed Keel version, the update MUST run from that state and the Codex line MUST name the versions as read from the cache because the query did not answer. A Codex marketplace whose source is not a Git repository MUST be reported `manual`, naming its source and the command that would make it upgradable, and MUST NOT be re-pointed. The Claude marketplace refresh MUST be retried once when it fails, and when the retry also fails, the Claude line MUST read `failed` and say the refresh failed twice. A `failed` line for a host step that exited nonzero MUST name its exit status and, when the host wrote any, its last line of stderr. The Codex marketplace refresh MUST be retried once when it fails, and when the retry also fails, the Codex line MUST name the sparse marketplace paths `.agents/plugins` and `plugins/keel` as `sparse_paths` under `[marketplaces.keel-marketplace]` in the Codex config. The command that makes a marketplace upgradable MUST add it with `--sparse .agents/plugins --sparse plugins/keel`, and those paths MUST contain the Codex catalog and the plugin source it names. When Codex's hook definitions differ between the installed and the new plugin, the Codex line MUST say Codex will ask for review before those hooks run. When the source is the default registry package, the CLI line MUST name the version the npm registry served as its latest. The CLI line MUST take its before and after versions from `<npm root -g>/@christang/keel/package.json`, read before packing and after installing; when the install exits 0 but that file holds a version other than the packed one, the line MUST read `failed`, naming the file and the version it holds, and when the file cannot be read after installing, the line MUST say the install was not verified and why. When `claude plugin update` fails with `E404 No match found for version X` and `npm view @christang/keel version`, allowed the host-query limit, answers a version older than X, the Claude line MUST read `pending`, naming X, the registry's latest, and that `keel --update` should be rerun in a few minutes, and that line MUST NOT count as a failure; an E404 for a version the registry already serves, or an `npm view` that fails or answers nothing, MUST leave the line `failed`. The exit status MUST be nonzero only when a step that ran failed. `--dry-run` MUST print each planned command and run none. No hook or projection MAY invoke this behavior.

#### Scenario: Both plugins are updated and each line says when it applies
- **WHEN** `claude` and `codex` both report Keel installed at an older version, from a Git marketplace, and `keel --update` runs
- **THEN** each host's documented update commands run once, in order, after the CLI update
- **AND THEN** the output carries one line per component naming the old and new version, that the Claude plugin applies to running sessions at their next hook call with skills and agents after `/reload-plugins`, and that the Codex plugin applies at the next hook call

#### Scenario: An absent host is not a failure
- **WHEN** `codex` does not resolve, or reports no Keel plugin
- **THEN** the Codex line reads `absent`, no Codex command runs, and the exit status reflects only the steps that ran

#### Scenario: A local Codex marketplace is reported, not re-pointed
- **WHEN** Codex reports the Keel marketplace with a non-Git source
- **THEN** the Codex line reads `manual`, names the source path and `codex plugin marketplace add TanglmChris/keel --ref main --sparse .agents/plugins --sparse plugins/keel`, and no marketplace command runs

#### Scenario: Changed Codex hook definitions are named
- **WHEN** the new Codex plugin's `hooks/codex.json` differs from the installed one
- **THEN** the Codex line says Codex will ask for review in `/hooks` before the changed hooks run

#### Scenario: A failed host step fails the command and says which
- **WHEN** a host update command exits nonzero
- **THEN** that component's line reads `failed` with the command, the other components still report, and `keel --update` exits nonzero

#### Scenario: A dry run runs nothing
- **WHEN** `keel --update --dry-run` runs
- **THEN** it prints the planned CLI and host commands and invokes no host command and no install

#### Scenario: A failed Codex refresh is retried once
- **WHEN** `codex plugin marketplace upgrade` fails once and then succeeds
- **THEN** it runs twice, `codex plugin add` runs once, the Codex line reports the new version, and `keel --update` exits 0

#### Scenario: A lasting Codex refresh failure names the sparse remedy
- **WHEN** `codex plugin marketplace upgrade` fails on both attempts
- **THEN** it runs twice, `codex plugin add` does not run, the Codex line reads `failed` and names `sparse_paths`, `.agents/plugins` and `plugins/keel`, and `keel --update` exits nonzero

#### Scenario: A hung host query is a failure, not an absent host
- **WHEN** `codex plugin list --json` does not return within the query limit and Codex's config and cache show no Keel install
- **THEN** the Codex line reads `failed`, names `codex plugin list --json` and the limit, does not read `absent`, no Codex update command runs, the Claude line still reports, and `keel --update` exits nonzero

#### Scenario: A hung query does not stop an update Codex's own state can carry
- **WHEN** `codex plugin list --json` does not return within the query limit, Codex's `config.toml` declares `[marketplaces.keel-marketplace]` with `source_type = "git"`, and its plugin cache holds Keel 5.0.0
- **THEN** `codex plugin marketplace upgrade keel-marketplace` and `codex plugin add keel@keel-marketplace` each run once, and the Codex line reports `5.0.0 -> 5.1.0` read from the plugin cache and says `codex plugin list --json` did not answer
- **AND THEN** `keel --update` exits 0

#### Scenario: A failed Claude refresh is retried once
- **WHEN** `claude plugin marketplace update` fails once and then succeeds
- **THEN** it runs twice, `claude plugin update` runs once, the Claude line reports the new version, and `keel --update` exits 0

#### Scenario: A lasting Claude refresh failure says so with the host's error
- **WHEN** `claude plugin marketplace update` fails on both attempts
- **THEN** it runs twice, `claude plugin update` does not run, the Claude line reads `failed`, says it failed twice and carries the host's last stderr line, and `keel --update` exits nonzero

#### Scenario: A failed host step names the host's error
- **WHEN** `claude plugin update` exits 1 after writing to stderr
- **THEN** it runs once and the Claude line reads `failed`, naming the command, `exited 1`, and the last stderr line

#### Scenario: A query that times out once is retried
- **WHEN** `codex plugin list --json` exceeds the query limit once and then answers
- **THEN** the Codex plugin is updated, its line reports the new version, and `keel --update` exits 0
- **AND THEN** a query that exceeds the limit on both attempts runs twice and the Codex line reads `failed`, saying it timed out twice and naming the limit

#### Scenario: A version the registry does not serve yet is pending, not failed
- **WHEN** `claude plugin update` exits 1 with `E404 No match found for version 5.2.0` and `npm view @christang/keel version` answers 5.1.0
- **THEN** the Claude line reads `pending`, names 5.2.0 and 5.1.0, says to rerun `keel --update` in a few minutes, and does not read `failed`
- **AND THEN** the CLI line names 5.1.0 as the npm registry's latest, the Codex line still reports, and `keel --update` exits 0

#### Scenario: An E404 the registry cannot explain stays a failure
- **WHEN** `claude plugin update` exits 1 with `E404 No match found for version 5.2.0` and `npm view @christang/keel version` answers 5.2.0, or exits nonzero
- **THEN** the Claude line reads `failed` with the host's error, and `keel --update` exits nonzero

#### Scenario: An install that did not take is not reported as updated
- **WHEN** the global prefix holds 5.0.0, `keel --update` packs 5.1.0, and `npm install -g` exits 0 leaving the prefix at 5.0.9
- **THEN** the CLI line reads `failed`, names the prefix's `package.json` and `5.0.9`, and the command exits nonzero
- **AND THEN** when the install leaves 5.1.0, the line reads `updated 5.0.0 -> 5.1.0`, its before version read from the prefix rather than from the running copy

### Requirement: Both READMEs state the CLI and carry the same sections
`README.md` MUST name every subcommand and flag that `keel --help` lists, every standing-authorization name the code accepts, and every exit code the CLI returns, and MUST NOT restate a limit the protocol removed. `README.zh-CN.md` MUST meet the same command and name checks and carry the same number of `##` and `###` sections as `README.md`.

#### Scenario: The English README states the CLI
- **WHEN** `keel --help` lists a subcommand or flag, or `src/core/config.js` accepts a standing-authorization name
- **THEN** `README.md` names it
- **AND THEN** the README's count of authorization names equals the code's, and it describes exit codes 0 through 4

#### Scenario: The Chinese README matches the English one
- **WHEN** the validator reads `README.zh-CN.md`
- **THEN** it names every subcommand, flag, and authorization name the English README must name
- **AND THEN** its `##` and `###` section counts equal those of `README.md`

### Requirement: The configuration file and the Chinese docs follow their sources
`keel/config.yaml` MUST document each declaration in `CONFIG_DECLARATIONS` exactly once, in that order. Each `docs/*.zh-CN.md` MUST carry the same number of headings and code fences as its English page and name every `keel` command that page names.

#### Scenario: The configuration file documents its declarations in order
- **WHEN** the validator reads the `# <name> (optional):` comment blocks of `keel/config.yaml`
- **THEN** each declaration of `CONFIG_DECLARATIONS` has exactly one, in that order

#### Scenario: A Chinese doc matches its English page
- **WHEN** `docs/<page>.zh-CN.md` exists
- **THEN** its heading and code-fence counts equal those of `docs/<page>.md`
- **AND THEN** it names every `keel` command `docs/<page>.md` names

### Requirement: A release completes only once the registry serves its version

The publish job MUST, after `npm publish` and before it tags and creates a release, wait until `npm view @christang/keel@<version> version` on registry.npmjs.org prints that version, polling at a fixed interval up to a time limit. A poll that exits nonzero MUST count as not yet served. When the limit passes first, the job MUST fail before the tag and the release are created, naming the version and the limit. The wait MUST be skipped exactly when the publish is skipped.

#### Scenario: The wait ends when the registry serves the version
- **WHEN** `scripts/await_registry.js @christang/keel 5.2.0` runs against an npm whose `npm view @christang/keel@5.2.0 version` fails twice with E404 and then prints 5.2.0
- **THEN** it polls three times and exits 0

#### Scenario: A version the registry never serves fails the wait
- **WHEN** the same npm never prints the version within the time limit
- **THEN** `scripts/await_registry.js` exits nonzero, naming the version and the limit

#### Scenario: The release waits for the registry
- **WHEN** `.github/workflows/publish.yml` is read
- **THEN** a step running `scripts/await_registry.js` for the planned version sits after the `Publish` step and before `Tag and release the landed version`, under the same skip condition as `Publish`

### Requirement: An update names the sessions on an older plugin and adopts the idle ones on request
`keel --update` MUST name the Claude Code background sessions started before the installed Keel plugin's `lastUpdated`. With `--adopt` it MUST restart each idle one with `claude stop`, waiting for its process to exit, then `claude --bg --resume <session id>` with no prompt and no other flag. It MUST leave a busy or waiting session, one whose worktree has `keel/guard.json`, and its own session, and name them.

#### Scenario: Adopting restarts only the idle sessions on the older plugin
- **WHEN** after the Claude plugin update, `claude agents --json` lists an idle, a busy, and a guarded session started before `lastUpdated`, an idle one started after it, and the session running the command, and `keel --update --adopt` runs
- **THEN** only the idle older session is stopped and, once its process has exited, resumed with `--bg --resume <its id>` and nothing else
- **AND THEN** the line names it as adopted and the busy and guarded sessions as left, and the command exits 0

#### Scenario: Without adopting, the older sessions are only named
- **WHEN** the same sessions are listed and `keel --update` runs without `--adopt`
- **THEN** no session is stopped or resumed
- **AND THEN** one line names the sessions started before the update and that `keel --update --adopt` restarts the idle ones

### Requirement: A skill's plugin copy carries every file of its source
For every Keel skill, the plugin copy under `plugins/keel/skills/<skill>/` MUST hold the same set of files as `src/skills/<skill>/`, and each file in the copy MUST have the same bytes as its source, except that a copy's `SKILL.md` MAY add the Claude-only frontmatter fields `user-invocable` and `argument-hint`, which the portable source MUST NOT carry; with those lines removed, its bytes MUST equal the source's. `native-plugin-manifests` and `skill-portability-policy` MUST fail and name the file when one is missing from the copy or differs from its source by anything else.

#### Scenario: A split-out file missing from the plugin copy is caught
- **WHEN** `src/skills/review-checklist/conditional-checks.md` exists and the plugin copy lacks it
- **THEN** `native-plugin-manifests` fails, naming `conditional-checks.md`

#### Scenario: Claude-only fields stay in the plugin copy
- **WHEN** the plugin copy of `review-checklist/SKILL.md` adds `user-invocable: false` to the source's frontmatter, and the source carries neither Claude-only field
- **THEN** both checks pass, and they fail when the source carries `user-invocable` or the copy differs by any other line

### Requirement: The review checklist loads its conditional checks on demand
The review checklist's `SKILL.md` MUST keep its base checks and MUST name four conditions:
- `Coupling: required`;
- a matching domain lens;
- a new or materially expanded skill;
- an accepted plan-mode artifact.

The criteria that apply only under those conditions MUST live in `conditional-checks.md` beside `SKILL.md`, which is read only when a condition applies. The handoff skill MUST tell the HANDOFF override apart from the shift note.

#### Scenario: The base checklist names the conditions and not their criteria
- **WHEN** the review checklist skill is read
- **THEN** `SKILL.md` names `conditional-checks.md` and its four conditions, and holds no `## Skill change review` or `## Planning artifact funnel` section
- **AND THEN** `conditional-checks.md` holds those sections with their criteria
- **AND THEN** the handoff skill names `keel shift ready` and says that the shift note selects no task

### Requirement: The slash menu offers what a person runs

The plugin MUST ship the skills `align-expectations`, `debug-failure`, `handoff`, `review-checklist`, and `tdd-or-test-first`, with no `keel-` prefix on their names, so that each one is invoked as `/keel:<name>`. `debug-failure`, `review-checklist`, and `tdd-or-test-first` MUST declare `user-invocable: false`, so that only the model invokes them. `align-expectations` and `handoff` MUST stay user-invocable and declare an `argument-hint`. The Claude plugin MUST ship the commands `shift`, `context`, `start`, `done`, and `chat`, and each of the four new ones MUST name the `keel` command it runs: `keel context`, `keel gate task-start`, `keel gate task-complete`, and `keel chat unread`. The plugin MUST NOT ship a Markdown-to-Word skill. `keel docx` MUST print that it was retired and exit nonzero. `docs/commands.md` and `docs/commands.zh-CN.md` MUST list every command and skill a person can invoke.

#### Scenario: The plugin ships the renamed skills and the new commands
- **WHEN** the packaged plugin's skills and commands are read
- **THEN** the skills are exactly the five names without a `keel-` prefix, with `user-invocable: false` on the three model-only ones and an `argument-hint` on the other two; the commands are exactly `shift`, `context`, `start`, `done`, and `chat`, each new one naming its `keel` command; and `claude plugin validate` passes on the plugin directory

#### Scenario: The retired export says so
- **WHEN** `keel docx setup` or `keel docx convert a.md` runs
- **THEN** it prints that `keel docx` was retired and exits nonzero, and installs or converts nothing
