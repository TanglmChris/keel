## Decisions

- D1 — Use `thread/read(includeTurns: false)` to verify identity and `thread/turns/list` with descending order and `itemsView: notLoaded` to find a matching turn. Retain only the page being searched.
- D2 — Limit the page loop to the existing RPC timeout budget. Stop on missing, malformed or repeated cursors and keep the exact turn unknown. Observe the terminal inventory independently after the thread identity check.
