# Keel Changelog

## 5.1.2 - CI: automated npm trusted publishing

- Added a GitHub Actions workflow (`.github/workflows/publish.yml`) that publishes the package to npm via OIDC trusted publishing when a GitHub Release is published, after running the full validation suite and asserting the release tag matches the package version.
- Version alignment: the npm package, both native plugin manifests, protocol docs, and this changelog share Keel 5.1.2; the OpenSpec dependency pin stays `^1.4.1`.

## 5.1.1 - public-release preparation: MIT relicense, bilingual README, documentation accuracy, privacy scrub

- Relicensed under MIT: a root `LICENSE` file is added and the npm package plus both native plugin manifests share the `MIT` SPDX id (previously `UNLICENSED`).
- The README is split into an English front page (`README.md`, now the default) and the comprehensive Chinese manual (`README.zh-CN.md`), both rewritten around the v5 native-plugin surface with a shared language switcher; the feature-documentation validators (`native-tasks-view`, `plan-funnel-guidance`, `domain-execution-references`, `precompact-probe`, `touch-guard-surface`, `validation-runner`, and the Dedicated Skill Policy check) now assert against the Chinese manual.
- Documentation accuracy: the target table, install-output list, and the retired `UserPromptExpansion` sync/archive hook claims across the README and `AGENTS.md` now match the real v5 install path — `keel --init` writes only the AGENTS.md bootstrap, the CLAUDE.md import, `openspec/config.yaml`, and the schema/overlay; execution skills and the SessionStart/PreToolUse hooks ship in the plugin; and `/opsx:sync`/`/opsx:archive` completion gates through `keel gate change-close` plus `keel-review-checklist` (capability `manual` on every target).
- Removed the orphaned v3 `.agents/keel/keel-adapter.js`; the Codex `.agents/plugins/marketplace.json` stays canonical.
- Privacy for the public repository: scrubbed the Windows username and personal path placeholders from tracked archive documents, and added `.claude/settings.local.json` to `.gitignore`.
- Version alignment: the npm package, both native plugin manifests, protocol docs, and this changelog share Keel 5.1.1; the OpenSpec dependency pin stays `^1.4.1`.

## 5.1.0 - authoring-artifact scope exemption, parallel validation runner, recorded contract anchor, spec-traceable validator pins

- `task-complete --base` no longer attributes changed paths under the selected change's own `openspec/changes/<change>/` directory as outside-Touch scope failures, so a change can be completed under an explicit base before its authoring commits land; other changes' directories, the archive tree, specs, and schemas stay attributable and no-base behavior stays warning-only. The tracked v3-era `.agents/skills/keel-*` copies are removed (the native plugin distribution stays canonical). (exempt-authoring-artifacts-and-clean-agents-legacy)
- `validate_plugin.py` gains one ordered scenario registry driving `--scenario` dispatch and a new `--all [--jobs N]` runner that executes every scenario as a parallel subprocess, fail-loud, with output replayed in registry order; `npm test` becomes a single `--all` invocation and drops from 3-4 minutes to roughly 25 seconds. Registration is enforced through registry membership instead of grepping the npm chain. (consolidate-and-parallelize-validation-runner)
- `keel gate task-start --record` writes the compiled capsule fingerprint into the selected task's Evidence by replacing exactly its literal `- Contract: pending` line; a non-pending or missing anchor refuses deterministically and writes nothing. The capsule fingerprint excludes Evidence values, so recording never drifts the contract or an active guard. The permitted gate writes become the disposable guard manifest plus this opt-in anchor replacement. (record-contract-anchor-on-task-start)
- The `expectation-alignment-skill` validation asserts only document structure and spec-traceable contract anchors — each retained literal cites the `keel-expectation-alignment` requirement or scenario that names it — instead of pinning roughly forty sentence-length and common-word phrases, so editorial rewording no longer forces paired validator edits. (pin-skill-validation-to-contract-anchors)
- Version alignment: the npm package, both native plugin manifests, protocol docs, and this changelog share Keel 5.1.0; the OpenSpec dependency pin stays `^1.4.1`.

## 5.0.0 - retire grill, thin execution skills to contract content

- **BREAKING** `keel-grill-open-questions` is retired: the source skill, plugin distribution copy, CLI/installer listings, and all schema/docs references are removed. `keel-align-expectations` deep alignment is the only question-loop entry. `keel --install`/`--init` removes byte-identical previously packaged copies (v4 redirect and v3 dist variants) from target repos and preserves user-modified copies with a manual migration warning, mirroring the v4 profile-retirement pattern; the new `grill-retirement` scenario locks the surface absence, fresh-install behavior, both target migrations, and the preserve path. (retire-grill-and-thin-execution-skills)
- `keel-tdd-or-test-first`, `keel-debug-failure`, and `keel-align-expectations` are thinned to Keel-unique contract content: procedural teaching the host runtimes now natively provide (red-green loop mechanics, horizontal-slicing narrative, mocking tutorial, generic diagnosis and interview mechanics) is dropped or demoted to a one-line ownership boundary, while the Verify strategy taxonomy, per-label red/green evidence contract, capsule binding, domain-reference hooks, retry fuse, checkout preservation, failure-report shape, materiality routing, candidate-expectation rule, D/F/A/Q provenance, and write-back ownership stay intact. No skill names or requires a host-native skill, so Codex/OpenCode portability is unchanged.
- Version alignment: the npm package, both native plugin manifests, protocol docs, and this changelog share Keel 5.0.0; the OpenSpec dependency pin stays `^1.4.1`.

## 4.3.0 - native tasks view and guard-manifest scope exemption

- `keel project tasks --target claude` compiles a disposable `keel-native-tasks/v1` checklist view from the selected change's tasks.md — ordered task ids, titles, checkbox state, the default-selected task, and the source fingerprint — for the current agent to mirror manually into host-native task tools. Claude target only; read-only, never persisted, no synchronization loop, and host-side disagreement is projection evidence that never writes back. (project-native-tasks-view)
- `task-complete --base` no longer attributes `keel/guard.json` — the one artifact the gate contract itself permits a gate to write — as an outside-Touch scope failure, so default-guarded tasks complete without a manual `keel guard clear`. The exemption is the exact literal path in `scopeEvidence`; guard lifecycle is unchanged. (exempt-guard-manifest-from-scope-comparison)
- Version alignment: the npm package, both native plugin manifests, protocol docs, and this changelog share Keel 4.3.0; the OpenSpec dependency pin stays `^1.4.1`.

## 4.2.0 - post-audit hardening (touch write guard, compaction continuity, execution-phase domain references, surface alignment)

- `keel guard start|status|clear` turns Touch from discipline into deterministic interception on the Claude target: `guard start` requires a passing `task-start` compile, writes a one-shot `keel/guard.json` (`keel-write-guard/v1` with change/task, capsule fingerprint, normalized Touch, and authority-file hashes), and the plugin `PreToolUse` hook then deterministically rejects `Edit`/`Write`/`NotebookEdit` outside Touch with exact paths and recovery commands. Fingerprint or authority drift invalidates the guard instead of enforcing a stale contract. (enforce-touch-write-guard)
- Post-compaction continuity is source-aware: the SessionStart hook distinguishes startup, resume, clear, and compaction sources and reinjects only the authoritative continuity pointer after compaction, with honest pre-compaction capability reporting instead of claiming probes it cannot run. (wire-compaction-continuity-projection)
- Domain references (web, hardware, hardware DSL) extend beyond authoring into execution and review phases, loaded only when the selected task touches the matching domain. (extend-domain-references-to-execution)
- The managed bootstrap marker is single-sourced from `assets/bootstrap/AGENTS.md`, README and surface docs align with the v4 runtime, and plan-mode output funnels into OpenSpec authority instead of remaining chat-only. (align-v4-surface-docs-and-markers)
- Version alignment: the npm package, both native plugin manifests, protocol docs, and this changelog share Keel 4.2.0; the OpenSpec dependency pin stays `^1.4.1`.

## 4.1.0 - native-single-task-goal-execution

- `keel project goal --target codex|claude --change C --task T` compiles one authorized task capsule into a disposable `keel-native-goal/v1` projection (objective, Acceptance, command labels, verification strategy, Touch, stop boundary, current-agent ownership, and a terminal completion condition); OpenSpec, Git, the capsule fingerprint, and deterministic gates stay the only durable authority.
- The native goal is target-neutral and normalizes to the same semantic fields on Codex and Claude; Claude conditions above 4,000 characters are refused rather than truncated, and OpenCode stays manual compatibility only. Continuity is reconstructed from OpenSpec and Git, with `--expected-fingerprint` and `--expected-owner` hard-stopping on drift, divergence, missing authorization, or a completed task instead of chaining to a next task.
- `keel project helper` compiles a bounded read-only `keel-helper-brief/v1` for one question or one repository-byte-stable command, and `keel project helper --verify` accepts a return only after before/after repository byte identity, reporting exact changed paths without cleanup. Helpers never write products, delegate, nest, or hold completion authority, and helper absence never disables current-agent goal execution.
- New portable `keel-run-single-task-goal` skill and thin Codex/Claude activation adapters own the single-task lifecycle, positive/negative triggers, and manual fallback; `keel capabilities` reports helper discovery, tool restriction, nested-delegation prevention, byte-stability, and enforced/advisory/manual levels separately.
- Version alignment: the npm package, both native plugin manifests, marketplaces, diagnostics, bootstrap marker, docs, and changelog share Keel 4.1.0 while OpenSpec stays 1.5.0-integrated; no goal scheduler, cursor, queue, global Stop hook, or OpenCode automation is introduced.

## 4.0.0 - native-plugin-packaging

- **BREAKING** Keel ships as one canonical dual-runtime native plugin at `plugins/keel` (`.codex-plugin/plugin.json` + `.claude-plugin/plugin.json`) discovered through repo marketplace catalogs; skills and the SessionStart hook are plugin-owned.
- **BREAKING** The custom distribution is retired: the root `plugin.json`, `dist/` projections, the `build_plugin.py` builder, `src/adapters`, `src/hooks`, and the duplicate full-protocol assets are removed. Migration removes byte-matching packaged v3 skill/adapter/hook copies and preserves user-modified copies with exact-path warnings; existing OpenCode files are left untouched and outside v4 support.
- `keel --init/--install` is a thin host operation: it installs the official OpenSpec 1.5.0 schema, managed overlays, one sub-1KB `AGENTS.md` bootstrap block, and one Claude `@AGENTS.md` import; it no longer copies Keel skills, hooks, adapters, or full protocol payloads.
- `keel --doctor` reports native plugin source/runtime, bootstrap, Claude import, OpenSpec, and legacy-migration surface states from probes rather than copied trees.
- The npm package ships only the thin CLI/Core, schema, bootstrap, native plugin, and docs; the executable `@christang/keel` CLI and the native plugin are installed separately and share the base version.

## 4.0.0 - align-expectations-before-specs

- New `keel-align-expectations` skill owns the pre-spec/pre-task checkpoint: quick path for complete low-risk requests, deep path asking one material decision at a time with recommendations; repository facts are inspected before user questions and inferred candidates stay unauthorized until accepted.
- **BREAKING** `--profile` is removed; web/hardware/hardware-dsl guidance ships as on-demand references inside the alignment skill. Migration removes packaged-identical legacy profile copies and preserves user-modified copies with a warning.
- `keel-grill-open-questions` is a compatibility redirect to the alignment deep path.
- Codex and Claude OpenSpec propose surfaces gain a managed Keel Authoring Overlay; the apply overlay now returns newly discovered material expectations to alignment. OpenCode keeps portable artifacts only.
- Forward-test evidence for the skill lives under keel/archive/skill-evidence/.

## 4.0.0 - repair-and-thin-task-contract

- Compact v4 task source form: tasks record Covers, Touch, Verify (Strategy plus M<n> checks), and an Evidence anchor; omitted fields inherit versioned `keel-task-capsule/v1` defaults.
- Compatible expanded v3 tasks compile through the same parser; contradictory legacy fields fail with migration diagnostics. OpenSpec 1.5.0 is the authoring/validation baseline.
- `keel gate task-start` returns the compiled capsule and deterministic fingerprint; the recorded Evidence Contract anchor gates resume, HANDOFF continuation, projection, and completion, and drift hard-stops until explicit reauthorization.
- `keel gate task-complete` enforces strategy-aware evidence: red-green strategies need concrete per-label `.red`/`.green` records; unsupported strategies fail task-start.
- `keel context` excludes storage-only zero-checkbox backlogs from inference with a warning while keeping explicit selection and authoring changes actionable.
- OpenCode keeps manual compatibility only; this change ships no native goal/plugin automation.

## 3.0.0

- Continuity is recomputed by `keel context`; new installs omit HANDOFF and preserve legacy files.
- Shared read-only Core gates expose task-start, task-complete, and change-close.
- Target adapters and doctor use capability evidence with conservative manual fallback.
- Codex and Claude projection is one-way, disposable, and explicitly authorized for goal/task/subagent views.
- Risk-triggered authoring guidance keeps accepted hidden knowledge in durable OpenSpec artifacts.
- Optional `web`, `hardware`, and `hardware-dsl` profiles are packaged but never installed implicitly.
