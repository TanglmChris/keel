# Design — default-self-update-to-registry

## Context

`runGlobalUpdate` (`bin/keel.js`) resolves the update source as
`options.updateSource || process.env.KEEL_UPDATE_SOURCE || DEFAULT_UPDATE_SOURCE`,
then runs `npm pack <source> --pack-destination <tmp> --json` followed by
`npm install -g <tarball>`. The help text interpolates `${DEFAULT_UPDATE_SOURCE}`,
so it tracks the constant automatically.

## Facts

- **F1** — `DEFAULT_UPDATE_SOURCE = "github:TanglmChris/keel"` is a git-type spec.
  `npm pack github:...` performs a git-type fetch, which npm rejects with
  `EALLOWGIT` where git-type fetches are disabled (issue #4).
- **F2** — `@christang/keel` is published to the npm registry; `validate_plugin.py`
  already asserts `package.json` name is `@christang/keel`. `npm pack @christang/keel`
  is a registry-type fetch that does not need git.
- **F3** — The explicit `--source github:...` path is exercised by the existing
  `update-pack-install` validator scenario, and the README's "unreleased build from
  GitHub" section documents packing the git spec deliberately. Both must keep working.

## Decisions

### D1 — Default the update source to the registry package `@christang/keel`

`DEFAULT_UPDATE_SOURCE` becomes `@christang/keel`. Rationale: the released CLI is
the registry `latest`; a registry-type default fetches without git and works in
locked-down npm. The git spec remains reachable via explicit `--source` /
`KEEL_UPDATE_SOURCE` for unreleased dev builds, so no capability is lost — only the
default flips from git-type to registry-type.

### D2 — Lock the default with a validator scenario, keep the explicit-git scenario

A new scenario asserts the no-`--source` default plans a pack of `@christang/keel`
and never a git-type (`github:`) spec. The existing `update-pack-install` scenario
(explicit `--source github:...`) is unchanged and now stands as the proof that the
override still honors a git spec. Rationale: the two scenarios pin both halves of
the new requirement independently.

## Risks

- Low. Only the default constant changes; the pack/install pipeline, the `--source`
  override, and `KEEL_UPDATE_SOURCE` are untouched. Anyone who was relying on the
  git default to pull an unreleased `main` must now pass `--source github:...`
  explicitly — documented in the README's unreleased-build section.

## Verification

Regression-first through the CLI's observable `--update --dry-run` plan: a new
validator scenario asserts the default pack plan names `@christang/keel` and no
git-type spec (green after the constant flips; red before, when the plan named
`github:TanglmChris/keel`). The existing explicit-`--source` scenario continues to
prove the git override.
