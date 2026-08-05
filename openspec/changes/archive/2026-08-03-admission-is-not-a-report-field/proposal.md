## Why

`triage:` declares which work may start unattended, and the only thing that can carry that declaration today is a label on the issue itself. So the owner's decision — *this specific piece of work may run without me* — is recorded in a field the person who reported the bug can see, and in the same vocabulary they were asked to file it under.

Two things are bound together that are not the same thing:

1. **Who decides that this work may begin unattended.** The repository owner, necessarily a human.
2. **Where that decision is written down.** Today: on the issue.

The second leaks the first. A reporter does not know or care whether the repository runs automation, and cannot be expected to know whether `auto` belongs on their issue. In any repository that accepts issues from outside, labels are already a shared classification vocabulary — `bug`, `enhancement`, `area:cli` — and an operations switch meaning "this project's robot may touch this one" does not belong in it.

For a repository whose issues are all filed by its owner this costs nothing. For a repository where **other people report and the maintainer fixes**, the design does not work: the curation step is required to happen in a field the reporter can see and edit, whose semantics are not operational.

Reported as #62 by the owner, from a session on 2026-08-02.

## What Changes

`triage:` gains a second admission source that lives in the repository: a list of issue numbers in `keel/config.yaml`. Labels remain a source and are not deprecated.

- `triage:` accepts a nested form declaring `labels:` and `issues:` independently. A bare list under `triage:` still means labels, so every existing declaration keeps its exact meaning.
- `keel triage` accepts `--issue <n>` beside `--labels`, and requires at least one of them. An issue is admitted when it carries an accepted label **or** when its number is listed. The reason names which source admitted it.
- A `triage:` block Keel cannot fully read admits nothing and names what it could not read, exactly as an unrecognized `authorize:` action or `delegation:` tier already does.

**What this deliberately does not change.** Admission is still a declaration and never an inference — "which issues look easy" remains the judgement 5.7.0 refused, and this change adds no way to make it. Curation is still one issue at a time: an issue number is as specific as a label applied by hand. Admission still answers "may this begin" and nothing after it. No declaration authorizes a merge.

This repository's own `keel/config.yaml` gains no issue numbers. Shipping the mechanism is this change; using it is the owner's act.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `keel-unattended-triage`: the declaration gains a repository-side issue-number source beside labels; evaluation gains the issue number as an input; a declaration that cannot be fully read admits nothing and says which part failed.

## Impact

- `src/core/config.js`: `readTriagePolicy` returns declared labels, declared issue numbers, and what it could not read; `triageIssue` takes the issue number and names the source that admitted.
- `bin/keel.js`: `--issue` parsing and validation, and the `--doctor` triage surface reporting both sources.
- `keel/config.yaml`, `AGENTS.md`, `README.md`, `src/skills/keel-align-expectations/SKILL.md` and its distributed copy: the wording that says a label is the only unit.
- `scripts/validate_plugin.py`: the `triage-declaration` scenario extends to the second source, the unreadable declaration, and the backward-compatible flat form.
- Risk is an admission that widens without anyone declaring it. It is bounded by leaving every existing entry's meaning untouched (a bare list is still labels, and no bare token changes classification) and by failing the whole policy closed whenever any part of the block is unreadable.
- No new dependency. No gate, timing, ordering, or protocol-state change. The permission boundary changes only in that a second declared way to write the same decision exists.
