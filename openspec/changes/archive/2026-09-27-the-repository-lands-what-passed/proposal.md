## Why

Two things, both in `.github/workflows/publish.yml`.

**#157 — the 5.70.0 concurrency group drops versions.** GitHub's default `queue: single` keeps at most
one *pending* run per group, and a newer run cancels the one waiting. `cancel-in-progress: false` protects
only the running publish. So a burst of three or more releases publishes the first and the last and
cancels the rest — strictly worse than the read-side confusion 5.70.0 fixed, where nothing was lost.
5.70.0's changelog calls `cancel-in-progress: false` "the load-bearing half"; it is one of two.

**#155 follow-up — the owner wants merge-to-publish with no human step and no stored secret.** The
earlier sketch chained three workflows (auto-merge → push to `main` → release → publish) and needed a
personal token, because events made with `GITHUB_TOKEN` start no new workflow runs, so every hand-off
would break. The chain is the problem, not the token.

## What Changes

- **`queue: max` joins the group**, keeping up to 100 pending runs in FIFO order. The scenario refuses a
  group without it, and the 5.72.0 changelog corrects the 5.70.0 claim instead of leaving it standing.
- **`publish.yml` gains a `land` job** triggered when `Full gate` completes and when a pull request
  opens. It finds an open pull request into `main`, authored by the repository owner from this
  repository, whose head is the commit `full-gate` just passed on; confirms the `full-gate` check-run
  succeeded; and merges it with `--match-head-commit`, so what merges is what was tested. It checks out
  nothing and runs no pull-request code.
- **The `publish` job runs in the same workflow run** after a merge: it checks out the merge commit, and
  if `package.json`'s version has no tag it publishes to npm and then creates the tag and release. One
  run, no hand-off, so `GITHUB_TOKEN` is enough and no secret is stored. The existing
  `release: published` path is unchanged for manual releases.
- **`keel/config.yaml` declares `merge: repository:full-gate`** — true from the moment this change lands,
  since this change is what makes it true.

## Capabilities

### Modified Capabilities

- `keel-validation-runner`: the publish workflow keeps every pending run, and lands only what passed.

## Impact

- `.github/workflows/publish.yml`, `scripts/validate_plugin.py`, `keel/config.yaml`, `README.md`.
- **Not adopted**: a separate workflow file. npm's trusted publishing is bound to `publish.yml` by name,
  and splitting the job would reintroduce the hand-off `GITHUB_TOKEN` cannot make.
