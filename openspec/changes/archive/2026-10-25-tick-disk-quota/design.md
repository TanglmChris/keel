## Facts

- F1 — `keel tick` runs each due patrol as `keel patrol --repo <worktree> --since-last --notify --json` (`src/core/tick.js`). `keel patrol` turns `--disk-free-gb` against `--disk-min-gb` (default 20) into the `disk` snapshot entry and its risk. It turns `--quota` into the quota risk once per alert step (`quotaRisk`). Since 5.193.0 (#434), both are gated on `coverage.repositoryWide`.
- F2 — Claude Code 2.1.307 has no CLI subcommand that prints usage. The weekly percent reaches only status-line scripts, as `rate_limits.seven_day.used_percentage` (Claude Code changelog). The owner's `~/.claude/statusline-command.sh` already reads `rate_limits`.
- F3 — `fs.statfsSync` (Node ≥ 18.15) gives `bavail * bsize`. On this Mac, for the keel worktree's filesystem, it gave 52.38 GiB, and `df -g` reported 52 available.
- F4 — kaiwu-ip's old host task passed `--quota <n> --disk-free-gb <n>`, read with the host's usage tool and `df -g`.

## Decisions

- D1 — Before each patrol run, the tick measures free space on that patrol's worktree filesystem, `floor(bavail * bsize / 2^30)`, in the same units as `df -g`, and passes `--disk-free-gb <n>`. A failed measurement passes nothing and is reported in the tick output.
- D2 — `disk_min_gb:` (a positive number) and `quota_file:` (a path, absolute or relative to the repository's worktree, with `~` expanded) are repository-wide settings. The tick reads each from the first `patrol:` item that declares it, and passes the values to every patrol run. The patrol's own gating (F1) decides who reports. A malformed value is ignored by name, as other `patrol:` keys are.
- D3 — The first number in the `quota_file:` (an integer or a decimal) is the percent, passed as `--quota`, rounded to an integer, only when the file was modified within the last 6 hours. The tick prints one quota line each time the quota state changes between `read`, `stale`, `unreadable`, and `unchecked`, keeping the last state in `tick/state.json`. So a stale file or an undeclared source is said once, not every 300 s.
- D4 — Keel runs no command to obtain quota (owner, 2026-10-25). Writing the file is the owner's or the host's part. The README shows a one-line status-line addition.
