## Context

Issue #259.

## Facts

- F1 — dsh 0.2.0-rc.2 `--profile headless` reports a workspace-write file policy. In rtl_ppa_prj on 2026-10-05 it refused writes to `/dev/stdout` and to `~/Library/Caches/com.apple.python`, and allowed `/tmp`.
- F2 — It takes no sandbox flag, so the catalog's per-mode `sandbox` field, which is the value Keel passes to the CLI, stays `null` for both modes.
- F3 — Inside the directory it starts in, it writes freely, so a helper still needs a separate worktree, as the write-boundary requirement already demands for a CLI with no read-only sandbox.
- F4 — The reporter's working practice was `TMPDIR=<worktree>/runs/<task>/tmp`, beside that run's brief and result files.

## Decisions

- D1 — A catalog entry gains an optional `ownSandbox` text, printed on the Sandbox line. The per-mode `sandbox` keeps its meaning (F2), and the write-boundary rule is unchanged (F3).
- D2 — dsh's pitfall about having no sandbox is replaced with one stamped from the issue, and pitfalls for `/dev/stdout` and `PYTHONPYCACHEPREFIX` are added (F1).
- D3 — A template's `{tmp}` is filled with `<dirname of --out>/tmp`, which the brief creates and names (F4). dsh's template sets `TMPDIR={tmp}` and `PYTHONPYCACHEPREFIX={tmp}/pycache`. A machine entry with its own template is unaffected unless it uses `{tmp}`.
