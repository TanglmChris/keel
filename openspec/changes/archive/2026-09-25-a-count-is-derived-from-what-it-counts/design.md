## Context

The header of `keel/config.yaml` enumerates the declarations a project may write. A check pins that
enumeration by literal, and the literal includes a written-out count.

## Goals / Non-Goals

**Goals:**

- The check reads the declaration set from the module that defines it.
- A header missing a declaration fails, naming that declaration.
- Adding a declaration requires editing the header and nothing else.

**Non-Goals:**

- Checking the prose count. It stays in the header for a reader and is not asserted.
- Generating the header. It is prose with rationale per declaration; only the naming is checked.

## Decisions

- **F1** — The assertion is two literal comparisons in `delegation-resident-text`, phrased as English
  numerals, and has been bumped `Four`→`Five`→`Six`. Basis: read at 08263f6, and the 5.63.0 change's
  `## Invalidates` I6 records the miss that produced this issue.
- **F2** — `src/core/config.js` already names every declaration it reads, in separate readers and
  vocabularies: `fast_check`, `authorize`, `precedents`, `triage`, `delegation`, `full_mode_paths`.
  Nothing collects them, so nothing can be asserted against them. Basis: read at 08263f6.
- **D1** — **The module exports the list, and the check asks the module.** The scenario runs `node`
  to read the export rather than regexing the source: the property under test is what the code reads,
  and a regex over the source is a second copy of the same literal problem one level down. Basis: F2.
- **D2** — **The failure names the missing declaration.** A count disagreement tells an author that
  two numbers differ; the name tells them which line to write. Basis: the cost recorded in F1 was
  spent on a diagnostic that named a number.
- **D3** — **The prose count is no longer asserted.** It stays in the header because a reader
  benefits from it, and checking it would reintroduce exactly the literal this change removes. A
  header that names all six declarations and says "five" is a wording slip a reader catches; a header
  that omits one is a defect a check catches. Basis: the checkable property is membership.

## Hidden Knowledge / Assumptions

- **A1** — A declaration read somewhere other than `src/core/config.js` would be absent from the
  export and therefore unchecked. Basis: F2 finds all six there. Consequence if wrong: the new
  declaration is not asserted in the header, which is the status quo for it rather than a regression.

## Risks / Trade-offs

- **The scenario now depends on a `node` subprocess** to read the export. Accepted: the suite already
  runs `node` for every gate assertion, so this adds no new dependency.
- **The prose count can drift silently.** Accepted per D3, and it is the lesser failure: a wrong
  number beside a complete list misleads nobody about what they may declare.

## Open Questions

None.
