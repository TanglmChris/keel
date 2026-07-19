# keel-align-expectations v1 forward-test evidence

Date: 2026-07-12. Owner task: openspec/changes/align-expectations-before-specs/tasks.md#1.2.

Evaluation integrity: each case ran in an isolated read-only helper session that received only the raw prompt, a minimal verified project context, and the canonical skill path. Helpers did not receive intended answers, expected verdicts, or evaluator conclusions, were prohibited from product writes, OpenSpec edits, completion marking, and further delegation, and each confirmed a no-modification STOP statement. The evaluator judged returned reports against the rubric below after the runs.

Rubric per positive case: triggered correctly; asked only material questions (each with why-it-matters and a recommended answer); separated repository facts from user-owned product choices; produced observable acceptance including negative behavior; routed write-back to correct durable owners. Rubric per control: avoided an unnecessary interview and avoided artifact mutation.

## Positive case P1 — generic software (config format migration)

- Raw prompt: "我们的命令行工具目前用 config.ini 存配置。请把配置迁移到 config.yaml。" Context: Python CLI, configparser in src/config.py, no config tests, README documents ini keys, ~200 pip users.
- Triggered: yes; helper identified the hidden external-interface, migration, and dependency choices behind the one-liner.
- Path: deep, citing user-visible behavior, external interface, data migration, and dependency commitment triggers.
- Question materiality: 4 questions (compatibility cutover, migration mechanics, PyYAML dependency, versioning), each with why-it-matters and a recommendation; no stylistic questions; 1:1 key mapping stated as a labeled candidate, not silently assumed.
- Facts vs product choices: 6 repository facts (configparser usage/interpolation, path resolution, README key diff, packaging state, missing tests, existing OpenSpec artifacts) marked for inspection instead of asking; only residual product choices escalated.
- Observable acceptance: dual-read loading, deprecation warning, migrate-command idempotence and no-overwrite behavior.
- Negative behavior: malformed YAML produces a clear error naming file and line; both-present precedence defined.
- Durable write-back: proposal (scope/non-goals), design (D/F/A/Q with basis and risks), specs (load/fallback/migrate scenarios), tasks (Covers, test-first verification, stop boundaries); explicitly gated task executability on accepted questions because silence does not authorize the interface change.
- Verdict: pass.

## Positive case P2 — web/API (user list export button)

- Raw prompt: "在用户管理页面加一个'导出用户列表'按钮。" Context: React admin + REST, paginated /api/users, PII columns, admin/operator roles, ~80k rows.
- Triggered: yes; loaded exactly references/web.md and no other reference.
- Path: deep, citing new external interface, PII permission boundary, irreversible cost of 80k-row export, and observable acceptance changes; button placement/label kept quick as labeled non-material assumptions.
- Question materiality: 5 questions (role permission, export scope, format/encoding, sync-vs-async delivery, field set) in dependency order with recommendations; audit logging and rate limits labeled as candidate expectations requiring explicit acceptance.
- Facts vs product choices: 7 repository facts (existing export patterns, role enforcement shape, filter params, streaming facilities, audit mechanism, component/i18n conventions, column formats) reserved for inspection; permission choice correctly escalated as user-owned.
- Observable acceptance: role-gated button and 403 behavior, filter-honoring export, exact column/header/encoding contract.
- Negative behavior: API error yields a user-visible error state with no partial file; empty-result edge defined as headers-only file.
- Durable write-back: mapped per owner including rendered-page and route-contract verification per the web reference; task executability gated on the permission decision.
- Verdict: pass.

## Positive case P3 — hardware/generated artifact (DSL FIFO depth)

- Raw prompt: "把 DSL 模型里 axi_buffer 的 FIFO 深度从 16 改到 32，然后重新生成 RTL。" Context: DSL generates RTL and testbenches, golden byte-for-byte CI compare, downstream DMA latency assumption, regeneration script.
- Triggered: yes; loaded exactly references/hardware-dsl.md and no other reference.
- Path: deep, citing generated equivalence/golden re-baselining, timing semantics with an external consumer, and a contradiction between the one-line intent and repository facts (guaranteed golden divergence).
- Question materiality: 3 questions (golden re-baseline authorization, DMA assumption scope, motivating observable outcome) with recommendations; explicitly stopped questioning once the contract was writable.
- Facts vs product choices: 6 repository facts (parameter location/sharing, generator coverage and order, hand-edit status of generated files, encoded DMA assumptions, CI compare mechanics, derived-artifact naming) reserved for inspection.
- Observable acceptance: depth-32 full/empty scenarios, deterministic regeneration with no manual edits, simulation against new goldens, DMA-side check.
- Negative behavior: overflow behavior and unexpected regeneration diffs outside axi_buffer named as stop-and-return-to-authoring conditions.
- Durable write-back: proposal/design/specs/tasks mapping including Coupling of DSL source, generated RTL, and goldens as one candidate; unresolved DMA ownership recorded as a Q with a gate.
- Verdict: pass.

## Negative control N1 — routine one-line doc fix

- Raw prompt: "README.md 第 12 行 'recieve' 拼错了，帮我改成 'receive'。"
- Triggered: consulted the checkpoint but classified the request as quick-path routine work with no material choice; emitted one compact confirmation (goal, non-goals, acceptance, evidence, one labeled non-material assumption) without an interactive pause.
- Interview avoided: yes; zero questions asked, explicitly citing the skill's do-not-interview routing.
- Artifacts untouched: yes; no OpenSpec write-back proposed and no files modified; helper confirmed STOP.
- Verdict: pass.

## Negative control N2 — repository-answerable factual question

- Raw prompt: "我们这个项目单元测试用的是什么框架？" Context: pytest.ini and pytest-style tests present.
- Triggered: no; helper cited the skill's exclusion for facts the repository answers and answered pytest directly with its basis recorded as an F statement.
- Interview avoided: yes; zero questions asked.
- Artifacts untouched: yes; no OpenSpec mutation proposed; helper confirmed STOP.
- Verdict: pass.

## Unresolved findings: none

All five cases passed the rubric on the first run; no trigger or routing refinement was required, so no evidence-driven skill edit followed. One helper observation retained for context: N1's helper noted that a live run must base its F statements on its own reads when provided context and the working tree disagree — consistent with the skill's contradiction rule, no skill change needed.
