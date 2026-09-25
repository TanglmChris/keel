## Context

#153: eleven concurrent publishes to one npm package produced a registry read side that reported
published versions as missing, and two re-runs were triggered on that false reading.

## Facts

- **F1** — measured: the packument was read three times over several minutes and reported three
  different sets of present versions before settling on all twelve. The write side never agreed that
  anything was missing: re-running the two apparently-absent versions failed with
  `You cannot publish over the previously published versions`.
- **F2** — `publish.yml` has no `concurrency` block, so GitHub runs one job per release event with no
  ordering. Eleven releases created in a loop are eleven simultaneous jobs.
- **F3** — GitHub's default for a declared concurrency group is `cancel-in-progress: true`. For a
  publish job that default is actively wrong: it would cancel a queued publish when the next release
  fires, losing a version for real rather than appearing to.
- **F4** — this workflow's behavior cannot be exercised locally. It runs only on GitHub, only on a
  `release` event, and the suite has no other file in that position.

## Decisions

- **D1** — one concurrency group for the whole workflow, not per version. Per-version grouping would
  be `group: publish-${{ github.ref }}`, which serializes nothing, because each release has its own
  ref. The thing being protected is the package, and there is one of those.
- **D2** — `cancel-in-progress: false`, asserted separately from the group (F3). A check that only
  looked for a `concurrency` block would pass on the configuration that loses versions, which is worse
  than the one this change fixes.
- **D3** — the scenario reads the workflow file rather than running it (F4). It asserts the two keys
  and the `release` trigger they are scoped to, which is what a future edit could silently drop.
- **D4** — no registry polling is added to the workflow. The `+ @christang/keel@<version>` line is
  emitted by the publish itself and is the confirmation; anything that reads the packument back to
  decide whether the publish worked reintroduces exactly the lag this change works around.

## Alternatives considered

- **A1** — create the releases with a delay between them instead. Rejected: it puts the fix in whoever
  happens to be running the release loop, which on 2026-09-25 was an agent and next time may not be,
  and it leaves the workflow wrong for any other cause of simultaneous releases.
- **A2** — have the scenario parse the YAML with a dependency. Rejected: the repository holds no YAML
  parser and reads its own flat config line-oriented for the same reason. Two keys and a trigger are
  matchable without one.

## Open questions

None.
