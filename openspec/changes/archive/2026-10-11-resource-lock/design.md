## Context

Issue #254, and the #250 split of 2026-10-05. The owner decided on 2026-10-11 that this issue's implementation is delegated to codex, run from this session, which reviews the result and re-runs every check.

## Facts

- F1 — The chat store lives in the repository's git common directory (`src/core/chat/store.js` `locate`), shared by every worktree. `store.currentRole(where)` gives a worktree's bound role or null. `store.directPost(where, target, text)` posts a direct message, which wakes the target. `store.isoLocal` stamps local time.
- F2 — `src/core/shift.js` is a self-contained `keel` subcommand built on that store, with a role-optional identity (`ownNotePath` falls back to the worktree's name and id), `writeFileAtomic`, and its own error class whose message `main` prints as `keel shift: …` with exit 1. `keel lock` follows the same shape.
- F3 — Keel schedules nothing (AGENTS.md, Unattended runs), so nothing can fire at an expiry.
- F4 — `keel/config.yaml` declares no `external_agents:`, so `keel agents brief codex` refuses every brief.
- F5 — rtl_ppa_prj also wants CPU slots (JOBS ≤ 8 per machine) coordinated. That is a counted resource, not an exclusive one.

## Decisions

- D1 — A lease is a JSON file at `<common>/keel-chat/locks/<resource>.json` holding `resource`, `holder` (the role, or `worktree:<name>-<id>` when the worktree has none), `role` (or null), `worktree` (absolute path), `acquired`, `expires` (ISO local time), `note`, and `waiters` (a list of the same identities). A resource name is 1–64 characters of letters, digits, `.`, `_`, and `-`, starting with a letter or digit; any other name is refused by name.
- D2 — `acquire` on a free resource creates the file with an exclusive create, so of two racing acquirers exactly one wins and the other is refused. `acquire` by the current holder renews: it replaces `expires` and `note` atomically. `acquire` by anyone else while the lease is live exits 1, naming holder, worktree, expiry, and note, and adds the requester to `waiters` once.
- D3 — `--for` takes `<n>s|m|h|d`; it is required, and so is `--note`, because an unexplained or unbounded claim is the thing that went wrong. `release` by anyone but the holder is refused, naming the holder; there is no force, because an abandoned lease ends at its expiry.
- D4 — Every `keel lock` command first frees each expired lease it finds (F3) and, for each, posts once to the holder and each waiter with a role, from the running worktree's role, `lock <resource> expired at <time> (held by <holder>: <note>)`. With no role in the running worktree, nothing is posted and the freed lease is printed. Release posts `lock <resource> released by <holder>` to each waiter with a role, the same way.
- D5 — `acquire` prints that the lease enforces nothing on Git or the filesystem. `list` prints every live lease, one per line, with `--json` printing them as data; it exits 0.
- D6 — `keel shift check` reports each live lease whose `worktree` is this worktree as an item of kind `lock`.
- D7 — `keel/config.yaml` declares `external_agents: allow: [codex]` with no `egress_deny`: this repository is public, so nothing in it is withheld from the provider.
- D8 — Counted resources such as CPU slots are out of scope (F5). An exclusive lease per slot (`cpu-1` … `cpu-8`) is the workaround the guide names.
