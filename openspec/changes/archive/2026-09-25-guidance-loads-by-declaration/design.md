## Context

Issue #135 asks for guidance to be tiered by executor capability: how-to prose (A-class) loses value as
the executor gets stronger, while falsifiability machinery (B-class) gains it. The report proposes that
Keel emit less A-class content when the repository declares a strong executor.

## Facts

- **F1** — Keel is not on the delivery path for a skill body. Skills ship inside the plugin; the host
  reads `plugins/keel/skills/*/SKILL.md` directly, `scripts/install_to_repo.py` writes no skill, and
  `plugin-skills-match-source` refuses any drift between the plugin copy and `src/skills/`. Nothing
  Keel runs sits between the declaration and the read, so no declaration can make the host load less
  of a body than the body contains.
- **F2** — measured before designing. Keel's own six skill bodies total 28,939 bytes; its overlay
  blocks add 10,907; the generic stepwise prose in the `opsx` command and skill files is 32,518 bytes
  authored by OpenSpec (`openspec update --force` is the remediation Keel's own doctor prints for
  them). The largest single body of A-class prose in an agent's context is therefore text Keel cannot
  edit, and the overlay Keel does own is almost entirely B-class.
- **F3** — Keel's own bodies are criteria-dense. Reading all six: `keel-review-checklist`,
  `keel-align-expectations`, and `keel-tdd-or-test-first` are lists of criteria with almost no
  procedure. `keel-run-single-task-goal` is the exception — its provenance and license note, manual
  fallback, bounded-helper mechanics, and per-target activation detail are conditional how-to prose
  that most activations never need.
- **F4** — Keel already requires of other skills what it does not do itself.
  `keel-review-checklist` asks a new skill to "confirm detailed conditional knowledge uses progressive
  references when it is not needed on every activation".

## Decisions

- **D1** — the reference file is the mechanism. A skill's A-class prose moves out of `SKILL.md` into
  `guidance.md` beside it. Given F1 this is the only way the resident cost falls: the body is the one
  artifact Keel controls that the agent reads at activation, so making the body smaller is making the
  load smaller. Nothing is generated and nothing is emitted conditionally.
- **D2** — the skip is declared, never self-assessed. `executor_tier:` in `keel/config.yaml` takes
  `standard` (absent default, today's behavior) or `high`. A split body instructs: read `guidance.md`
  before proceeding unless the repository declares `high`. #135 is explicit that an executor's own
  judgement of "do I need the guidance?" is the judgement it is worst at; with no declaration the
  instruction to read is unconditional, so the failure mode of an unconfigured repository is paying
  for a read, never skipping one.
- **D3** — `guidance.md` carries no criterion, and that is checked rather than intended. If a tier
  could remove a criterion it would be a relaxation of the gates wearing a capability label. So a
  guidance file is asserted to contain none of the vocabulary Keel states criteria in (`MUST`,
  `MUST NOT`, `SHOULD`, `refuses`, `rejects`, `hard-stops`), which makes "the tier changes no
  criterion" a property of the repository instead of a promise in prose. A criterion that *is* only
  conditionally relevant stays in the body; progressive disclosure of criteria is a different change
  and would need a different proof.
- **D4** — one skill is split, and the measurement says why. Only `keel-run-single-task-goal` has
  A-class prose worth moving (F3). Splitting a criteria-dense body would move criteria, which D3
  forbids, so the other five keep one body each. The mechanism is general; its current application is
  one skill, and that is a finding about Keel's skills rather than a partial delivery.
- **D5** — `executor_tier` is its own key, not the `delegation:` tier. The report suggests reusing
  `routine|standard|deep`. Those name who runs a *delegated* task; a repository may delegate routine
  work to a weak delegate while its own session is strong, so one key cannot answer both without
  lying about one of them.
- **D6** — the declaration is reported where the session starts. `keel context` and `keel --doctor`
  print the tier, so a reader learns a guidance file is being skipped without opening a skill. Both
  surfaces state that the tier affects guidance only; a reader who takes it for a relaxation is worse
  off than one who never saw it.
- **D7** — an unreadable value fails closed to `standard`. Same rule as `delegation:` and
  `authorize:`: the author of a typo believes they declared what they typed, and the safe direction
  here is reading the guidance.

## Alternatives considered

- **A1** — two bodies per skill, one per tier. Rejected: two copies of the same contract drift, and
  F1 means Keel could not choose between them anyway — the host would read whichever file is on disk.
- **A2** — the agent decides what to skip. Rejected by #135's own argument, restated in D2.
- **A3** — tier the OpenSpec-authored prose too. Out of scope by the user's decision to tier Keel's
  own skill bodies only, and blocked in fact: that text is regenerated by `openspec update --force`,
  so any edit Keel made to it is reverted by the command Keel tells people to run.

## Open questions

- **Q1** — should `guidance.md` be projected into target-native layouts?** Not now. The plugin already
  copies the skill directory wholesale, so the file travels with the body it belongs to; a projection
  would be a second delivery path for the same bytes. Durable owner: this design.
