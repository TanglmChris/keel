## Why

Keel's own full gate has no automated net. `package.json`'s test script runs 70 validator scenarios, and the only thing that runs them is a local pre-push hook on one Windows machine. `.github/workflows/publish.yml` says so in a comment: the suite is "Windows/CLI-specific and runs in the pre-push hook before any release tag is pushed, so it is not re-run here."

That was defensible when releases were rare. On 2026-07-27 this repository shipped **five archived changes across three releases in one day**, every one of them verified only by that hook. A skipped `--no-verify`, a different machine, or a contributor who never installed the hook, and nothing catches a regression.

It also contradicts Keel's own convention. `keel-verification-layering` already defines the split — the fast inner-loop check at a local pre-push, the **full gate at CI or `keel gate change-close`** — so the CI half is documented and simply not implemented for Keel itself.

Two concrete blockers, both smaller than the comment implies:

- **Two scenarios hard-require external CLIs.** `native-plugin-marketplaces` and `native-plugin-install-matrix` call `shutil.which("codex")` / `claude` and `return 1` when either is missing, so the suite cannot pass anywhere both CLIs are absent — including any CI runner. They are the only two of 70.
- **Five assertions hardcode Windows path separators.** `validate_target_surface_scenario` compares `keel --doctor` output against `.claude\commands\opsx`, `.claude\skills`, `.codex\skills`, `.opencode\commands`, and `.opencode\skills`. The CLI prints those through `path.join`, so they are forward slashes on Linux.

Nothing else found by inspection blocks a Linux run: `run_python.js` already resolves Python per platform, the validator uses no `shell=True`, and `.gitattributes` pins `*.md` to LF so the byte-budget assertions are platform-stable.

Reported as issue #10.

## What Changes

- A scenario that cannot run because an **external runtime is absent** reports a skip and exits `3` instead of failing. `--all` counts skips separately, names them with their reason in the summary, and does not treat them as failures.
- The five platform-dependent path assertions normalize captured output separators instead of asserting one platform's spelling.
- A `test` workflow runs the full gate on `ubuntu-latest` for every push and pull request. It does not replace the local pre-push fast check; it implements the CI half of the layering convention Keel already documents.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `keel-validation-runner`: the full run gains explicit skip semantics for an absent external runtime, and its assertions become platform-independent so the suite runs on a clean CI runner.

## Impact

- A regression in any of the 68 runtime-independent scenarios is caught on every push and pull request, not only when one machine's hook runs.
- The two native-runtime scenarios still run wherever the CLIs exist — the author's pre-push hook keeps exercising them — and are visibly reported as skipped where they do not, rather than silently absent or falsely failing.
- Keel stops preaching a verification split it does not apply to itself.
- Honest limit: this cannot be proven from the authoring machine. Task 2.1's evidence is a real green CI run, and fixing whatever further platform assumptions that run surfaces is inside its scope.
