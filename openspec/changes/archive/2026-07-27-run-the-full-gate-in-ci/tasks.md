<!-- Compact v4 task source (keel-task-capsule/v1, defaults version 1).
     Record only task-specific authority. Omitted fields inherit versioned
     defaults: Owner is the current Keel agent, Mode is implementation, Read
     is the change proposal/design/specs/tasks plus discovered repository
     context, Acceptance derives from Covers, autonomy defaults to hard-stop,
     Coupling defaults to none, helpers stay read-only/evidence-only, and
     commit, push, sync, archive, and cross-task continuation stay
     unauthorized. Declare a field only when it differs from these defaults. -->

## 1. Make the suite runnable on a clean runner

- [x] 1.1 Skip on an absent external runtime instead of failing, and count skips separately
  - Covers:
    - D1 an absent external runtime exits 3 and is reported as a skip, and the skip reason is narrow by design
    - keel-validation-runner / The full run is parallel, deterministic, and fail-loud / An absent external runtime skips instead of failing
    - keel-validation-runner / The full run is parallel, deterministic, and fail-loud / Skipping is only for an absent runtime
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: with the codex and claude CLIs made unreachable, the two native-runtime scenarios each exit 3 and print a skip line naming the runtime they needed, and --all still exits 0 while its summary reports the run as passing, names both scenarios as skipped, and states a verified count that excludes them; a scenario that fails an assertion still exits 1 and is still named as a failure in that same summary; and with the CLIs reachable both scenarios run and pass as before. A new validator scenario locks the runner's skip accounting, and the full suite stays green on this machine where both CLIs exist

  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:f366938b6ac94e9582bc48d2aae64816fbdfec87eebd19a127eedc4b37164166
    - M1: a module-level `SKIPPED = 3` and a `skip_scenario(label, reason)` helper carry the reason to the report, with a comment stating why 3 rather than 0, 1, or 2 and that the reason is narrow by design. `run_all` accumulates skips beside failures, excludes them from the verified count so the number that lands in evidence is the number actually run, and appends `, N skipped: <names>` to the summary. The two native-runtime scenarios now return `skip_scenario(...)` naming the CLIs they need and what they probe, instead of `return 1`. `main()` needed no change: `--scenario X` already returns the scenario's own value, so a direct invocation exits 3 too
    - M1.red: the new `runner-skip-accounting` scenario exited 1 with "a skipping scenario must not fail the run", dumping `validation --all failed for: fake-skip` — a scenario reporting itself skipped was counted as a failure
    - M1.green: the scenario exits 0 across five checks. A synthetic skip beside a pass keeps the run at exit 0, names the skip and its reason, and reports `plus 1 scenario` rather than 2; a passing scenario is not listed among the skips; a skip beside a real failure still exits non-zero and names only the failure; and both real native-runtime scenarios, invoked with `PATH` reduced so neither CLI resolves, exit **3** with a skip line naming `codex`. `npm test` reported "validation --all passed: baseline plus 71 scenarios" with **no skips**, which is the other half of the proof: on a machine where both CLIs exist the skip path does not fire and both scenarios still run
    - Review:
      - Status: pass
      - Acceptance check: pass — a scenario that cannot run is visibly skipped with its reason and excluded from the verified count, a failure beside it still fails the run, and the skip path is proven to fire only when the runtime is genuinely absent, satisfying D1 and both referenced scenarios
      - Scope check: pass — `scripts/validate_plugin.py` only, within Touch, verified against `--base HEAD`
      - Findings: the first version of the new scenario tried to substitute the registry inside a child process, which cannot work — `run_all` dispatches each scenario as its own subprocess that re-reads the real registry from disk, so the substitution was ignored and the harness failed for the wrong reason. It was retargeted at the accounting seam instead, replacing `run_scenario_processes` with fixed result triples, which is the behavior this task changes; the process fan-out itself is already covered by the existing `validation-runner` scenario. No product code was affected. Discard reason: resolved while authoring, nothing remains to own
    - Blocker: none

- [x] 1.2 Make the doctor path assertions independent of the host separator
  - Covers:
    - D2 platform-dependent path assertions normalize the captured output rather than branching on the host
    - keel-validation-runner / The full gate runs on a clean CI runner / Path assertions do not depend on the host separator
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: every target-surface assertion that compared doctor output against a host-spelled path now folds the captured output's separators and states the forward-slash form, and no assertion in the suite compares against a literal backslash path any more. Because the old assertions passed on this Windows machine, the proof is run against POSIX-shaped output instead: the old form fails on it and the new form passes, while both still pass on the Windows-shaped output this machine produces. The target-surface scenario and the full suite stay green here
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:cffd801c145794a27ba89343a0f72d5d28c9358da91cadca127169017b0f9146
    - M1: a `posix_paths` helper folds separators, with a docstring stating why the assertion normalizes rather than branching on the platform or accepting both spellings. **Six** assertions were rewritten, not the five the issue implies: the five literal `.claude/commands/opsx`, `.claude/skills`, `.codex/skills`, `.opencode/commands`, `.opencode/skills` checks, plus `codex_prompt_dir`, which is built from a `Path` and so carried the host separator on both sides of the comparison. A search for a literal backslash path assertion now returns only the helper's own docstring
    - M1.red: the old form was applied to POSIX-shaped doctor output — what a Linux runner prints — and failed: `old assertions (literal backslash, no fold): FAIL missing ['.claude\\commands\\opsx', '.codex\\skills', '.opencode\\commands']`. This is the regression CI would have hit, and it is invisible on Windows, where the same old form passes
    - M1.green: the new form passes against both shapes — `new assertions (forward slash, folded): PASS` on POSIX-shaped output and on Windows-shaped output — while the old form still passes on Windows only, confirming the change is a no-op here and a fix there. Note this makes the Windows run a real proof of the POSIX assertion: after folding, what the assertion compares *is* the forward-slash form, so the spelling CI will see is the spelling this machine already exercises. `node scripts/run_python.js scripts/validate_plugin.py --scenario target-surface` passes, and `npm test` reported "validation --all passed: baseline plus 71 scenarios"
    - Review:
      - Status: pass
      - Acceptance check: pass — no assertion in the suite encodes a host separator any more, the regression is demonstrated against the output shape CI will actually produce, and the Windows run exercises the forward-slash comparison directly, satisfying D2 and the referenced scenario
      - Scope check: pass — `scripts/validate_plugin.py` only, within Touch, verified against `--base HEAD`. The red/green harness is a throwaway script under the job scratch directory and was not added to the repository
      - Findings: the task's Verify said "five" assertions; the sixth, `codex_prompt_dir`, was found during implementation and is the more interesting one, since it compares two host-built strings rather than a literal. Verify was corrected and the contract re-recorded before completion rather than letting the evidence contradict the stated bar. Discard reason: corrected in place, nothing remains to own
    - Blocker: none

## 2. Run it in CI

- [x] 2.1 Add the test workflow and make a real run green
  - Covers:
    - D3 the workflow runs the full gate on a POSIX runner for push and pull request, and the release path is unchanged
    - D4 the evidence is a real green run, and fixing what that run surfaces is inside this task
    - keel-validation-runner / The full gate runs on a clean CI runner / The repository runs its own full gate in CI
  - Touch:
    - .github/workflows/test.yml
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: evidence-first
    - M1: a real workflow run on the pushed commit completes successfully with the run URL and conclusion recorded, its log shows the baseline plus the verified scenario count and both native-runtime scenarios named as skipped, and any platform assumption the run surfaces is fixed here rather than deferred; the release workflow is unchanged and still carries its own tag-and-version guard; and the suite stays green on this machine afterwards
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:8096c09d76bc77b1908508b12e3b24c60ad92d204d4c75f80727cf7bfa1b1e98
    - M1: `.github/workflows/test.yml` ("Full gate") runs on `ubuntu-latest` for every push and pull request, with per-ref concurrency cancellation, `actions/setup-node@v4` at Node 20 with npm cache, `actions/setup-python@v5` at 3.12, `npm ci`, then the same single `npm test` entry point — no scenario enumeration, per `keel-validation-runner`. `publish.yml` is untouched and keeps its tag/version guard. The `validation-runner` scenario now asserts the workflow exists and declares `npm test`, `npm ci`, `push:`, `pull_request`, and `ubuntu-latest`, and that the release workflow still carries its guard, so neither can quietly stop being what it is. **Real run: https://github.com/TanglmChris/keel/actions/runs/30260375118 — conclusion `success`, 57s**, on commit `eb46593`. Its log ends with `validation --all passed: baseline plus 69 scenarios, 2 skipped: native-plugin-marketplaces, native-plugin-install-matrix.`, each skip preceded by its full reason naming the codex and claude CLIs. That is the accounting from task 1.1 behaving on a real clean runner: 69 verified there, 71 verified here, and the difference is named rather than hidden. `npm test` on this machine after the push still reports "baseline plus 71 scenarios" with no skips
    - Review:
      - Status: pass
      - Acceptance check: pass — a real run is green, the log carries the verified count and both named skips, and the release path is unchanged and asserted, satisfying D3, D4 and the referenced scenario. E1 is now true for the 69 runtime-independent scenarios on every push and pull request
      - Scope check: pass — `.github/workflows/test.yml` and `scripts/validate_plugin.py`, both within Touch, verified against `--base HEAD`
      - Findings: the first run passed with no fixes needed, so D4's expectation that CI would surface further platform assumptions did not materialize — the inspection in F1 through F6 was complete. Recording this because the absence of a surprise is weak evidence, not strong: this run exercised one Linux distribution at one Python and Node version, and A4's assumption about case-insensitive path lookup was not disproved so much as never exercised in a way that would distinguish it. The workflow now runs on every push, which is where that assumption will actually be tested over time. Discard reason: nothing actionable remains; the workflow is the ongoing check
    - Blocker: none

## Expectation Coverage

- E1: the 68 runtime-independent scenarios are verified on every push and pull request, not only when one machine's hook runs Covered by: 2.1
- E2: a scenario that cannot run is visibly skipped with its reason, never silently absent and never falsely failing Covered by: 1.1
- E3: skipping can never stand for an unverified assertion Covered by: 1.1
- E4: no assertion depends on which platform printed the path Covered by: 1.2
- E5: the release path keeps its own tag-and-version guard and is not touched Covered by: 2.1
