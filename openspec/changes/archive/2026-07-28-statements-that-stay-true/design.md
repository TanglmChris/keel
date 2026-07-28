## Context

Three unrelated reports turn out to share one shape: a durable statement that was true when written, is false now, and carries nothing that would tell a reader it had expired. This is the `## Invalidates` problem from 5.3.3 seen from the other end — those entries are declared by the change that causes the staleness, but nothing catches staleness that accumulated before the rule existed.

## Goals / Non-Goals

**Goals:**
- The bootstrap sentence is accurate without raising the budget.
- No live spec names a version that has shipped and moved on.
- Version alignment is checked rather than asserted, across every target.
- The fingerprint guarantee names the boundary it actually holds within.

**Non-Goals:**
- Raising the 1024-byte bootstrap budget. The user chose to make room instead.
- Making archived fingerprints reproducible (D4).
- Auditing every live spec for staleness of other kinds. This change fixes version pinning, which is mechanically findable; prose staleness is not.

## Decisions

- **F1** — The bootstrap block is 1016 bytes against a `< 1024` budget. Naming the exemption while keeping both guard opt-outs measures 1030; keeping only `--no-guard` measures **1012**. Basis: measured on 2026-07-28 against `thin-native-install`'s own byte rule.
- **F2** — Seven version-pinned statements sit in two live specs: `keel-expectation-slice-evidence-gates` pins `3.0.0` (and forbids `2.7.0`), `keel-native-plugin-package` pins `4.0.0` in three scenarios. Basis: `grep` for backticked semver across `openspec/specs/`. #22 reported one of them.
- **F3** — Archived anchors fail to reproduce because `resolveAuthority` records `source` as `openspec/changes/<change>/tasks.md#<id>`, and archiving renames `<change>` to `archive/<date>-<change>`. Basis: inspected the resolved authority of an archived task; the path is visible in every entry.
- **D1** — Make room in the bootstrap by listing `--no-guard` only. Basis: the user's decision. The exemption prevents a workflow-blocking misreading that costs a reauthorization; the second opt-out is a command still discoverable from `keel --help` and `keel guard status`. The lower-value sentence loses.
- **D2** — Replace the version-pinned requirement with the invariant it was reaching for: every shipped marker agrees with the package version. Basis: a requirement naming `3.0.0` is unfollowable at 5.3.4, but "the pins agree" is exactly what `bump_version.js` maintains and what #23 shows is unmaintained for `.codex/`. Rewriting keeps the intent; removing would drop it.
- **D3** — Enforce that invariant with a check over every marker the repository ships, and make `bump_version.js` refresh every initialized target. Basis: #23 recurred within one release cycle after a manual fix, twice in two days. A rule maintained by remembering is not maintained.
- **D4** — Document the fingerprint bound rather than restoring reproducibility. Basis: the only mechanism that would preserve existing anchors is normalizing an archived change's path back to its live form, which would make the displayed `source` name a path that does not exist. Trading an honest display for a corpus nobody needs at runtime is the wrong side of the trade; archived tasks are never resumed.

## Hidden Knowledge / Assumptions

- **A1** — Removing the `4.0.0` scenarios from `keel-native-plugin-package` deletes the only spec statement that pins plugin manifest versions. The replacement invariant covers them by construction, since both manifests are shipped markers. Basis: the manifests are already in `bump_version.js`'s pin list.
- **A2** — The marker-alignment check must scan the markers a release actually ships, not a hardcoded list, or it becomes the next thing to fall behind. Deriving the list is the point of the check, not an optimization.

## Coupled Iteration Contract

Not required; no coupled artifacts.

## Risks / Trade-offs

- **Dropping `keel guard clear` from the bootstrap** loses a discoverable command for consumers who never run `keel --help`. Accepted per D1; the misreading it buys out is worse and the command is unchanged.
- **A marker-alignment check will fail every release until `bump_version.js` runs.** That is intended — it is the signal #23 is missing — but it means the bump and the check must ship together, which is why they are one task.
- **Removing spec scenarios loses history.** Accepted: the archived changes that introduced them keep their text, and a live spec is a statement of what is required now.

## Open Questions

None.
