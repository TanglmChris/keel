## Context

#155: the owner can delegate merging to a repository rule (auto-merge behind a required check), and
Keel's protocol keeps implying human review because nothing records who merges.

## Facts

- **F1** — measured 2026-09-26: `allow_auto_merge: false`, `main` unprotected, and `full-gate` runs on
  every branch push. Delegation is possible and not yet on.
- **F2** — the agent-side refusal is two-layered and holds regardless of Keel: the classifier denied
  the push with `Bash(git:*)` already allowed, and denied reconfiguring permissions as
  `[Auto-Mode Bypass]`.
- **F3** — `authorize:` already has a scoped form, `issue:<owner>/<repo>`, refused bare because a bare
  entry would claim more than it names. The same shape fits a merge claim that is only honest beside
  the check it depends on.
- **F4** — Keel reads `keel/config.yaml` and never GitHub. It cannot observe whether auto-merge or
  branch protection is actually on.

## Decisions

- **D1** — a separate `merge:` key, not an `authorize:` entry. `authorize:` lists what the *agent* may
  do without asking; merging is not in it and stays out, because both guards (F2) should keep refusing
  an agent merge. `merge:` describes the repository.
- **D2** — two forms: `human` and `repository:<check>`. A bare `repository` is refused (F3): "no person
  reviews this" without naming what does is the claim that misleads most.
- **D3** — the projection reports only a declaration that exists, like `full_mode_paths`. An absent
  `merge:` changes nothing about today's behavior, and a line printed every session in every repository
  is a line readers learn to skip. `keel --doctor` always reports it, including absence, because the
  doctor is where a reader goes to learn what is and is not declared.
- **D4** — the `repository:` line says the plain consequence: no human reviews before merge, and the
  named check is the last gate. That sentence is the whole point of the declaration; a line that only
  echoed the value would leave the reader to infer it.
- **D5** — an unreadable declaration claims nothing and is reported with the accepted forms (the same
  closed-vocabulary rule every other declaration follows). "Claims nothing" is the conservative
  direction here: the projection neither asserts human review nor its absence.
- **D6** — Keel does not verify the claim against GitHub (F4). It is the owner's statement, recorded
  and reported where Review sees it.

## Alternatives considered

- **A1** — `authorize: merge`. Rejected by D1: it would read as permission for the agent, which is the
  exact thing the guards refuse, and a future agent reading the list would be right to take it that way.
- **A2** — default an absent `merge:` to `human` and report it. Rejected by D3: Keel cannot know that
  merges are human in an undeclared repository, and asserting it would be the same unfounded claim this
  change exists to stop the protocol making.
- **A3** — have Keel query branch protection with `gh`. Rejected by D6: the gates and the projection are
  local and offline, and that property is what their verdicts rest on.

## Open questions

None. Whether to turn auto-merge on is the owner's decision and is outside this change.
