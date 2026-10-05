## Context

Issue #226.

## Facts

- F1 — `launchctl bootout` returns before the service is gone; a `bootstrap` issued meanwhile fails with `Bootstrap failed: 5: Input/output error`, observed 2026-10-05 on macOS 26 (Darwin 25.6.0), and a later bootstrap of the same plist succeeded.
- F2 — `start()` in `src/core/chat/lifecycle.js` accepts a failed bootstrap whose output matches `already`, `in progress`, or `5:`, so the failure in F1 reported success.
- F3 — `launchctl print gui/<uid>/<label>` prints `state = …` and `pid = …` for a loaded service and exits non-zero with `Could not find service` for an unloaded one.
- F4 — `readStatus()` in `src/core/chat/bridge.js` decides `running` only by signalling the status file's pid, which can still exist while exiting or be reused.

## Decisions

- D1 — The bridge reads launchd's view through one helper: loaded with state and pid when `print` shows a `state =` line, unloaded when `print` fails with `Could not find service`, and unknown otherwise (a system without launchctl, or a test double that prints nothing). Unknown keeps today's behavior.
- D2 — `start` returns at once, saying so, when launchd reports the service running. Otherwise it retries `bootstrap` every 500 ms while it fails with `5:`, `already`, or `in progress`, until it succeeds or the wait (10 s, `KEEL_CHAT_LAUNCHCTL_WAIT_MS` for tests) runs out; then it fails naming launchctl's last output. Any other failure fails at once.
- D3 — `stop` waits, within the same bound, until launchd reports the service unloaded; `install` boots out, waits the same way, then bootstraps with D2's retry.
- D4 — The bridge records in its status file whether launchd started it (launchd sets `XPC_SERVICE_NAME` to the agent's label). For such a status file, `status` reports not running when launchd reports the service unloaded, or loaded with a pid other than the status file's. A bridge run by hand (`keel chat bridge run`) is judged by its pid alone, as today, because launchd knows nothing about it.
