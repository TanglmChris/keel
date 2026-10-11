## Why

Issue #259: `keel agents dsh` (5.99.0) says `Sandbox: helper none (needs a separate worktree); implementation none`, with the pitfall "It offers no sandbox flag … It reads and writes wherever it is started". Measured in rtl_ppa_prj on 2026-10-05 with dsh 0.2.0-rc.2, `--profile headless` does run under a sandbox, which it reports as a workspace-write file policy. It refused writes to `/dev/stdout` (yosys's `tee -o /dev/stdout` failed, breaking the flow's dependency probe) and to `~/Library/Caches/com.apple.python` (macOS Python's `compileall`), while `/tmp` stayed writable. Believing the catalog, the session expected dsh to write anywhere, and dsh spent about an hour working around `/dev/stdout` and left wrapper scripts in `/tmp`.

## What Changes

- A catalog entry may describe a sandbox its CLI applies by itself. `keel agents dsh` prints dsh's on its Sandbox line, and says a separate worktree is still needed because it writes freely inside its own directory.
- dsh's pitfalls are corrected: the "reads and writes wherever it is started" pitfall is replaced, and two are added, for `/dev/stdout` and for macOS Python's cache directory.
- A catalog template may use `{tmp}`. The brief creates a `tmp` directory beside `--out`, names it, and fills `{tmp}` with it. dsh's template sets `TMPDIR` to it and `PYTHONPYCACHEPREFIX` beneath it.

## Capabilities

### Modified Capabilities
- `keel-external-agents`: an entry's own sandbox is shown, and a template's `{tmp}` is filled beside the brief.

## Impact

`src/core/agents.js`, `scripts/validate_plugin.py`, the published spec, and the changelog.
