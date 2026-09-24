## Context

`authorize:` is a closed list of action names matched by exact membership. Every name in it today
describes an action the working checkout already bounds: `commit`, `push`, `release`, `archive`,
and `continuation` all act on this repository, and the declaration and the thing it permits are
the same size. A tracker write is the first entry where they are not.

## Goals / Non-Goals

**Goals:**

- A project can declare that the agent may open an issue, and the declaration says which
  repository that reaches.
- The unscoped form is refused rather than silently accepted, with the required form named.
- The existing fail-closed behavior, the inheritance into an unauthored Autonomy boundary, and
  every current entry's meaning are unchanged.

**Non-Goals:**

- Enforcement. Keel does not invoke `gh` and cannot observe one that runs; the scope is read and
  obeyed by the agent, as `commit` is.
- Closing, commenting on, labelling, or transferring issues; pull requests; anything
  cross-repository.
- Retro-scoping the existing entries. `commit` and `push` stay bare, because a resource name there
  would repeat what the checkout already says.

## Decisions

- **F1** — The vocabulary is a flat array of exact names at `src/core/config.js:10`, tested with
  `includes()` at `:181`. `configList`'s item pattern is `^\s+-\s*(\S+)\s*$`, so
  `issue:TanglmChris/keel` already arrives as one token: the reader needs no change, only the
  matcher does. Basis: read at 42389c6, 2026-09-24.
- **F2** — Three consumers read the declared list. `bin/keel.js:1791` loops the vocabulary and
  prints `declared.includes(action)`, so a scoped entry renders `issue` as `not authorized` unless
  that loop learns the form. `src/core/task-contract.js:1137` joins the list into the capsule's
  inherited `Standing authorization (keel/config.yaml): …` line, where a scoped string reads
  correctly as-is. `src/core/context.js:670` surfaces only the unknown-entry message. Basis: read
  at 42389c6.
- **F3** — One unrecognized entry voids the whole declaration (`src/core/config.js:184`), and the
  message names the entry plus the accepted names. Basis: read at 42389c6; asserted by the
  `standing-authorization-declaration` and `standing-authorization-sync-confusion` scenarios.
- **F4** — Closing an issue is not the gap. Every open PR in this repository carries a closing
  keyword — `Closes #133` on #139, `Closes #134` on #138, `Fixes #137` on #140 — so the issues
  close when the stack lands. What has no route is *creating* the issue that a `Durable owner:`
  must already point at. Basis: `gh pr view` on all three, 2026-09-24.
- **D1** — **`issue` is accepted only as `issue:<owner>/<repo>`.** A bare `issue` is an
  unrecognized entry and is reported with the required form. Basis: the decision recorded as
  `scope-a-grant-to-the-resource-not-the-credential` — a grant whose credential reaches further
  than the grant must name the resource, because the declaration's job is to record what it
  permits. Accepting the bare form as a convenience would make the narrow form optional and the
  wide one the default, which is the decision inverted.
- **D2** — **Keel authorizes and does not enforce, and the surfaces say so.** Keel never invokes
  `gh`. The scope is a declaration the agent reads and obeys, exactly as `commit` is one Keel
  never acts on. Basis: a reader who takes the scope for a sandbox would rely on a boundary
  nothing holds, which is worse than no entry at all — the same reasoning `keel/config.yaml`
  already applies to the delegation tier it cannot verify.
- **D3** — **The scope's shape is checked, its existence is not.** `<owner>/<repo>` must be two
  non-empty segments of `[A-Za-z0-9._-]`, and nothing more. Keel does not check that the
  repository exists, for the reason `triage` does not fetch an issue: a check that reaches the
  network trades the local, offline, deterministic evaluation the verdict rests on. Basis: the
  `triage:` rationale in `keel/config.yaml`, which this follows rather than restates.
- **D4** — **The doctor's per-action loop keys on the action name and reports the scope beside
  it.** `issue` prints `authorized` with `scoped to <owner>/<repo>`, so the line answers both
  questions a reader has. Basis: F2 — without this the loop reports `not authorized` for an entry
  the same command has just listed as declared, which is a diagnostic contradicting itself.
- **D5** — **This repository declares `issue:TanglmChris/keel`.** The repository that ships a form
  is the one that demonstrates it, as `keel/config.yaml` already records for `triage`'s bare-list
  form. Basis: that file's own stated reason, and F4's gap being live here.

## Hidden Knowledge / Assumptions

- **A1** — A project that wants the agent to file into a *different* repository's tracker — a
  monorepo's issues living elsewhere, or a fork reporting upstream — cannot express it: one entry
  names one repository, and a second `issue:` entry is accepted by the parser but has never been
  exercised. Basis: not measured; no such project is known here. Consequence if wrong: the
  declaration is too narrow and gets widened, which is the direction the precedent
  `declarative-authorization-over-blanket-bypass` explicitly prefers over a bypass. **Discarded
  as speculative** — building multi-entry semantics now would design for a case nobody has.

## Risks / Trade-offs

- **The scope is a promise, not a fence.** D2 is the honest statement of it and the surfaces carry
  it, but a reader who skims will still assume enforcement. The mitigation is wording, which is
  weaker than a mechanism and is the best available: Keel would have to wrap `gh` to do better,
  and wrapping the agent's tools is a much larger claim than this change makes.
- **`keel/config.yaml` stops being copyable verbatim** between projects once it carries a scoped
  entry. Accepted: the cost is one line a new project edits, against a grant that would otherwise
  silently be the widest entry in the file.
- **Exact-membership matching becomes two-shaped.** Every other entry is matched by identity and
  this one by prefix-plus-shape, so a future reader of `readStandingAuthorization` has two rules
  to hold. Mitigated by keeping the scoped form data-driven — the action declares that it requires
  a scope, rather than the matcher special-casing the string `issue`.

## Open Questions

None.
