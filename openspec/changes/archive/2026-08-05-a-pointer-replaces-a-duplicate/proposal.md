## Why

`#55` measured the `keel-align-expectations` skill's injection footprint and found it had grown,
not shrunk, since the issue was filed: skill 8,041 → 8,364 chars; the four `opsx/*.md` command
files 27,733 → 31,257 combined. Its `## Unattended runs` section (1,581 chars, 19% of the skill)
is a near-verbatim second copy of `AGENTS.md`'s own `## Unattended runs` section (1,457 chars) —
five distinctive sentences ("may not merge", "Keel schedules nothing", "designed boundary",
"Admission answers", "never from a precedent") appear once in each file. `AGENTS.md` is resident
and loads on every session; the skill loads again whenever it activates. So in a repository with
both files, roughly 1,457 of those 1,581 characters are read a second time for no new information.

The measurement also names why this is a real duplication and not a coincidence of wording: the
skill is a *portable* artifact (`keel-skill-sourcing-and-portability`'s "Keel skills have one
portable authority" — its content must work in any target the skill is projected to), and its
`## Unattended runs` section was written to stand alone for a host that might not have `AGENTS.md`.
The cost of that self-containment is the second copy — and the copies have already been shown to
drift apart in wording once (this repo's own `AGENTS.md` grew a `keel:start` version-check
paragraph the skill copy never gained), which is the concrete failure mode a pointer removes.

## Measurement (2026-08-05, 5.31.0)

```
$ wc -c src/skills/keel-align-expectations/SKILL.md
    8364
$ grep -c "^## " src/skills/keel-align-expectations/SKILL.md
    9
```

The `## Unattended runs` section spans lines 74-97 of the skill (`sed -n '74,97p'`), 1,581 of the
file's 8,364 characters. `AGENTS.md`'s own `## Unattended runs` section (`AGENTS.md:55-61`) is
1,457 characters. Five sentences carrying the section's distinguishing content are present,
character-for-character, in both files; `scripts/validate_plugin.py`'s
`validate_unattended_boundary_scenario` and the M5 check inside
`validate_triage_admits_from_the_repository_scenario` are what pin them there today, requiring the
literal phrases in `AGENTS.md`, the canonical skill, and the plugin-distributed skill copy alike.

## What Changes

Owner decision (2026-08-05, `dasauto#18`): "leave a one-line pointer from the skill's Unattended
runs section to the AGENTS.md section it duplicates, rather than keeping the skill fully
self-contained." This change implements exactly that, and only that:

- `src/skills/keel-align-expectations/SKILL.md`'s `## Unattended runs` section body is replaced
  with a short paragraph naming what lives in `AGENTS.md`'s own `## Unattended runs` section and
  pointing there, instead of restating it. The heading stays; the section's *place* in the skill
  (between "Decision precedents" and "Domain lenses") is unchanged.
- `plugins/keel/skills/keel-align-expectations/SKILL.md` receives the identical edit, keeping the
  two copies byte-identical — the existing invariant every skill validator already enforces.
- The two deterministic validators that currently require the five boundary phrases and the
  issue-number phrase inside the skill files are updated to instead require a pointer marker
  there, while continuing to require the full phrases in `AGENTS.md` itself (which is the surface
  that actually needs to stand alone, and does not change).

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-unattended-triage`: two new scenarios (one under each of two requirements) record that a
  secondary surface such as the `keel-align-expectations` skill may point to `AGENTS.md`'s
  statement of the admission sources and the open-PR/no-merge boundary instead of repeating them,
  provided `AGENTS.md` itself still states both in full.

## Impact

- `src/skills/keel-align-expectations/SKILL.md` and `plugins/keel/skills/keel-align-expectations/SKILL.md`
  — the `## Unattended runs` section body (~1,260 of ~1,581 characters removed, replaced by a
  ~320-character pointer paragraph).
- `scripts/validate_plugin.py` — `validate_unattended_boundary_scenario` and the M5 block of
  `validate_triage_admits_from_the_repository_scenario` are updated to check the skill files for a
  pointer marker instead of the full phrase sets, and to keep checking `AGENTS.md` for the full
  phrase sets unchanged.
- `openspec/specs/keel-unattended-triage/spec.md` — two new scenarios.
- No change to `AGENTS.md`'s own `## Unattended runs` content, to any code path that reads the
  skill at runtime, or to admission/gate/write-guard behavior. This is a documentation-surface
  consolidation, not a protocol change.
