## Why

Three reported issues share one failure mode: a Keel diagnostic is accurate about *what* it checked and silent about *why* it failed, so the author debugs the wrong thing. All three were found by authors doing ordinary first-time work, and all three cost a round of reading Keel's source to recover.

**Issue #7** — three diagnostics in task-contract parsing point away from the real cause.

The worst is the compact-v4 detection. `requiredFieldProblems` decides between the compact v4 and legacy v3 required-field sets with `isConcrete(field(task, "Verify"))`, and `isConcrete` treats any `<...>` anywhere in the text as a placeholder. A legitimate v4 task whose `Verify` prose contains angle brackets — the reporter wrote a filename pattern inside backticks — silently compiles as v3 and reports seven missing fields the author never intended to use, including `Candidate Boundary` and `Report`. The template comment says compact v4 needs only Covers, Verify, and Evidence, so the diagnostic contradicts the documented schema. The real fix is one pair of angle brackets.

The other two: `unresolved-covers` cannot say that the target requirement's own name contains the ` / ` hierarchy separator, and `unresolved-authority` says "requires documented design authority" — pointing the author at `design.md` — when the parser actually wants a `Pre-authorized fallback:` line under `Autonomy boundary:` on the task.

**Issue #6 and issue #9** — the same dev-versus-consumer confusion, in both directions.

`plugins/keel/.claude-plugin/plugin.json` exists only in Keel's own repository, and `keel --init` never creates it. In any consumer repository the `native plugin source` check is therefore permanently `missing`, and the next line's remediation tells an author who just installed the plugin to install the plugin. Its version branch says "align both before release", which is meaningful only to Keel's maintainers.

The reverse direction is issue #9: running `keel --install` inside Keel's own repository overwrites `AGENTS.md` with the consumer-facing bootstrap from `assets/bootstrap/AGENTS.md`, dropping the protocol sections that four validation scenarios assert on and turning the repository red.

Neither command can tell whether it is running in Keel's own repository or a project that consumes Keel.

## What Changes

Make each of these diagnostics name its actual cause, and teach `doctor` and `--install` which repository they are in.

- Report a dedicated diagnostic when `Verify` is present but placeholder-judged, naming the offending token, instead of silently switching to the v3 required-field set.
- Stop treating angle brackets inside inline code spans as placeholders, so documented filename and format patterns are writable in `Verify` prose.
- Make `unresolved-covers` state when a candidate requirement name contains the ` / ` separator, and `unresolved-authority` state the exact field and line prefix it wants.
- Add one predicate for "this repository is Keel's own source", and use it so `doctor` does not present a dev-only check as a consumer failure, and `--install` does not rewrite Keel's own `AGENTS.md`.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-task-capsule`: compact-versus-expanded detection must fail loudly rather than silently degrade, and Covers and authority diagnostics must name their cause.
- `keel-target-surface-diagnostics`: development-only surface checks must be scoped to the repository where they are meaningful.

## Impact

- Authors writing their first compact v4 `tasks.md` stop being handed a v3 field list they never asked for.
- Consumer repositories stop seeing a permanent `missing` they cannot act on, and stop being told to install an already-installed plugin.
- `keel --install` becomes safe to run inside Keel's own repository, closing the trap recorded in issue #9.
- No change to what a valid task compiles to: every fix here is diagnostic wording, placeholder scope, or check applicability. Existing valid tasks keep their fingerprints.
