## Why

Issue #164, change 3 of 3. Since 5.74.0 and 5.75.0, a Keel release reaches a Claude project's plugin and CLI with nobody acting. What still waits is the protocol. Each repository's `AGENTS.md` carries a managed block stamped with the version that wrote it, and only `keel --install` in that repository moves it. Today the agent notices the mismatch — `AGENTS.md` asks it to compare `keel context`'s `Keel:` line against the stamped version — and then has to stop and ask, every time.

The owner decided (#164, option (i)) that the agent should refresh the block under a standing authorization declared in `keel/config.yaml`, leaving the owner only the commit.

## What Changes

- **A seventh `authorize:` name, `protocol-refresh`.** It covers exactly one action: running the refresh `keel context` names when the repository's managed protocol is older than the running Keel. Like every other name, it removes the confirmation and never a gate, and nothing rides along with it. It does not commit.
- **`keel context` names the refresh.** When the stamped protocol is strictly older than the running Keel, it prints one `Protocol:` line. The line gives both versions and the refresh command, `keel --install --target <t>`, with the target inferred from what the installer left in the repository. It also says whether the refresh is standing-authorized, or deferred because a task's write guard is active. The JSON result carries the same fields. A protocol that is equal or newer prints nothing, and so does Keel's own source repository, whose `AGENTS.md` is authored rather than installed.
- **The protocol says what to do with it.** `AGENTS.md` and the consumer bootstrap gain one rule. Under `protocol-refresh`, run the named refresh before other work and never while a write guard is active. Report it, and leave the diff uncommitted. Without the authorization, ask.

## Capabilities

### Modified Capabilities

- `keel-standing-authorization`: the vocabulary gains `protocol-refresh`, with its scope stated.
- `keel-stateless-continuity`: `keel context` reports a managed protocol older than the running Keel, with the refresh and its authorization.

## Impact

- `src/core/config.js`, `src/core/context.js`, `scripts/validate_plugin.py`, `AGENTS.md`, `assets/bootstrap/AGENTS.md`, `README.md`, `keel/config.yaml`.
- An older Keel reading a declaration that lists `protocol-refresh` fails closed: the whole declaration authorizes nothing until it is corrected. This is the same compatibility behavior `continuation` documented when it was added.
