## Context

Issue #34 separated four causes of interruption. 5.5.0 addressed the one that is a missing
declaration: an action the owner authorized had nowhere durable to live. This change addresses the
one that is a missing memory: a *decision* the owner made had nowhere durable to live either, so
the same question returns after every context reset and the reasoning that settled it is lost.

The owner's three rules were accepted on issue #34 before any design existed. This document turns
them into requirements and chooses the mechanism, which turned out to be one the repository already
has rather than one to invent.

## Goals / Non-Goals

**Goals:**

- A decision, and the reasoning behind it, survives a context reset in a form Keel can find.
- A precedent surfaces at the moment a similar decision is being made, not at every session start.
- Applying a precedent to a decision that would otherwise have interrupted the owner is visible in
  one line.
- Nothing is authorized by accumulation; promotion is an owner act.
- A repository that declares no store behaves exactly as it does at 5.5.0.

**Non-Goals:**

- Creating or seeding the owner's private store. That is a repository action, and this change must
  not require it to be complete.
- Any network access from a hook or gate.
- Deciding for the owner whether one store serves all their projects or each project keeps its own.
  A declarable path makes that a deployment choice rather than a spec fork.
- `/loop` orchestration (issue #34 layer L3).

## Decisions

- **F1** — Domain lenses are the existing instance of this pattern: user-authored markdown in
  `keel/lenses/*.md`, self-describing through an `Applies when:` header, only the matching lens
  loaded, none bundled, `keel lenses list|add` for management, and a `keel --doctor` lens surface.
  Requirements at `openspec/specs/keel-domain-lenses/spec.md:23-65`; templates at `assets/lenses/`.
  Basis: read 2026-07-29.
- **F2** — `src/core/config.js` exists as of 5.5.0 with a hand-rolled line-oriented reader over
  `keel/config.yaml`, shared by `bin/keel.js` and `src/core/task-contract.js`. Basis: shipped in
  this repository's 5.5.0 release.
- **F3** — The SessionStart hook has a 15-second timeout (`plugins/keel/hooks/hooks.json:11`), runs
  on every session including post-compaction reinjection, and emits a human-visible
  `systemMessage` beside the model-visible `additionalContext`. Basis: shipped in 5.4.0; read
  2026-07-29.
- **F4** — The nine-category materiality list lives at
  `src/skills/keel-align-expectations/SKILL.md:14`. Basis: read 2026-07-29.

- **D1 — A precedent store is a sibling surface to lenses, not a reuse of them.** It shares the
  mechanism — declared directory, self-describing header, match-then-load, nothing bundled — and
  differs in two ways that make sharing the file space wrong: precedents accumulate over time
  rather than being authored once, and each carries a promotion state a lens has no concept of.
  Basis: F1 plus the accepted rules on issue #34.
- **D2 — The store path is declarable, where the lens path is fixed.** `keel/lenses/` is
  necessarily in-repo because a lens describes that repository's domain. A precedent describes how
  its owner decides, which is not repository-scoped, and the owner asked for one private store
  across environments. Basis: the owner's stated goal on issue #34; a declarable path also makes
  "one store for everything" and "one store per project" the same mechanism.
- **D3 — Keel reads a local directory and nothing else.** How the directory came to exist — a git
  clone, an installed plugin, hand-authored files — is outside Keel. Basis: a hook or gate that
  reaches the network trades the local, offline, deterministic properties that make those surfaces
  trustworthy (issue #33), and a 15-second SessionStart budget (F3) cannot absorb a fetch that
  fails on VPN, expired credentials, or a plane.
- **D4 — A precedent record must carry its rationale, and one that carries only a conclusion is
  reported incomplete.** A record saying "chose A" cannot be applied to a situation that is not
  literally the recorded one; "chose A because B fails offline" can. Basis: accepted as D4 on issue
  #34; this is the field that decides whether the store accumulates value or noise.
- **D5 — Citation triggers on "would otherwise have interrupted the owner".** Applying a precedent
  is stated explicitly exactly when the absence of that precedent would have produced a question.
  Basis: accepted on issue #34. Citing every routine decision makes citation noise and destroys the
  signal; citing none hides what the agent decided on the owner's behalf. The trigger selects
  precisely the set where the agent acted in the owner's place.
- **D6 — Promotion is owner-accepts-agent-proposal, never a usage threshold.** A precedent is
  `recorded` when written and becomes `authorized` only through an explicit owner acceptance of a
  proposal the agent makes. Basis: accepted on issue #34. A threshold crosses without anyone
  watching, which is the property that makes it unsafe rather than the count itself.
- **D7 — A precedent answers a recurrence within a materiality category and never moves a decision
  out of the list.** The category is a required field precisely so this is checkable. Basis:
  accepted on issue #34; without a fixed point the system drifts toward asking nothing, and the
  drift is slow enough to be invisible.
- **D8 — SessionStart carries a pointer only.** Count, authorized count, and last-sync — never
  bodies. Basis: F3's per-session cost and the fact that a store grows monotonically while the
  precedents relevant to any one session are a small subset. Bodies load on match, as lenses do.
- **D9 — A precedent has no power over gates, evidence, Review, or the write guard.** It informs a
  decision; it never substitutes for a proof. Basis: the boundary 5.5.0 drew for standing
  authorization, for the same reason — the owner's intent is to avoid being asked, never to avoid
  being told when something fails.
- **D10 — Nothing is bundled and nothing is on by default.** Keel ships no precedent and no store.
  Basis: F1's precedent with lenses, and the owner's requirement that other users get the interface
  only.

## Hidden Knowledge / Assumptions

- **A1** — The store is maintained as an ordinary git working copy by its owner; Keel neither
  clones, pulls, nor writes to a remote. Staleness is therefore possible and must be *visible*
  rather than corrected: the surfaces report a last-sync time and never block on it. Basis: D3.
  Owner: the store's own repository; this change adds no sync mechanism and must not add one
  silently.
- **A2** — A precedent file is authored by a human or written by the agent at the owner's
  instruction, and is reviewed like any other tracked file. Keel does not validate that a rationale
  is *good*, only that it is present. Basis: D4 is a structural check, not a semantic one. Resolve
  by: the specs state the incompleteness check as a shape check, so no reader infers that Keel
  judged the reasoning.

## Risks / Trade-offs

- **A precedent applied to a decision that only resembles the recorded one.** This is the failure
  the whole design is arranged against: D5 makes every consequential application visible in one
  line, D7's category field makes "same kind of decision?" a checkable question, and D6 keeps the
  auto-applicable set small and owner-chosen. Accepted residual risk: a wrong application that the
  owner does not read. It is one line in the transcript rather than silence, which is the best
  available outcome short of not applying precedents at all.
- **The store grows and its value per file falls.** No mitigation beyond D8's pointer and
  match-then-load. Accepted: a store that is never pruned is still strictly better than a decision
  that evaporated.
- **Two declaration surfaces in `keel/config.yaml`.** `authorize:` and the precedent store now
  share a file that held one key a release ago. Accepted: the file is the repository's Keel
  declaration, and splitting it would make the owner track two files to answer one question.

## Open Questions

- **Q1 — RESOLVED 2026-07-29, before any task started.** The question was whether this change could
  dogfood its own interface, since no precedent store existed. The owner authorised creating one,
  and `TanglmChris/decision-precedents` (private) now exists with its local working copy beside
  this repository. Task 4.2 was added to declare it, so the interface ships in use rather than only
  fixture-tested. **D11** follows from the resolution: because the store is a private repository
  that CI and any other clone will not have, declaring it here is only honest if an absent store is
  silent — so 4.2 must prove the declared-but-missing path degrades to the no-store behavior rather
  than to an error. That is the scenario a cloner and CI both land on.
