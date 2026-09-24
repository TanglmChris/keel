## Context

Every other durable rule in Keel arrives somewhere the agent cannot miss: the bootstrap block
states it, a declaration in `keel/config.yaml` lets a project adjust it, and a gate checks the
result. Routing has none of the three. It is prose in Keel's own README, and a consuming project's
agent reaches the first decision of the session without it.

## Goals / Non-Goals

**Goals:**

- The routing rule is in the installed block, in one line, within the existing budget.
- A project can declare the paths the size heuristic gets wrong, each with the reason.
- The rule and the project's exceptions are both readable at the moment the decision is made.

**Non-Goals:**

- Enforcement. Routing decides whether a change exists; there is no change for a gate to bind
  to, and a gate that fired afterwards would be reviewing a decision already taken.
- Replacing the size heuristic. It stays, with the declaration as its correction.
- A `lite_mode_paths`, in any spelling.
- Deciding routing *for* the agent. Keel reports what is declared; the agent still reads the work.

## Decisions

- **F1** — `assets/bootstrap/AGENTS.md` is 9 lines, 5 bullets, and contains no routing content.
  Its budget is 12 managed-block lines, enforced by `RESIDENT_BLOCKS` in
  `scripts/validate_plugin.py:93`, whose `required` list pins the topics it must keep. Basis: read
  at dd63247, 2026-09-24.
- **F4** — The block carries a **second budget**, which F1 missed: `thin-native-install` and
  `delegation-resident-text` each independently assert it is under **1024 bytes**. Measured at
  dd63247: the block is **1014 bytes — 10 bytes of headroom** — over five bullets of 148, 326, 139,
  144, and 181 bytes. So any addition at all exceeds it, and a shorter line is not a fix. Basis:
  measured 2026-09-24, after the first implementation attempt turned both scenarios red at 1348
  bytes.
- **F5** — The repository had already faced this trade and declined to spend the budget.
  `delegation-resident-text` records why the bootstrap omits the delegation clause: *"delegation is
  inert until declared, so an installing repository that declares nothing is fully served by the
  sentence already there. What the check enforces is that the sentence stays true by default, and
  that the budget is not quietly spent later."* Routing differs on exactly the distinguishing
  point — it is never inert, and every session routes whether anything is declared or not. Basis:
  read at `scripts/validate_plugin.py:18071`.
- **F2** — Routing has no implementation. `grep -rn "Full mode\|Lite mode\|full_mode\|routing"`
  over `src/` and `bin/` returns two hits, both unrelated prose inside skills. The rule exists at
  `README.md:271` and nowhere else that an installed agent reads. Basis: measured at dd63247.
- **F3** — Neither existing reader can hold the entry. `configList`'s item pattern is
  `^\s+-\s*(\S+)\s*$` — one token, no reason. `configMap`'s is `^\s+(\w+)\s*:\s*(\S+)\s*$` — a
  `\w+` key, which `results/experiments.jsonl` is not, and a single-token value, which a sentence
  is not. Basis: read at `src/core/config.js:32` and `:286`.
- **D1** — **One direction only: `full_mode_paths` and no `lite_mode_paths`.** Basis: the owner's
  decision, 2026-09-24, recorded as the precedent
  `a-declaration-raises-the-floor-never-lowers-it`. The symmetric case is real — a mechanical
  rename across twenty files clears any size bar and carries no design risk — and is not the test.
  A floor-raising entry's worst misuse costs time; a floor-lowering entry's worst misuse is
  durable policy that exempts every future change touching the path, including the ones nobody had
  in mind.
- **D2** — **Each entry carries its reason, and an entry without one is not read.** Basis: the
  owner's decision, 2026-09-24. A bare path declares that a file is special and leaves the agent
  unable to recognise the sibling the list does not name; the reason is what transfers, which is
  the precedent store's stated founding principle applied to a declaration rather than to a
  decision record.
- **D3** — **An unreadable `full_mode_paths` routes everything Full, and reports why.** Basis: D1
  plus the invariant the other declarations already follow. `authorize:` and `triage:` fail closed,
  and closed for them means *less proceeds without a human* — authorizing nothing, admitting
  nothing. The shared principle is not "grant nothing", it is **fail toward more scrutiny**. For a
  declaration whose purpose is to add process, more scrutiny is more Full mode. Failing the other
  way would silently lower the floor on a typo, which is the outcome D1 exists to prevent.
- **D4** — **A third reader rather than a widened existing one.** `configList` and `configMap` are
  each read by declarations whose shapes this must not disturb, and F3 records that widening
  either one means loosening a pattern that is currently exact. The new reader is confined to this
  key.
- **D5** — **The path's shape is checked; its existence is not.** An entry naming a path no file
  matches is still read and still routes. A path may name a file that does not exist yet — which
  is much of the point, since the schema change that has not happened is the one worth catching —
  and a check that refused it would make the declaration useless exactly where it matters. Basis:
  the same split `issue:<owner>/<repo>` takes in 5.62.0, for the same reason.
- **D6** — **`keel context` reports declared routing only when a declaration exists.** Basis: the
  precedent `mark-the-rare-side-not-the-common-one` — a line every session would train a reader to
  skip it, and the repositories that declare nothing are the common side.

## Hidden Knowledge / Assumptions

- **A1** — Reporting a path is not the same as the agent matching work against it. Keel prints the
  declared entries; whether the agent notices that the file it is about to edit is one of them is
  behavior no gate here observes. Basis: routing precedes the change, so nothing exists to bind a
  check to (Non-Goals). Consequence if wrong: the declaration is read past, and routing stays as
  it is today — the change would then have cost one bootstrap line and bought nothing, which is
  the failure mode to watch rather than a defect this change can close.

## Risks / Trade-offs

- **The bootstrap line is the expensive part, and it is now paid for by a raised cap.** The block
  is 5 bullets against a 12-line and (per F4) a byte budget; one more line is a real cost against
  the discipline #135 argues is already too high for a capable executor, and D7 makes the resident
  total larger rather than trading within it. Accepted because routing is the one rule with no
  other route to the agent — every other bullet's subject also has a gate, a command, or a
  declaration behind it, and F5 records that the last feature without that argument was correctly
  refused the same bytes. The risk this leaves is that 1400 becomes the next 1024: mitigated only
  by the reason living at the assertion, so the next author inherits the argument and not just a
  larger number.
- **A declaration nobody reads is worse than none**, because it looks like protection. A1 is the
  honest statement of it; the mitigation available is that the entry names its reason, which is
  what makes it readable as something other than a list.
- **The reason is free text.** Keel cannot check that it is a reason rather than a word, so the
  requirement is shape only: non-empty after the colon. A project that writes `- path: x` gets a
  declaration that parses and teaches nothing, and no check here will say so.

- **D7** — **The byte cap is raised deliberately, from 1024 to 1400, with the reason recorded at
  both assertions.** Basis: the owner's decision, 2026-09-25, after F4 was measured; recorded as
  the precedent `a-guard-against-quiet-drift-permits-a-loud-change`. The cap's own checks say what
  they defend — that the budget is *not quietly spent later* — and the adjective is the
  specification: a raise in a diff, with its reason beside the number, is the path that phrasing
  forces rather than a breach of it. The rejected alternative was compressing the existing bullets
  to fit under 1024, which would have gone **green on the worse outcome**: routing paid for out of
  gate-discipline prose that was already earning its place. 1400 rather than a round 1536, so the
  headroom is "current content plus one short clause" and the next addition has to argue for itself
  the same way this one did.

## Open Questions

None.
