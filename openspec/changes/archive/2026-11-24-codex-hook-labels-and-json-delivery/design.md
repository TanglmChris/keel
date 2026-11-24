## Decisions

- D1 — Use Codex 0.171.0's `statusMessage` for four distinct labels. Native review keys, executable commands, order, matchers and timeouts stay as defined. The label changes these definitions' review hashes. Review remains explicit under the Codex host, with commands and purpose documented. The upstream version's own Hooks Browser snapshot shows the label on the event row.
- D2 — Let Node drain stdout before terminating the SessionStart and PreToolUse programs. Preserve process status and the existing projection, deny, and ask payloads. Test the actual executable receiving host-shaped input against a deliberately slow pipe.
- D3 — Track live hook failures separately until an original native completion event identifies the cause. Publish a minimal capture boundary and distinguish ordinary hook failures from explicit write guard denials and from review state.
