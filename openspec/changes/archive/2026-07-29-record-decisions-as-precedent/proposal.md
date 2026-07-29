## Why

A decision the owner makes in conversation is spent the moment the context resets. The same
question gets asked again next session, and the reasoning that settled it — which is the part that
would generalize to a decision not yet seen — is gone entirely. 5.5.0 gave a repository a place to
declare *that* an action is authorized; it gave no place to record *why* a decision went the way it
did, or to have that reasoning surface when a similar decision comes up.

Keel already has the right mechanism and is not using it for this. Domain lenses are user-authored
markdown in a declared directory, self-describing through an `Applies when:` header, loaded only
when they match, with nothing bundled and nothing on by default. A precedent store is that same
shape with two differences that make it a sibling rather than a reuse: precedents accumulate rather
than being authored once, and each carries a promotion state a lens has no need for.

## What Changes

- A repository declares a **precedent store directory** in `keel/config.yaml`. Unlike
  `keel/lenses/`, the path is declarable rather than fixed, so one store outside the repository can
  serve several projects. Absent declaration means no store and no behavior change.
- Keel reads user-authored precedent files from that directory. Nothing is bundled; Keel ships no
  precedent, exactly as it ships no lens.
- Each precedent is self-describing: an `Applies when:` header naming the decisions it covers, the
  **materiality category** it belongs to, its **status** (`recorded` or `authorized`), the decision
  itself, and the **rationale**. A precedent recording only a conclusion is incomplete and is
  reported as such — the reasoning is the part that transfers to a decision not yet seen.
- `keel --doctor` reports the precedent surface: whether a store is declared, how many precedents
  it holds, how many are authorized, and when it was last synced.
- The SessionStart projection carries a **one-line pointer only** — count and last-sync — and never
  the precedent bodies. Bodies load at the moment a decision is being made.
- Three protocol rules from issue #34 become requirements:
  - **Citation**: applying a precedent is stated explicitly when, without it, the agent would have
    interrupted the owner. Decisions that would not have interrupted are not cited.
  - **Promotion**: `recorded` becomes `authorized` only by the owner accepting a proposal the agent
    makes. No usage count promotes anything.
  - **No reclassification**: a precedent answers a recurrence within a materiality category and can
    never move a decision out of the nine-category must-ask list.

No breaking change: a repository that declares no store behaves exactly as it does at 5.5.0.

## Capabilities

### New Capabilities
- `keel-decision-precedent`: how a repository declares a precedent store, what a precedent record
  must carry, when a precedent may be applied and must be cited, how promotion works, and what a
  precedent can never authorize.

### Modified Capabilities
- `keel-native-runtime-projection`: the SessionStart projection reports the precedent surface as a
  pointer and never carries precedent bodies.
- `keel-expectation-alignment`: alignment consults the matching precedent before escalating a
  decision the owner has already made, and records a new one when the owner makes a decision that
  is not yet covered.

## Impact

- **Code**: `src/core/config.js` (store declaration), `bin/keel.js` (doctor surface, `keel
  precedents` listing), `plugins/keel/scripts/session-start.js` (pointer), `src/skills/` and the
  distribution copies under `plugins/keel/skills/`, `scripts/validate_plugin.py`, `README.md`,
  `AGENTS.md`, `keel/CHANGELOG.md`.
- **Dependencies**: none added.
- **Risk — silent precedent application.** The failure this design most needs to prevent is a
  precedent being applied to a decision that only resembles the one it recorded. Mitigated by the
  citation rule making every consequential application visible in one line, by the category field
  making "is this the same kind of decision" checkable, and by promotion requiring an explicit
  owner act.
- **Risk — context cost that grows without bound.** A store accumulates. Mitigated by the
  pointer-only projection and by bodies loading on match, the same discipline lenses already use.
- **Risk — the store becomes an authority it was never granted.** Mitigated by the
  no-reclassification requirement and by precedents having no power over gates, evidence, or
  Review — the same boundary 5.5.0 drew for standing authorization.
- **Out of scope**: creating or seeding the owner's private store repository, which is a repository
  action and not a Keel change; any network access from a hook, which contradicts the local,
  offline, deterministic properties the gates depend on; and the `/loop` orchestration of issue
  #34's layer L3.
- **Authority**: issue #34 and its decision comment record the accepted rules this change
  implements.
