# templates-pass-their-own-gates

## Why

Issue #28's remaining authoring cost is in the templates, and both findings have the same shape: an author who follows the shipped template exactly produces something the gate then refuses.

- `templates/spec.md` gives `### Requirement: <!-- name -->` followed by `<!-- requirement text -->`. No MUST, no SHALL. `openspec validate` requires one, so following the template produced 16 errors of the form `ADDED "<name>" must contain SHALL or MUST` on first run.
- `templates/tasks.md` documents the red-green Evidence rule in prose — since 5.3.4 it even says the `.red`/`.green` entries come *in addition to* the bare `M<n>` — but shows no worked example. The reporter tried `M1（红）:` and `M1（绿）:` labels first, was refused, then landed on the flat form and was refused again for the missing bare entry. Issue #28 names one worked example as the fix that would have closed both attempts.

A template is the one artifact whose whole purpose is to be copied. Prose beside a wrong example loses to the example.

## What Changes

- The spec template's requirement text carries `SHALL`, so a requirement written from it validates on first run.
- The tasks template carries a worked red-green group: a `vertical-tdd` strategy, an untagged check with its bare, `.red`, and `.green` Evidence entries, and a `(regression)`-tagged check showing the exemption.
- Validation asserts these by running the templates through the tools that consume them, rather than by matching their prose.

## Impact

- `openspec/schemas/keel-spec-driven/templates/spec.md` and `templates/tasks.md`, plus the `assets/` copies of both
- `scripts/validate_plugin.py`
- Spec: `keel-validation-runner`

## Non-goals

- No change to what either gate accepts. Both findings are that the template disagrees with an already-correct rule.
- Issue #28 items 4, 5, 6, and 9 shipped in `diagnostics-name-the-cause`; item 8 is upstream OpenSpec CLI; item 10's first half is unverified and separately owned.
