## Why

Issue #499, reported from kaiwu-ip on 2026-11-02 (Keel 5.215.0) and taken up at the owner's request on 2026-11-08 ("继续，除 175，其它都要解"). A project that wants a session to publish a tag has no way to say so in `keel/config.yaml`: the Claude write guard denies every explicit tag refspec as undetermined (`refs/tags/x is not a branch`), a push carrying tags is allowed only as an ask on a `push-protected:` branch, and the owner's in-session approval cannot help because the deny fires before any ask. The real case: the owner approved pushing two annotated tags that preserve parked work, and the only way left was for the owner to type `! git push …` themselves; release tags hit the same wall.

## What Changes

- **A new authorization, `push-tag:<tag glob>[@<role>]`.** It lets a session of a matching role (every session without `@role`) push an explicit tag whose name matches the glob: `git push origin refs/tags/<name>`, `refs/tags/<name>:refs/tags/<name>`, `<src>:refs/tags/<name>` and `git push origin tag <name>`. The glob is a tag name with `*` matching within one `/` segment, as the branch globs do.
- **A tag outside the grants is denied with a message naming the grant** (`push-tag:`), and one a different role may push names that role, as `push:` does.
- **Unchanged, on purpose:** `--tags`, `--mirror`, `--follow-tags` and `push.followTags` keep today's verdicts (undetermined, or the protected-branch ask); no branch grant carries tags implicitly; deleting a tag (`--delete`, `:refs/tags/x`) is still refused as undetermined, since no grant covers it.
- A repository that declares only `push-tag:` limits tags and leaves branch pushes alone.
- `keel --doctor` lists the `push-tag:` grants with the others and says the guard enforces them; a malformed `push-tag:` entry voids the declaration like any other typo.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-touch-write-guard`

## Impact

`src/core/config.js`, `plugins/keel/scripts/pretooluse-guard.js`, `bin/keel.js`, `scripts/validation/guard.py`, `scripts/validation/registry.py`, `README.md`, `README.zh-CN.md`, `keel/config.yaml` (its vocabulary comment), the published spec, and the changelog.
