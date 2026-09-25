## Why

`delegation-resident-text` asserts that `keel/config.yaml`'s header names the right number of
declarations, from both sides, with the number written out as an English word (#143):

```python
if re.sub(r"\s+", " ", "Five independent declarations") in cfg:
    report("delegation-resident-text: the config header still says five declarations.")
    return 1
if re.sub(r"\s+", " ", "Six independent declarations") not in cfg:
    report("delegation-resident-text: the config header does not name six declarations.")
```

It has been hand-bumped twice: `Four` → `Five` when `delegation` arrived, `Five` → `Six` in 5.63.0
when `full_mode_paths` did.

The check's intent is right — the header is where a new project reads the declaration set from, so a
count that drifts is a real defect. The problem is that **the assertion is not derived from the thing
it describes.** Nothing connects it to the declarations Keel actually reads, so adding one and
updating the header still fails, in a scenario whose name has nothing to do with what was changed.
In 5.63.0 that cost one red suite run and a second `## Invalidates` entry the first pass missed,
because the entry named the file the wording lives in and not the check holding it.

## What Changes

- **`src/core/config.js` exports the declaration names it reads**, as the one list both the reader and
  the check consult.
- **The header is asserted against that list**, by asking the module rather than by matching a
  literal. The failure **names the declaration missing from the header** instead of a number, so it
  points at what was added rather than at an arithmetic disagreement.
- **The English numeral is dropped from the assertion.** A count in prose stays in the header for a
  reader; nothing checks it, because the checkable property is that every declaration is named and a
  number is a lossy restatement of that.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `keel-validation-runner`: an assertion about a set is derived from that set, and names the member
  that is missing rather than a count.

## Impact

- `src/core/config.js` — the exported list.
- `scripts/validate_plugin.py` — the assertion, and one new scenario proving it tracks the list.
- `keel/config.yaml` — the header, which must name every declaration.
- Every future declaration then costs a header line and nothing else. It is small each time, and it
  never stops otherwise.
