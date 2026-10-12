## Context

Issue #307 and the owner's decision of 2026-10-12 recorded on it; parts 1 and 3 shipped in 5.121.0 and 5.122.0.

## Facts

- F1 — The host-run patrol in rtl_ppa_prj reads the weekly quota's percent used from the Claude desktop app (`get_usage`); Keel has no access to it.
- F2 — The owner's rule (#307): no report at 50 %; report at 90, 95, and 99 %, once each per quota period; at 90 % or more, no nudges, only reports to the coordinator.

## Decisions

- D1 — `--quota <percent>` (0–100), `--quota-alerts <list>` (default `90,95,99`), `--quota-quiet-at <percent>` (default 90); malformed values are refused by name.
- D2 — State in `<chat root>/patrol/quota.json` (`{ last, reported }`). When `--quota` is below the stored `last`, `reported` empties (a new period). Each threshold at or below the figure that is not in `reported` is added to it, and the highest of those becomes one risk: `weekly quota is at <p>%, past <t>%`. A run without `--quota` leaves the state alone.
- D3 — With `--quota` at or above `--quota-quiet-at`, `--nudge` sends nothing and prints `nudges paused: quota at <p>%`.
- D4 — The quota risk joins the run's risks, so `--notify` sends it, it prints as `risk:`, and the run log counts it (5.122.0).
