## Why

Keel installs two kinds of content into an agent's context, and their marginal value moves in
opposite directions as the executor gets stronger (#135):

| | marginal value as capability rises |
|---|---|
| **A. how to do it** — how to split tasks, write tests, order commits, what to do first | → 0 |
| **B. make yourself falsifiable** — red/green, `Fails with:`, fingerprint drift, `Durable owner:` existence, Touch attribution | rises |

They are mixed in the same artifacts with nowhere to separate them, so a capable executor pays for A
and a weak one may not get enough of it. The reporting repository ran 24 changes and consulted no
A-class guidance once; every error actually caught was B-class.

**Measured before designing, and it moves the deliverable.** Of the guidance in an agent's context:

| content | bytes | author |
|---|---|---|
| Keel's own six skill bodies | 28,939 | **Keel** |
| Keel's overlay blocks | 10,907 | **Keel**, and almost entirely B-class |
| generic stepwise prose in the `opsx` command and skill files | 32,518 | **OpenSpec** |

The remediation Keel's own doctor prints — `run keel --init --target claude or openspec update
--force` — is the tell: Keel appends an overlay to those files and does not author them. So the one
concrete A-class example the report gives (`openspec-propose`'s phased artifact loop) sits in prose
Keel cannot remove, and the overlay Keel does own is the B-class half the report says to keep.

**And the mechanism the report assumed does not exist.** Skills ship in the plugin and the host reads
`SKILL.md` directly; `scripts/install_to_repo.py` writes no skills, and the plugin copy must byte-equal
`src/skills/`. Keel's CLI never sits between the host and a skill body, so a declared tier cannot
change what gets loaded.

## What Changes

- **A skill's A-class prose moves out of the always-loaded body into a referenced file.** The body
  keeps the contract and the criteria; the stepwise detail becomes `guidance.md` beside it. That is
  the only mechanism that reduces resident tokens under the constraint above, because the body is the
  one thing Keel controls that the agent reads at activation.
- **The reference is followed by declaration, not by self-assessment.** `executor_tier:` in
  `keel/config.yaml` takes `standard` (the default, and today's behavior) or `high`. Each split skill
  states: read `guidance.md` first unless the repository declares `high`. The report is explicit that
  an executor's judgement of "do I need this?" is the judgement it is worst at, so the skip is
  declared and the instruction to read is unconditional in its absence.
- **`keel context` and `keel --doctor` report the declared tier**, so the declaration is visible where
  the session starts rather than only inside a skill.
- **The tier affects guidance and nothing else.** It MUST NOT change a gate, a criterion, an evidence
  requirement, or a Review, and the surfaces say so — a reader who takes it for a relaxation is worse
  off than one who never saw it.

## Capabilities

### New Capabilities

- `keel-guidance-tiering`: a skill's stepwise guidance is referenced rather than resident, followed by
  declaration, and cannot affect any criterion.

### Modified Capabilities

None.

## Impact

- `src/core/config.js`, `src/core/context.js`, `bin/keel.js` — the declaration, its reporting, and its
  health.
- `src/skills/*/SKILL.md` plus a new `guidance.md` per split skill, mirrored into `plugins/keel/`.
- `keel/config.yaml`, `README.md` — where a project reads the declaration from.
- **Not adopted from the report**: `executor_tier` reusing the `delegation:` tier vocabulary. Those
  tiers name who runs a *delegated* task; a repository may delegate routine work to a weak executor
  while its own session is strong, so one key cannot answer both without lying about one of them.
