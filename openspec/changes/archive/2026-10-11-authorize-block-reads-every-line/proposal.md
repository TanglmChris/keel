## Why

Issue #275, found while adding `push:<branch glob>` (#257): in `authorize:`, a list item containing a space (`- push:main branch`) ends the block. That entry and every entry after it are dropped silently, and `keel --doctor` reports `authorize: ok`. Every other malformed entry is named and voids the declaration; this one shrinks it without a word. The same reader also drops an item carrying a trailing YAML comment (`- commit  # why`).

## What Changes

- Inside `authorize:`, every indented, non-comment line is an entry: a list item is read whole, and any other indented line is read as written. Each is then classified like any entry, so an unreadable one is refused by name and voids the declaration. Only a line at column zero ends the block.
- A trailing ` # comment` is stripped from an item before it is read, in `keel/config.yaml`'s reader and in the push guard's own reader.

## Capabilities

### Modified Capabilities
- `keel-standing-authorization`: every line of the block is read; none is dropped.

## Impact

`src/core/config.js`, `plugins/keel/scripts/pretooluse-guard.js`, `scripts/validate_plugin.py`, the published spec, and the changelog. A declaration that silently lost entries now fails closed and names the line.
