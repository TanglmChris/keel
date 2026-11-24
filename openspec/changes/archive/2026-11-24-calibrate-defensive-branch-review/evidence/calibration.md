# Defensive-branch review calibration for #533

Baseline: public Keel commit `ac0da21a`. These four retrospective engineering cases calibrate the rubric. The precise model behind each relevant branch is unknown, so the cases establish observable behavior and no model attribution.

| Workload | Concrete protection to retain | Excessive candidate or observed failure | Replayed evidence |
| --- | --- | --- | --- |
| Internal transformation | A validation fixture excludes OpenSpec while retaining its Node interpreter and unrelated siblings on the shared PATH. | Dropping a whole directory for one executable silently changes unrelated inputs. The earlier failure was documented by #137; the short filter now removes only its declared names. | `a-filter-drops-only-what-it-named`, which asserts both removal and preservation. |
| External or untrusted input | The write guard denies declared in-repository unauthorized writes; its boundary is resolved before manifest failures can affect unrelated paths. | Treating any malformed manifest as authority to deny out-of-repository writes was a real scope violation. The runner's old fallback to baseline success on unsupported flags (#444, `c81c0472`) is a separate observed example of hidden failure. | `guard-scope-is-the-repository`, `runner-refuses-what-it-would-not-run`. |
| Asynchronous ownership and retry | Wait for the original native writer to unload. Keep a timed-out or refused acquisition pending for inspection. Preserve exactly one acquisition attempt. | A generic automatic retry after an ambiguous result would replay a potentially effective action. This is a negative control, not a purported shipped defect. | `969b4ae0` and `node --test --test-name-pattern='source unload' scripts/test_codex_onboarding.js`. |
| Supported legacy compatibility | Use the text worktree list on Git 2.34.1, which fails the NUL-delimited invocation. | Removing the fallback would break a measured supported host. Inventing parsing fallbacks for unobserved formats would exceed the available contract. | `8e43cdb5`, `worktree-overview` on real Git 2.34.1. |

For each candidate record the public trigger, requirement or observed regression, expected error visibility, and state after a retry or duplicate result. A grounded safety boundary can need an extra branch. A fallback that manufactures success or changes unrelated behavior is a failure even if the happy path is green. The current replay took 10.61 seconds for the four named Python scenarios and 2.15 seconds for the two native-boundary stand-in tests. No model requests or model token usage occurred.

## Prespecified model pilot

Use four public or synthetic task prompts corresponding to the rows above. Freeze inputs, permissions, reasoning label, client version and success tests before running. Compare two instruction styles (existing guidance and a short requirement/contract/observed-failure rule) for the target model and a separately named comparator, in randomized order, with one response per combination as a 16-run screening pilot. Save the actual outputs labelled only by fixture and run ID for scoring. Record unnecessary branches, hidden failure, acceptance pass, regressions, wall time, and tokens. Require repeated runs before making a claim about prevalence or model specificity. Without that dataset, report the model attribution as unverified.

The cases are suitable for semantic review. They do not justify a branch-count rule, a deterministic lint gate, or a permanent skill change without an actual comparison.
