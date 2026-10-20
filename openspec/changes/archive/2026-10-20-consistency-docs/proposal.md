## Why

This is the third and last part of issue #413. The first two parts corrected the protocol surfaces and the two READMEs. What remains is the text a reader of `docs/` or `keel/config.yaml` relies on.

`keel/config.yaml`:
- Its comment blocks do not follow the order `CONFIG_DECLARATIONS` says the file documents them in.
- `patrol` is described twice.
- `executor_tier` has no block.
- The scoped-name sentence omits `push-protected`.

`docs/updating.md`:
- It still says Claude reloads "skills and agents". 5.173.0 removed the agents.
- It does not mention the 5.174.0 Codex fallback (#412).
- It does not mention the registry lag right after a release (#421).

`docs/shift-change.zh-CN.md`:
- It has five sections against the English eight.
- It never mentions `keel patrol` or `keel tick`.

`docs/chat-slack-setup.zh-CN.md`:
- It lacks the sentence that edits and deletions carry over.

`README.md`, three sentences the Chinese rewrite in 5.176.0 found unclear (listed on #413):
- the authorization ordinals beside a list that counts `push:<branch glob>` separately;
- "A clear there keeps no title";
- "noticed expiry".

The README's Commands block mirrors `keel --help`. It does not say that each command group prints its full subcommand list.

## What Changes

- `keel/config.yaml`:
  - one comment block per declaration, in `CONFIG_DECLARATIONS` order, each above its declaration when this repository declares one;
  - a new `executor_tier` block;
  - `push-protected` in the scoped-name sentence.
- `docs/updating.md`:
  - the reload line and the skills row now name skills only;
  - the hung-query fallback and the post-release registry lag are documented.
- `README.md` and `README.zh-CN.md`:
  - the three sentences are rewritten;
  - the Commands block points to each group's own help.
- `docs/shift-change.zh-CN.md` and `docs/chat-slack-setup.zh-CN.md` are brought to their English counterparts.
- Two scenarios hold this:
  - `config-documents-in-declaration-order`;
  - `docs-zh-match-english`, which checks every `docs/*.zh-CN.md` against its English page.
- `keel-native-plugin-package` gains a requirement for both.

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `keel-native-plugin-package`

## Impact

Files touched:
- `keel/config.yaml`
- `docs/updating.md`
- `docs/shift-change.zh-CN.md`
- `docs/chat-slack-setup.zh-CN.md`
- both READMEs
- `scripts/validate_plugin.py`
- the published spec
- the changelog

No behavior changes.
