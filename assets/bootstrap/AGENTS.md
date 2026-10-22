<!-- keel:start version=5.196.0 -->
## Keel Bootstrap

- Start every session with `keel context`; OpenSpec artifacts and Git are the durable authority, and memory or transcripts may only inform.
- Memory: write only what the next session would get wrong without it and the repository cannot answer, never a one-off slip; one fact per entry. Recheck it after a fix, at a release, and at a shift change.
- Obey the selected task capsule: `keel gate task-start` before implementing, `--record` its fingerprint to Evidence `Contract`, which `task-complete` requires, before checking complete. Touch bounds product writes; the change's own dir is exempt. On Claude a passing `task-start` guards it by default (`--no-guard` opts out).
- Work through an approved `tasks.md` in order, each task through its own gates. A subagent is the model's choice and is treated as the main agent is. No commit, push, sync, or archive unless the task, the owner, or `keel/config.yaml` authorizes it.
- Route Full (the OpenSpec flow) for new features, interface or protocol changes, cross-module work, or over ~3 files / 100 lines; Lite for local fixes with no interface change. No gate checks routing; a project corrects the size bar with `full_mode_paths:` in `keel/config.yaml`, which `keel context` reports.
- SessionStart projections are disposable views, never authority; without the plugin, run the commands by hand.
- Keel skills and hooks come from the `keel` native plugin (`codex plugin add` / `claude plugin install`); `keel --init` owns only the OpenSpec schema, overlays, and this bootstrap.
<!-- keel:end -->
