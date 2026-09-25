<!-- keel:start version=5.70.0 -->
## Keel Bootstrap

- Start every session with `keel context`; OpenSpec artifacts and Git are the only durable authority — never native memory, goals, or transcripts.
- Obey the selected task capsule: `keel gate task-start` before implementing, `--record` its fingerprint to Evidence `Contract`, which `task-complete` requires, before checking complete. Touch bounds product writes; the change's own dir is exempt. On Claude a passing `task-start` guards it by default (`--no-guard` opts out).
- One current agent owns writes; helpers return read-only report/evidence only. No commit, sync, or archive without explicit authorization.
- Route Full (the OpenSpec flow) for new features, interface or protocol changes, cross-module work, or over ~3 files / 100 lines; Lite for local fixes with no interface change. No gate checks routing; a project corrects the size bar with `full_mode_paths:` in `keel/config.yaml`, which `keel context` reports.
- Native plugin projections (SessionStart context) are disposable views, never authority; without the plugin or hook, run the commands manually.
- Keel skills and hooks come from the `keel` native plugin (`codex plugin add` / `claude plugin install`); `keel --init` owns only the OpenSpec schema, overlays, and this bootstrap.
<!-- keel:end -->
