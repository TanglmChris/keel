# Design

## Verified facts

- **F1** — `openspec/schemas/keel-spec-driven/templates/spec.md` is eight lines and contains no `MUST` or `SHALL`; its requirement body is the HTML comment `<!-- requirement text -->`. Confirmed by reading the file.
- **F2** — `openspec/schemas/keel-spec-driven/templates/tasks.md` documents the red-green rule in the `Verify` comment block, including "IN ADDITION TO the bare `M<n>` entry", and shows only `- M1: <public behavior check>` with `- M1: pending`. No `.red` or `.green` entry appears anywhere in it.
- **F3** — Both templates exist twice, at `openspec/schemas/keel-spec-driven/templates/` and `assets/openspec/schemas/keel-spec-driven/templates/`, and each pair is currently byte-identical. Confirmed by `diff`.
- **F4** — The suite already has `run_openspec`, which returns `None` when the CLI is absent so a scenario can skip rather than fail. `node_modules/.bin/openspec` is present.
- **F5** — A red-green strategy requires per-label `.red`/`.green` Evidence in addition to the bare entry, and `regression`-tagged checks are exempt while still needing the bare entry; `task-start` refuses a red-green strategy whose every check is tagged `regression` with `regression-only-strategy`.

## Decisions

### D1 — The template is verified by running it, not by matching its prose

Assert both templates through the tool that consumes them: fill their author-facing slots with concrete text the way an author would, then run `openspec validate` on the spec template's output and `keel gate task-start` on the tasks template's output.

A prose assertion — "the template contains `SHALL`" — would pass for a template that contains the word in a comment telling the author to add it, which is the state that produced the reported failure. Running the template is the only check that distinguishes a template an author can copy from one that merely mentions the requirement. It also means the templates cannot drift from the gates without the suite noticing, which is the durable property; the two specific findings are just today's instances.

Cost: the spec-template assertion depends on the OpenSpec CLI. It skips when absent, matching the existing `run_openspec` scenarios, and CI has the dependency installed.

### D2 — The spec template's requirement text is a sentence, not a comment

Write `The system SHALL <!-- observable behavior -->` as the requirement body. The template is shipped to consumer repos, so the subject is generic rather than `Keel`. The comment stays as the slot marker, but the modal verb is literal text, which is what makes the copied requirement valid.

### D3 — The worked red-green example is a second task group, not a rewrite of the first

Group 1 stays the plain `evidence-first` shape, which is the common case and the one a reader should meet first. The red-green example is added as its own group so that both forms are visible side by side and the diff to the existing template is additive.

The example shows the full shape the reporter had to discover by trial: a `vertical-tdd` strategy, one untagged check carrying three Evidence entries (`M1`, `M1.red`, `M1.green`), and one `(regression)`-tagged check carrying only its bare entry. Tagging every check would make the group refuse itself under `regression-only-strategy` (F5), so the untagged check is load-bearing and the example is annotated to say so.

### D4 — The tasks-template assertion fills slots mechanically

The template's slots are angle-bracket markers, and the concreteness test rejects those, so the scenario substitutes them before gating. Substitution is a plain regex over `<...>` runs plus removal of HTML comments — deliberately dumb, so that a new slot added to the template is handled without touching the scenario, and so the scenario is testing the template's structure rather than a hand-maintained copy of it.

## Risks

- **R1** — The spec-template scenario skips silently where the OpenSpec CLI is absent, so a local run can be greener than CI. Accepted: it matches the existing `run_openspec` scenarios, and `keel-validation-runner` already requires the full gate to run on a clean CI runner.
- **R2** — A future template slot the mechanical substitution cannot fill would fail the scenario for a reason that is not a template defect. Mitigated by the failure naming the compiled diagnostics, so the cause is visible; and a slot a dumb substitution cannot fill is itself worth knowing about.

## Questions

- None.
