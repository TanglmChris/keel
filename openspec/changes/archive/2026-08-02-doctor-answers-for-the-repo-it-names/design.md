## Context

`keel --doctor` opens with `keel doctor for <repo>`, where `<repo>` is `options.repo` or the cwd. Every subsequent line is read by the user as a statement about that repository. The OpenSpec pin line is not one: it reads `PACKAGE_ROOT/package-lock.json`, where `PACKAGE_ROOT = path.resolve(__dirname, "..")` is the directory Keel itself is installed in.

The two coincide in exactly one situation — running `node bin/keel.js` from Keel's own source checkout — which is the situation every existing scenario and every development session runs in. That is why the cross-check was written, shipped, and covered without anyone seeing it fail.

## Goals / Non-Goals

**Goals:**
- The OpenSpec pin doctor reports is the pin of the repository doctor names.
- The reported pin and the answering binary are attributed to their roots, so a reader can tell the two apart even when they disagree.
- A repository declaring no OpenSpec pin is reported as declaring none, not as a read failure and not as a disagreement.
- Coverage exercises the diagnosis from a repository that is not Keel's checkout, since that is the only place the defect exists.

**Non-Goals:**
- Changing which `openspec` binary Keel runs (D2).
- Installing, selecting, or refusing an OpenSpec version.
- Making doctor fail, or changing its exit status, on a version disagreement. The disagreement is advisory.
- Fixing the other `PACKAGE_ROOT` consumers (`SHIPPED_LENS_DIR`, `PACKAGE_JSON`, `INSTALL_SCRIPT`). Those legitimately refer to Keel's own installed assets.

## Decisions

- **F1** — `keel --doctor` reports the OpenSpec pin of Keel's install location, not of the repository it names. Measured 2026-08-02 at 5.14.0: a scratch repo whose `package-lock.json` pins `@fission-ai/openspec` at `9.9.9` was reported `openspec: ok - <keel-checkout>/node_modules/.bin/openspec (1.6.0, lockfile 1.6.0)`. Neither number came from the diagnosed repository. *Basis: direct execution of `node bin/keel.js --doctor` from the scratch repo.*
- **F2** — the defect is invisible to the suite by construction. `run_keel` (`scripts/validate_plugin.py:1044`) always spawns `node <ROOT>/bin/keel.js`, so `PACKAGE_ROOT` is Keel's checkout in every scenario regardless of `cwd`. `source-repo-cli-resolution` already drives doctor from a temp consumer directory and still cannot see it, because that directory's *identity* is not what the read is rooted at. *Basis: read of `run_keel` and `validate_source_repo_cli_resolution_scenario`.*
- **F3** — `keel-target-surface-diagnostics` already requires the correct behavior in words: doctor reports "the range **the repository** declares", and "Keel MUST NOT install, select, or refuse an OpenSpec version: reporting is the scope." The spec does not need its stance changed, only its subject named unambiguously. *Basis: `openspec/specs/keel-target-surface-diagnostics/spec.md:273-275`.*
- **F4** — `lockedOpenSpecVersion()` has exactly one caller, `runDoctor()` (`bin/keel.js:1429`). Rerooting it cannot affect any other surface. *Basis: `grep -n lockedOpenSpecVersion bin/keel.js` returns `:702` and `:1429`.*
- **D1** — `lockedOpenSpecVersion(repo)` takes the diagnosed repository as its root and does not fall back to `PACKAGE_ROOT`. A fallback would restore the exact confusion being removed: it would report Keel's pin under a heading naming the user's repository, and the reader could not tell which case they were in. *Basis: F1; the failure being fixed is misattribution, and a silent fallback is misattribution.*
- **D2** — `openspecCandidates()` keeps `PACKAGE_ROOT` as its root; which binary runs does not change. Issue #57's candidate to reroot both is declined. Rerooting resolution would make Keel select an OpenSpec build on the user's behalf, which `bin/keel.js:689` and the spec quoted in F3 both refuse, and would silently change the program every existing consumer runs at upgrade — the same class of surprise this change exists to make visible. *Basis: F3; user decision 2026-08-02 when the contradiction between the issue's candidate and the recorded stance was put to them.*
- **D3** — the pin is reported as `repo pins <version>` or `repo declares no OpenSpec pin`, replacing `lockfile <version>` / `lockfile unreadable`. The answering binary stays attributed by its printed path. `lockfile unreadable` described the mechanism and named no owner; both replacements name whose fact is being reported. *Basis: F1 — the old wording is true of a file the reader was never told about.*
- **D4** — a repository declaring no pin produces no warning and no disagreement. Most repositories do not depend on OpenSpec directly, so absence is the ordinary case; warning on it would train readers to ignore the line. Absence and disagreement are different statements and are reported differently. *Basis: `@fission-ai/openspec` is Keel's dependency, not a required dependency of repositories Keel is used in.*
- **D5** — the new scenario builds a repository whose `package-lock.json` pins a version that cannot be the answering binary's, and asserts doctor reports *that* pin. This makes the test hermetic: it needs no global install, no network, and no second Keel on disk, while still exercising the case where install location and diagnosed repository differ. *Basis: F2 — the missing coverage is a differing root, not a differing installation method, and only the former needs to be simulated.*

## Hidden Knowledge / Assumptions

- **A1** — a consumer repository's `package-lock.json` is the right place to read its OpenSpec pin, as opposed to `package.json` `dependencies` or a `.openspec.yaml` field. Keel's own read already uses the lockfile and reports a resolved version rather than a range, which is what the disagreement check needs. *Basis: `lockedOpenSpecVersion()` walks `lock.packages` for a resolved `version`; a range in `package.json` cannot be compared to a reported version without resolving it. Owner: this change — if a repository pins OpenSpec only in `package.json`, doctor reports "declares no OpenSpec pin", which D4 makes a safe, non-warning outcome rather than a wrong one.*

## Coupled Iteration Contract

Not required; no task declares `Coupling: required`.

## Risks / Trade-offs

- Consumer repositories that pin an OpenSpec version differing from the one Keel bundles will see a `warning` verdict from doctor where they previously saw `ok`. This is the intended effect and the entire point of the 5.11.0 cross-check, but it is a visible change at upgrade. Mitigated by D4 (absence never warns) and by the warning remaining advisory — doctor's exit status is unchanged.
- Keel's own checkout sees a wording change (`lockfile 1.6.0` → `repo pins 1.6.0`) with no change in verdict, since there `repo == PACKAGE_ROOT`. `runtime-versions-are-checked` asserts the version *number* appears in the line rather than the surrounding words, so it stays green; this was verified before authoring rather than assumed.
- Reading a lockfile from a user-supplied path is a new read of an untrusted file. It is already wrapped in `try/catch` returning `null`, is parsed as JSON with no execution, and adds no write surface.

## Open Questions

None.
