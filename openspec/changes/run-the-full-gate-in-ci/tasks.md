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

- [ ] 1.2 Make the doctor path assertions independent of the host separator
  - Covers:
    - D2 platform-dependent path assertions normalize the captured output rather than branching on the host
    - keel-validation-runner / The full gate runs on a clean CI runner / Path assertions do not depend on the host separator
  - Touch:
    - scripts/validate_plugin.py
  - Verify:
    - Strategy: regression-first
    - M1: the five target-surface assertions that compared doctor output against backslash paths now fold the captured output's separators to forward slashes and assert forward-slash paths, no assertion in the suite compares against a literal backslash path any more, the target-surface scenario still passes on this Windows machine, and the same assertions hold against output captured with forward slashes; the full suite stays green
  - Evidence:
    - Contract: pending
    - M1: pending
    - M1.red: pending
    - M1.green: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## 2. Run it in CI

- [ ] 2.1 Add the test workflow and make a real run green
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
    - Contract: pending
    - M1: pending
    - Review:
      - Status: pending
      - Acceptance check: pending
      - Scope check: pending
      - Findings: pending
    - Blocker: none

## Expectation Coverage

- E1: the 68 runtime-independent scenarios are verified on every push and pull request, not only when one machine's hook runs Covered by: 2.1
- E2: a scenario that cannot run is visibly skipped with its reason, never silently absent and never falsely failing Covered by: 1.1
- E3: skipping can never stand for an unverified assertion Covered by: 1.1
- E4: no assertion depends on which platform printed the path Covered by: 1.2
- E5: the release path keeps its own tag-and-version guard and is not touched Covered by: 2.1
