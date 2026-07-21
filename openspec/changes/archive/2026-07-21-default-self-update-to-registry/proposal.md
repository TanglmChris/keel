# Default self-update to the published registry package

## Why

`keel --update` defaults its fetch source to the git spec `github:TanglmChris/keel`
(`bin/keel.js` `DEFAULT_UPDATE_SOURCE`), so it runs `npm pack github:TanglmChris/keel`
— a git-type fetch. In npm environments that disable git-type fetches (enterprise
or locked-down `npm`), this hard-fails with `EALLOWGIT`
("Fetching packages of type \"git\" have been disabled") and the CLI is stuck on
the old version — even though `@christang/keel` is published to the npm registry
(`latest`). Reported as GitHub issue #4.

The git default is a pre-publication leftover: releases now ship to the registry
through the OIDC publish workflow, so the registry `latest` is the canonical
released CLI. The default self-update source should point at the published
package, not a git spec.

## What changes

- `DEFAULT_UPDATE_SOURCE` becomes the published registry package `@christang/keel`,
  so `keel --update` with no `--source` packs a registry-type spec that works where
  git-type fetches are disabled.
- Add a validator scenario locking the default: `keel --update --dry-run` with no
  `--source` plans a pack of `@christang/keel` and never a git-type spec.

## Non-goals

- No change to the explicit `--source` / `KEEL_UPDATE_SOURCE` override — a git spec
  such as `github:TanglmChris/keel` stays available for installing an unreleased
  build, and the existing update-pack-install scenario keeps proving it.
- No `EALLOWGIT` detection/auto-fallback (issue #4 options B/C); changing the
  default is the root fix and the whole scope here.
- No README change — the "install the latest unreleased build from GitHub" section
  documents the intentional git path and stays as is.
- No version bump or release; this lands on `main` and folds into a later release
  decided separately.
