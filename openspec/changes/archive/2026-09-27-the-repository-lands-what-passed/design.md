## Context

`publish.yml` publishes on `release: published`. 5.70.0 gave it a concurrency group; #157 shows the group
cancels pending runs. #155 asked for the repository, not the agent, to merge; the no-secret design puts
merge, tag, release and publish in one workflow run.

## Facts

- **F1** — GitHub docs: "By default, any existing `pending` job or workflow in the same concurrency group
  will be canceled and the new queued job or workflow will take its place." `queue: max` allows up to 100
  pending runs; it is forbidden only with `cancel-in-progress: true`.
- **F2** — events produced with `GITHUB_TOKEN` (other than `workflow_dispatch`/`repository_dispatch`) start
  no new workflow runs. A merge or release made with it cannot trigger another workflow.
- **F3** — `main` is protected as of 2026-09-27: `full-gate` required, branch up to date, no reviews
  required, admins not enforced. A merge API call on a commit without a green `full-gate` is refused by
  GitHub regardless of what the workflow checked.
- **F4** — npm trusted publishing for this package is configured for the `publish.yml` workflow file.
- **F5** — `test.yml`'s job, and therefore its check-run, is named `full-gate`; its workflow is named
  `Full gate`.

## Decisions

- **D1** — `queue: max` beside `cancel-in-progress: false` (F1), asserted separately: a group that keeps
  one pending run looks identical to a queue until the third event.
- **D2** — one workflow run carries merge through publish (F2, F4). Nothing is handed to another
  workflow, so `GITHUB_TOKEN` suffices and no secret exists to leak or rotate.
- **D3** — the `land` job checks out nothing. `workflow_run` and `pull_request_target` run with write
  permission in the base repository's context, so running pull-request code there would hand that code
  the token. The job only calls the API; the code that runs afterwards is the merge commit on `main`.
- **D4** — only pull requests authored by the repository owner, from this repository (not a fork), into
  `main`. The owner's own pull requests are the ones the agent opens; anything else waits for a person.
- **D5** — merge only after reading the `full-gate` check-run on the exact head commit, and pass
  `--match-head-commit`, so a push after the check cannot slip an untested commit in. Branch protection
  (F3) is the second lock: if this logic is wrong, GitHub still refuses.
- **D6** — publish before tagging. If publish fails, no tag exists and a re-run retries it. If the tag is
  already there, the version was released and the run does nothing. An `npm publish` refused with
  `You cannot publish over the previously published versions` is treated as already published: that is
  the write side's answer, the only one #153 found trustworthy.
- **D7** — the release created in this run does not re-trigger `publish.yml` (F2), which is what keeps a
  landed version from publishing twice.
- **D8** — `workflow_run` ignores completions on `main`, where there is never an open pull request to land.

## Alternatives considered

- **A1** — a personal access token or GitHub App secret driving auto-merge and a chained release
  workflow. Rejected by D2: it only exists to cross hand-offs that one run does not have.
- **A2** — GitHub's auto-merge setting. Not needed: the job merges directly, and `allow_auto_merge`
  stays off.
- **A3** — let the agent enable merging from its local `gh`. Rejected: the outcome is an unreviewed merge
  taken by the agent, which the host's classifier refuses and `## Unattended runs` forbids.

## Open questions

None. This change cannot be exercised locally; its first real use is the next pull request after it
lands, and that run is the end-to-end evidence.
