## Context

Keel stops for confirmation in four distinct places, and only one of them is Keel's own design.
Host permission prompts, OpenSpec's upstream confirmation prose, Keel's protocol hard-stops, and
the agent's own politeness all read the same to the user, but each has a different fix. Issue #34
separates them. This change addresses the part that is Keel's: there is no durable place to record
"you do not need to ask me this again", so an authorization granted in conversation dies at the
next `/clear`.

The vocabulary already exists at the task level. `src/core/task-contract.js:840-849` resolves an
`Autonomy boundary:` field and injects `Default: hard-stop` plus `Pre-authorized fallback: none`
when the task declares neither. What is missing is a repository-level default for that resolution
to inherit.

## Goals / Non-Goals

**Goals:**

- A repository declares standing authorization once, in a tracked file, for a closed set of named
  actions.
- A task with no explicit `Autonomy boundary:` inherits the declaration; a task that declares one
  keeps it.
- A reader of the compiled capsule or gate output can tell an inherited authorization from a
  task-authored one.
- The apply and archive overlays stop re-asking for a confirmation the declaration already grants.
- A repository that declares nothing behaves exactly as it does at 5.4.0.

**Non-Goals:**

- The precedent/sedimentation system (issue #34 layer L2). It will extend this declaration format,
  so designing it first would build on a format this change is still choosing.
- Making any gate weaker, optional, conditional, or network-dependent.
- Adding the `sync` surface to the overlay target list.
- Host-level permission configuration, which is `.claude/settings.json` and not Keel's product.

## Decisions

- **F1** — The OpenSpec surface overlay is generated in `bin/keel.js:1002-1066` and injected into
  the `propose`, `apply`, and `archive` command surfaces only (`OPENSPEC_OVERLAY_ACTIONS`,
  `bin/keel.js:68`). `sync` is not an overlay target even though `.claude/commands/opsx/sync.md:21`
  carries an `AskUserQuestion`. Basis: read 2026-07-29.
- **F2** — `keel/config.yaml` is parsed by `readFastCheck` (`bin/keel.js:1370-1380`), a single
  line-oriented regex over one key. There is no YAML reader in the repository. Basis: read
  2026-07-29.
- **F3** — `package.json` declares one runtime dependency (`@fission-ai/openspec`) and zero
  devDependencies. Basis: read 2026-07-29.
- **F4** — `.claude/commands/opsx/archive.md:37,48` instructs two separate confirmation prompts.
  Basis: read 2026-07-29.
- **F5** — The nine-category materiality list lives at
  `src/skills/keel-align-expectations/SKILL.md:14`. Basis: read 2026-07-29.

- **D1 — The declaration is a closed list of action names, not free-form.** `authorize:` holds a
  YAML list drawn from `commit`, `push`, `release`, `archive`. Basis: a closed vocabulary is the
  only form in which an unknown entry can be reported rather than silently granted or silently
  dropped; a free-form grant cannot distinguish a typo from a decision.
- **D2 — An explicit task-level `Autonomy boundary:` always wins.** The declaration supplies the
  default the task did not author; it never overrides one the task did. Basis: the task capsule is
  the authoritative contract for its own execution, and a repository default that could override a
  task's stated boundary would make the capsule unreadable on its own.
- **D3 — Authorization covers the action, never the proof of it.** A declared action still requires
  its gate to pass; no declaration suppresses evidence, Review, a gate result, or the write guard.
  Basis: the gates' value is that they are local, model-free, deterministic, and unconditional
  (issue #33). An authorization that could skip a gate would trade that for nothing — the owner's
  intent is to avoid being asked, not to avoid being told when something fails.
- **D4 — The capsule and gate output name the authorization source.** An inherited entry is marked
  as coming from the repository declaration rather than merged silently into the task's boundary.
  Basis: without this, a reader cannot distinguish "this task authorized a fallback" from "the repo
  authorizes it everywhere", which are different scopes of decision.
- **D5 — The config reader stays hand-rolled; no dependency is added.** Basis: F2 and F3. The format
  is one Keel controls and can keep line-oriented, so a YAML library would be the repository's
  first new dependency bought for a problem the repository created.
- **D6 — An unknown action name is a configuration error naming the accepted names.** It is neither
  a silent grant nor a silent ignore. Basis: a silent ignore turns a typo into an authorization the
  owner believes they granted and did not; the existing gate-rejection convention already names the
  field and its accepted forms (`keel-core-gates`, "Gate rejections for validated forms name the
  field and accepted forms").
- **D7 — The nine-category must-ask list constrains inference, not owner declaration.** Issue #34's
  rule that a precedent may never move a decision out of the materiality list (F5) binds the future
  precedent system. It does not bind what the owner may authorize explicitly: `release` is
  irreversible cost and remains declarable, because the owner writing it into a tracked file *is*
  the decision, not an inference about one. Basis: accepted on issue #34; the two mechanisms are
  deliberately not connected.
- **D8 — The overlay rule is conditional on a declaration existing.** The apply and archive
  overlays direct the agent to consult the declaration; with nothing declared, the surfaces behave
  as they do today. Basis: the overlay ships to every Keel consumer, and a default that removed
  confirmations would change behavior for repositories that never asked for it.
- **D9 — `archive` is in the vocabulary although issue #34 names only commit, push, and release.**
  Basis: the overlay half of this change exists to answer F4's two confirmation prompts, and
  without an `archive` action there is no declaration for that overlay rule to consult. The
  vocabulary is additive, so a later change may extend it without breaking a declaration.

## Hidden Knowledge / Assumptions

- **A1** — A widening of `authorize:` is caught the way any other tracked change is caught: it
  appears in a diff and in review. Basis: `keel/config.yaml` is committed, and this change adds no
  path that writes it programmatically. Owner: the repository's normal review process; this change
  adds no separate approval mechanism and must not add one silently.
- **A2** — Declaring an action does not make the agent perform it unprompted. It removes the
  confirmation, not the trigger; the action still happens only where the workflow already reached
  it. Basis: the declaration is read during autonomy resolution, which runs inside `task-start` for
  a task already selected. Resolve by: the specs state this as an explicit negative scenario, so a
  reader cannot infer a scheduler from an authorization.

## Risks / Trade-offs

- **Over-broad grant.** A declaration is a durable widening of what runs unattended, and it is
  easier to add than to remember. Mitigated by D1's closed vocabulary, D3's mandatory gates, and
  A1's tracked file. Accepted: the alternative in use today is a host-level bypass flag, which
  grants strictly more and records strictly less.
- **Inherited authorization mistaken for task-authored.** Mitigated by D4. The cost is that capsule
  output grows slightly.
- **Overlay churn.** The overlay marker embeds the package version (`bin/keel.js:70`), so every
  overlay-bearing file changes on release regardless. Adding a rule adds no new churn class.
- **The `sync` surface stays inconsistent.** `sync.md:21` keeps its `AskUserQuestion` while apply
  and archive learn to consult the declaration. Accepted for this change; adding a fourth overlay
  target is a separate decision with its own compatibility surface.

## Open Questions

None.
