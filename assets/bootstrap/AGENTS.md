<!-- keel:start version=5.2.4 -->
## Keel Bootstrap

- Start every session with `keel context`; OpenSpec artifacts and Git are the only durable authority — never native memory, goals, or transcripts.
- Obey the selected task capsule: `keel gate task-start` before implementing, record its fingerprint in the task Evidence `Contract` line, and pass `keel gate task-complete` before checking complete. Touch is the write boundary; on Claude a passing `task-start` guards it by default (`--no-guard`/`keel guard clear` opt out).
- One current agent owns writes; helpers return read-only report/evidence only. No commit, sync, or archive without explicit authorization.
- Native plugin projections (SessionStart context) are disposable views, never authority; without the plugin or hook, run the commands manually.
- Keel skills and hooks come from the `keel` native plugin (`codex plugin add` / `claude plugin install`); `keel --init` owns only the OpenSpec schema, overlays, and this bootstrap.
<!-- keel:end -->
