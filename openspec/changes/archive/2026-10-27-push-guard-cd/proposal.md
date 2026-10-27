## Why

Issue #486, approved by the owner on 2026-10-27 with the conservative fix. The push guard reads `push:` and `push-protected:` from the repository the session runs in, or the one `git -C` names. A `cd` earlier in the same call only counted when the push needed the current branch. With an explicit refspec, the target was checked against the session repository's rules even though the push ran in another repository. kaiwu-ip's kaiwu-layout session hit this on 2026-10-27: `cd <export dir> && git push --force-with-lease=main:<sha> https://github.com/…/kaiwu.git main:main` was denied as kaiwu-ip's `push-protected:main@kaiwu-chief`, though the export directory is a separate repository with no Keel config, and the owner had approved that push.

## What Changes

- **A `cd` or `pushd` before a push makes its repository unknown**, whatever the refspec, in a repository that declares a push scope. The call is denied, and the reason says the directory changes before the push and names `git -C <directory> push` as the form to use, instead of `git push origin <branch>`.
- `git -C <directory> push …` is judged by that directory's repository, as before.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-touch-write-guard`

## Impact

`plugins/keel/scripts/pretooluse-guard.js`, `scripts/validation/guard.py`, `scripts/validation/registry.py`, the published spec, and the changelog.
