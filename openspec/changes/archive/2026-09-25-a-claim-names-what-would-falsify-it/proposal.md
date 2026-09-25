## Why

`Fails with:` earns its place. In the reporting repository (`rtl_ppa_prj`, 24 archived changes, 67
capsules) it is **the single largest cause of re-recording — 8 of 24 non-`none` `Reauthorizations`
(33%)** — and three of its predictions were wrong, each wrong prediction exposing a defect in the
test rather than in the code: a "red" that pytest exits 0 on, a `1200` that was an estimate against
a measured 1799.9, and an `AttributeError` mistaken for an import failure.

This change covers the half it structurally cannot reach, and one adjacent thing with no criterion
at all (#132).

**A red can be entirely honest and the check still immune to the defect it exists to catch.** The
reporting repository's consistency check asserts that synthesis and STA report the same fmax:

```python
assert synth_f == pytest.approx(sta_f, rel=1e-9)
```

The red was real (the function did not exist), the signature predicted it correctly, the green was
real, and `rel=1e-9` reads as strict. Changing `set_load` from `0.0005` to `0.5` — a 1000× unit
error, 5e-16 against 5e-13 — **leaves the check green**, because `pytest.approx` carries a default
`abs=1e-12`. The only way to find that is to put the defect in and watch.

`.red` proves the check failed before the implementation existed. `Fails with:` predicts the red of
an **absent** feature. Neither says anything about the red of a **broken** one, and #116's own
closing note draws the line this extends: a signature written afterwards is a transcription, one
written beforehand is a prediction, and only a prediction can be wrong. Injection is the third
thing — and the two reds can be entirely unrelated, as above.

**Numbers in Evidence have no criterion.** `Basis:`, Evidence prose, and `Findings` are free text,
and one session produced six numbers that were estimates or recollection presented as measurement —
a fabricated `sha256:0e3a…` against a real `78c6dcdf…`, `1200 fF / 13×` against `1799.9 / 19.5×`,
a sampled `0.44%–4.26%` against a full `0–15.40%`. Three reached durable artifacts before being
caught. The exception proves the point: the `1200` **was** caught, because it sat in a `Fails with:`
clause and the gate required it in the `.red`. Same error class, same session — the one instance with
a criterion was stopped and the five without were not.

## What Changes

- **`Detects:` declares an injection.** A check may close with
  `Detects: \`<mutation>\` -> \`<failure it must produce>\``. `task-complete` requires that second
  literal in a `.detects` Evidence entry for the same check. The clause is part of the check text and
  therefore enters the contract fingerprint, so editing the injection afterwards shows up as drift —
  exactly as `Fails with:` does.
- **`Measured:` binds a number to the output that produced it.** A check may close with
  `Measured: \`<literal>\``, and `task-complete` requires that literal in the check's own `M<n>`
  Evidence. Opt-in, for the same reason `Fails with:` is: the `1200` was caught by a clause the
  author chose to write.
- **Clauses chain.** Checks are single-line today, so the clauses are parsed as a trailing sequence
  and any of the three may follow another. `Fails with:` keeps its exact meaning when it stands
  alone or comes last, which is every existing task.
- **Keel judges neither.** An author may declare an injection any check would catch, or a literal
  that is trivially present. Keel records the claim and puts it where Review can see it — the same
  contract `Fails with:` and `Discard reason:` already have.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-task-capsule`: a check may declare the defect it detects and the measurement behind a number
  it states, completion requires the declared literal in the matching Evidence, and the clauses chain
  on one check.

## Impact

- `src/core/task-contract.js` — the trailing-clause parser and the two new clauses.
- `src/core/gates.js` — the completion requirements and the task-start report.
- `scripts/validate_plugin.py`, `assets/openspec/**` templates, `README.md` — the vocabulary where it
  is documented and asserted.
- **The report's suggested refusal is narrowed, and this is a change to its design rather than a
  subset of it.** It proposed refusing `Detects:` on "checks for purely new functionality, shapes
  other than `(regression)`". A `(regression)` check is the *best* candidate for an injection: it has
  no honest red by construction, so injection is the only thing that can show it is not vacuous.
  Refusing it there would remove the clause from where it is worth most. Keel also cannot judge
  whether a defect is injectable, any more than it can judge whether a `Fails with:` literal is a
  good prediction. So the only refusal is a malformed clause, and the surfaces say Keel does not
  judge the injection.
