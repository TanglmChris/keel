## Context

Issue #307 and the owner's decision of 2026-10-12 recorded on it; part 1 shipped in 5.121.0 (#309). Quota thresholds (part 2) follow in their own change and will add a risk of their own.

## Facts

- F1 — 5.115.0's `--notify` sends every `changed:` line, including shift-status and remote-tip changes (`keel-coordinator-patrol` / A patrol run reports only what changed since the last one).
- F2 — The owner's rule for the coordinator (#307): report quota thresholds, low disk, a dirty shared checkout, and a nudge left unanswered twice; not shift-status changes or new commits.
- F3 — Keel cannot measure free disk on the host's terms; the host-run task can, as it already does by hand.

## Decisions

- D1 — Risks are computed on every run. The checkout risk applies when the snapshot's `checkout <path>` entry goes from `0 uncommitted paths` to more: `the shared checkout <path> has <n> uncommitted paths`. With `--disk-free-gb <n>`, the snapshot gains a `disk` entry, `low` or `ok` against `--disk-min-gb` (default 20); the disk risk applies when it turns `low`: `free disk is <n> GB, below <min> GB`.
- D2 — Unanswered nudges: when an unread nudge is sent and the role's oldest waiting record predates its previous unread nudge, the role's `unanswered` count rises by one, otherwise it becomes 1; a role with nothing waiting resets it to 0. When it reaches 2, the unanswered risk applies: `<role> has not answered 2 nudges; <n> record(s) addressed to it have waited since <created>`. `KEEL_PATROL_UNREAD_EVERY_MS` overrides the two-hour window, for tests.
- D3 — `--notify` (still requiring `--since-last`) sends one direct message from `keel-patrol` listing the run's risks, and nothing when there are none. Risks print as `risk:` lines, are in `--json` as `risks`, and keep a run's exit at 2.
- D4 — Every run of `keel patrol` (not `keel patrol task`) appends `<time> exit=<code> changes=<n> nudges=<n> risks=<n> notified=<yes|no>` to `<chat root>/patrol/log/<role>.log`.
