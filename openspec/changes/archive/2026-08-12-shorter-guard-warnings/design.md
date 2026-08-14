## Context

`src/core/guard.js:76-99` (`guardResult`) attaches two warning strings to every guard result
(`start`, `status`, `clear`):

1. Durability: the manifest is a disposable enforcement pointer, not durable authority — OpenSpec
   and Git are, and selection never derives from it. (143 chars)
2. Enforcement boundary: the reported status describes the manifest only; enforcement runs as a
   runtime hook in the host, which Keel cannot observe from the repository, so a written manifest
   is not evidence any write was checked. (201 chars)

`src/core/guard.js:409` renders each as a `Warning: <text>` line in the human-readable CLI output;
the JSON form carries them verbatim in `warnings`.

`scripts/validate_plugin.py:10193-10291` (`validate_guard_status_is_not_enforcement_scenario`,
issue `#14`) is the only test binding this text. It checks:

- Three needles must appear (case-sensitive substring) in the JSON `warnings` joined by a space:
  `"enforcement"`, `"runtime hook"`, `"cannot observe"`.
- The human-readable output must separately contain `"runtime hook"`.
- Three assertive phrases must not appear anywhere: `"enforcement is active"`, `"enforcement is
  live"`, `"writes are guarded"`.
- At least one warning string (checked individually, not the joined text) must contain `"durable
  authority"`.
- The pre-existing status value and warning count survive.

No test pins the exact sentence text — this is the same conclusion the `#92`/`#55` proposal
thread already reached by reading the same scenario before authorizing the shortening.

## Goals / Non-Goals

**Goals:**

- Reword both warnings to reduce combined length while every needle above still resolves and no
  forbidden phrase is introduced.
- Keep every idea a reader currently gets: manifest is disposable and not durable authority;
  OpenSpec/Git are that authority; selection never derives from the manifest; the status describes
  the manifest only; enforcement is a runtime-hook fact Keel cannot observe; a written manifest is
  not proof a write was checked.
- Record the decision in the spec so the Requirement's already-loose wording constraint (ideas,
  not exact text) is explicit, rather than leaving the next reader to re-derive it from the test
  file the way this change's own authoring had to.

**Non-Goals:**

- Moving either warning to `--verbose` or making it first-call-only. The owner's authorization
  (`#92`, 2026-08-12) was for shortening the default output, not for removing it from the default
  path — that was the alternative explicitly declined.
- Touching `#92` item 2 (the `keel-align-expectations` injection-surface restructuring). The owner
  did not authorize that as Full-mode work in the same decision; it stays a separate, still-open
  issue.
- Changing the `warnings` array shape, the `status` field, or any problem code. This is a string
  content change only.
- Generalizing the wording-brevity allowance to other disposable-pointer disclaimers elsewhere in
  the CLI (e.g. the SessionStart projection's durability statement, `keel-native-runtime-
  projection`). Those are governed by their own Requirements and are not part of what `#92`
  authorized.

## Decisions

- D1 — Keep exactly two warning strings, one per existing concern (durability, enforcement
  boundary), rather than merging into one. Basis: the validator's `durable authority` check tests
  a single warning entry for that substring (`any(... for warning in warnings)`), and keeping the
  concerns in separate strings keeps that check meaningful rather than incidentally passing
  because everything landed in one blob.

- D2 — Drop the explanatory clauses "in the host" and "from the repository" from the enforcement-
  boundary sentence, keeping the core claim (enforcement is a runtime hook; Keel cannot observe
  it; a written manifest is not evidence a write was checked). Basis: these clauses explain *why*
  Keel cannot observe enforcement (it runs in a different process than the one reading the repo)
  but are not required by the Requirement text, the validator's needles, or `#92`'s authorization,
  which asks for shortened wording with the MUST satisfied — not for preserving every existing
  clause.

- D3 — Drop "the only" from "the only durable authority" and restructure the sentence around an
  em-dash rather than two independent clauses. Basis: same as D2 — the exclusivity is a stylistic
  emphasis, not a distinct fact the Requirement or validator requires, and the shortened form
  still names OpenSpec and Git as the durable authority without asserting anything false.

- D4 — Spec delta is `MODIFIED Requirements` on `keel-touch-write-guard`'s existing "Guard
  capability is reported from observed evidence" Requirement, reproducing its text unchanged and
  its four existing Scenarios verbatim, adding one new Scenario. Basis: the Requirement's own
  prose already does not pin exact wording ("MUST state the enforcement boundary honestly" is
  about content, not phrasing), so no Requirement text changes; the new Scenario makes explicit
  what the `#92` authorization thread already established by reading the validator, so a future
  editorial pass does not have to re-derive it from test source.

- F1 — Verified 2026-08-12 against the live tree: `node bin/keel.js guard status | wc -c` reports
  398 and `node bin/keel.js guard clear | wc -c` reports 397, confirming `#92`'s measurement still
  reproduces before this change.

- F2 — Verified 2026-08-12: `grep -n "durable authority\|runtime hook\|cannot observe" openspec/
  specs/keel-touch-write-guard/spec.md` returns no match — none of the validator's needles are
  pinned as literal spec text today, confirming the Requirement constrains ideas, not wording.

## Hidden Knowledge / Assumptions

- A1 — The validator's needle check is case-sensitive substring matching on `" ".join(warnings)`.
  The original text supplies the lowercase `"enforcement"` needle via "a disposable *enforcement*
  pointer" in warning 1, not via warning 2's sentence-initial, capitalized "Enforcement runs…".
  The reworded text preserves this: warning 1 keeps "enforcement pointer" lowercase mid-sentence,
  so the needle resolves independently of how warning 2 capitalizes the word at its own sentence
  start.

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- Dropping "in the host" / "from the repository" (D2) slightly reduces the explanatory depth of
  why Keel cannot observe enforcement. Accepted: the causal explanation is not required by the
  Requirement, the validator, or the owner's authorization, and the core honesty claim (Keel
  cannot observe it; a written manifest is not evidence) is unchanged.

## Open Questions

None.
