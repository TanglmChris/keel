## Context

Keel's `triage:` declaration answers one question — may this issue start work without asking the owner — and it answers it from a label the issue carries. The evaluation is deliberately offline: the agent reads the issue with `gh` and hands Keel the labels, so nothing about the verdict depends on the network.

That shape is right about the unit and wrong about the location. A label is applied by a person to one issue, which is exactly the curation the policy wants; but the field it lives in belongs to the issue, and the issue belongs to whoever reported it. #62 asks for the decision to move into a file the repository owner controls, without giving it up to inference.

## Goals / Non-Goals

**Goals:**
- The owner can record admission in a file only a committer can change, and a reporter never sees it.
- Labels keep working, unchanged, for every repository already using them.
- Admission stays a declaration curated one issue at a time — no rule, pattern, author check, or heuristic.
- A declaration Keel cannot fully read admits nothing and says which part it could not read.

**Non-Goals:**
- Deciding whether a label is a *bad* way to admit work. It is one way. This change makes it not the only one.
- Inferring admission from anything — an issue's author, age, size, milestone, or a precedent. #62 explicitly does not propose this and neither does this change.
- Verifying that a human wrote the declaration. Keel could not verify a human applied the label either, and a file in the repository is strictly better on this axis, not perfect on it.
- Restricting *which* issues an owner may list. That is the owner's curation, and a limit on it would be Keel judging the work.
- Adding `keel triage` to `keel --help`, which omits the command entirely today. Same surface, different defect — see Findings ownership.

## Decisions

- **F1** — admission is label-only at 5.23.0. `readTriagePolicy` is `{ labels: configList(repo, "triage") }`; `triageIssue` intersects the carried labels with the accepted ones and has no other input; `keel triage` refuses to run without `--labels`. *Basis: `src/core/config.js:54` and `:178`, `bin/keel.js:561`, and `node bin/keel.js triage --labels auto` returning `admit` / `--labels bug` returning `refuse` on this repository at 5.23.0, 2026-08-03.*
- **F2** — the label is the only place the decision can be written, so recording it is a write to the issue, visible to everyone who can see the issue including its reporter. There is no second input to `triage` and no repository-side list. *Basis: F1 — the CLI accepts `--labels` and nothing else, and `readTriagePolicy` reads one key.*
- **F3** — `keel/config.yaml` is already the file that answers "what has this repository decided": `fast_check`, `authorize`, `precedents`, `triage`, `delegation`. Its own header says so. An admission list is the same kind of statement as the four beside it. *Basis: `keel/config.yaml:1-8`.*
- **F4** — the config reader is line-oriented on purpose and already reads three shapes: a scalar (`configScalar`), a list (`configList`), and one level of nested `name: value` entries (`configMap`, added for `delegation:`). Nesting one level is not new here; it is the shape `delegation:` already ships. *Basis: `src/core/config.js:25`, `:75`, `:120`.*
- **F5** — an unreadable declaration fails closed and is reported by name. `readStandingAuthorization` returns no declared actions at all when any entry is unrecognized, and `readDelegationPolicy` does the same for a tier, both with the comment that the author of a typo believes they declared what they typed. *Basis: `src/core/config.js:65` and `:111`.*
- **F6** — the flat form is what every installed repository has, and what all four shipped documentation surfaces teach: `keel/config.yaml`'s own declaration and comment, `README.md`'s worked example, `AGENTS.md`, and the alignment skill. Any change that reinterprets an existing entry changes an authorization boundary in repositories nobody edited. *Basis: `keel/config.yaml:81`, `README.md:201`, `AGENTS.md:56`, `src/skills/keel-align-expectations/SKILL.md:76`.*
- **F7** — the published spec names labels specifically: "Keel MUST read an optional `triage:` declaration from `keel/config.yaml` naming the issue labels that admit an issue", with a scenario "A declared label admits an issue". The requirement is modified by this change, not contradicted: its neighbours — no network, admission decides nothing after it, no merge, no scheduler — are untouched. *Basis: `openspec/specs/keel-unattended-triage/spec.md:6-27`.*
- **F8** — the surfaces that must keep agreeing are asserted. `unattended-boundary` requires five phrases in `AGENTS.md` and both copies of the alignment skill and requires the two skill copies to be byte-identical; `triage-declaration` asserts the `--doctor` lines `Unattended triage:`, `triage: ok`, and `triage: none`. *Basis: `scripts/validate_plugin.py:15779` and `:14564`.*

- **D1** — the second source is a list of issue numbers in `keel/config.yaml`, not a new `keel/triage.md`. #62 offers both; `config.yaml` is where every other repository decision already lives, and a decision that appears in a diff, can be reviewed in a pull request, and can be narrowed one entry at a time is the form this project has already chosen for authorization. *Basis: F3. Precedent applied: `declarative-authorization-over-blanket-bypass` — "buy autonomy with a declaration that is written down", and its axis of comparison is precisely tracked/diffable/reviewable/revocable-one-entry-at-a-time, which a label is none of. Without it this would have been a question to the owner about which of the two files #62 names.*
- **D2** — the shape is one level of nesting under `triage:`, with `labels:` and `issues:` each holding a list, and a bare list directly under `triage:` continues to mean labels.

  ```yaml
  triage:
    labels:
      - auto
    issues:
      - 62
  ```

  This is the shape #62 illustrates. The alternative considered was typed entries in the existing flat list (`- auto`, `- issue:62`), which needs no new reader at all — and is rejected, because a repository whose label is literally named `issue:5` would have that entry silently change from "a label that admits" to "issue 5 admits". Silently reinterpreting an existing entry in an authorization declaration is the one failure this change must not have. *Basis: F4, F6. Precedent applied: `no-dependency-for-a-format-we-control` — its decision is to hand-roll rather than add a parsing library, and that is honoured; its rationale's warning about nested maps is what made this a question at all, and `configMap` shows the repository already accepted exactly one level of it. Without the precedent this would have been "add a YAML library", which the reader below does not need.*
- **D3** — an `issues:` entry is a bare positive integer. Nothing else is accepted, including `#62`, which is reported by name with the accepted form rather than guessed at. *Basis: F5 — the vocabulary is closed so a typo can be named.*
- **D4** — a `triage:` block Keel cannot fully read admits nothing, and the refusal names the entries it could not read. This covers a bare list mixed with sub-keys, a sub-key that is neither `labels:` nor `issues:`, and an `issues:` entry that is not a number. *Basis: F5, applied unchanged.*
- **D5** — `keel triage` accepts `--issue <n>` and requires at least one of `--labels` / `--issue`. `--labels` stops being mandatory because a repository declaring only issue numbers should not have to pass an empty label list to be answered. Every invocation that worked before still works. *Basis: F1 — the current requirement exists to stop a caller expecting Keel to fetch the issue, and that reason is served by requiring at least one input.*
- **D6** — the reason names the source that admitted: the label, or the issue number and the file that lists it. A refusal names what was carried and both halves of what the repository accepts, so an issue that is neither labelled nor listed is distinguishable from a repository that declared only one of the two. *Basis: F7 — the published requirement "the reason names the label that admitted it" generalizes rather than disappears.*
- **D7** — the JSON keys are additive. `accepted` keeps meaning accepted labels and `matched` keeps meaning matched labels; `acceptedIssues`, `issue`, and `sources` are new. A consumer reading the 5.23.0 shape reads the same values from the same keys. *Basis: F1 — the shape is a published interface and renaming a key breaks a reader for no behavioral gain.*
- **D8** — this repository's own `keel/config.yaml` declares no issue numbers, and its `triage:` block is left in the flat form. It is left flat deliberately: the repository that ships the compatibility is the repository that demonstrates it. Adding an issue number here would widen this repository's own admission policy, which is the owner's act and not this change's. *Basis: the proposal's own boundary; `AGENTS.md` — "do not widen the triage policy".*

## Hidden Knowledge / Assumptions

- **A1** — an issue number in `issues:` refers to an issue in the repository the config file belongs to. Keel resolves nothing and cannot tell one forge or repository from another; the number is compared to the number it was handed. A repository that hands Keel a number from somewhere else gets an answer about a number, which is the same trust model as handing it labels from somewhere else. *Owner: this change, stated in the spec so a reader meets it as intent.*
- **A2** — a repository may declare both sources, and either admits alone. #62 asks for the label to become "one source, not the only one", which is satisfied only if both are live at once. *Basis: #62, candidate 2. Owner: this change.*
- **A3** — an owner listing an issue number has read that issue. The same assumption already carries the label form and is no weaker here; a number typed into a tracked file is, if anything, harder to apply by accident than a label picked from a dropdown. *Owner: this change.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- **The admission boundary is the thing being edited.** The mitigation is that no existing declaration changes meaning: a bare list is still labels, no bare token is reclassified, and the new source has to be typed into a tracked file to do anything. The direction of every failure mode is refusal — an unreadable block admits nothing.
- **Two ways to say one thing.** A repository can now declare admission twice, and a reader has two places to look. Accepted deliberately: #62 requires the label to survive as a source, and `--doctor` prints both so the answer to "what may run here" stays one command.
- **The flat form is now a compatibility shape rather than the shape.** It is documented as accepted, not deprecated, and the scenario asserts it, so it cannot rot quietly.
- **`keel --help` still does not mention `keel triage` at all**, so `--issue` is exactly as discoverable as `--labels` was — which is to say, through `README.md` only. Not folded in; see below.

## Open Questions

- None. #62 names the decision, the candidate, and the reason to prefer it; the two sub-choices it leaves open — which file, and how the entry is written — are answered by D1 and D2 from repository facts and two precedents, with the rejected alternative recorded beside each.

## Alignment

Routed deep: the change touches an external interface (`keel/config.yaml`'s accepted shape and the `triage` command surface) and a permission boundary (what may start unattended). The material product choice — whether admission should stop being label-only — is decided in #62 by the owner, who also names the preferred candidate and the stance it must not overturn. What remained after that was file choice and entry shape, both resolved against repository facts (F3–F6) and precedents cited at D1 and D2. No question survived to become a `Q<n>`.

Findings ownership: `keel --help` omitting `keel triage` is a pre-existing defect on the surface this change edits. It is not folded in, because doing so would make the change's acceptance about two things, and the command's absence predates the second source. It is recorded as a Review finding with a durable owner.
