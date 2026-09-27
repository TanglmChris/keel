## Findings

- F1 — The managed block is stamped `<!-- keel:start version=X.Y.Z -->` in `AGENTS.md`, and `CLAUDE.md` carries only an import. The SessionStart hook reads the stamp in `protocolVersion()`. `keel context` does not read it: it reports only `Keel: <running>`, and the protocol asks the agent to make the comparison.
- F2 — `keel --install` refreshes the managed block and the OpenSpec surfaces. Apart from the managed block and a one-time scaffold, it leaves what the project wrote alone, and a second run skips every file already current. It is the command the CLI's own help names: "repeat keel --install to refresh project protocol files".
- F3 — The standing-authorization vocabulary is closed (`STANDING_AUTHORIZATION_ACTIONS` in `src/core/config.js`). An unknown entry voids the whole declaration. Doctor lists every name as `authorized` or `not authorized` by iterating that array, so a new name reaches doctor without doctor changing.
- F4 — In Keel's own source repository `keel --install` skips `AGENTS.md`, because that file is the full protocol. `bump_version.js` moves its stamp, and `version-alignment` holds it equal to the package.
- F6 — A `keel --install --target codex` writes only `AGENTS.md`, `keel/`, and `openspec/` into the repository. Codex's OpenSpec commands are global prompts under `CODEX_HOME`, so there is no `.codex/` surface to recognize. This was measured while M5 was red; D3 first assumed there was one.
- F5 — `continuation-docs` asserts the README's vocabulary comment and `keel/config.yaml`'s as fixed six-name strings.

## Decisions

- D1 — **Name and scope.** The name is `protocol-refresh`, unscoped, because it acts on this checkout. It covers running the command `keel context` names on its `Protocol:` line, and only while that line says the stamp is older. It does not cover committing the result, and it does not cover refreshing when the stamp is equal, newer, or unreadable.
- D2 — **Comparison.** The stamp is read from `AGENTS.md`, then from `CLAUDE.md`, in the hook's order. Both versions are compared numerically as `X.Y.Z`. Only *strictly older* produces a line: a newer stamp means the CLI is the stale one, which the hook's drift line already reports, and a missing or unreadable stamp is not a refresh. Keel's source repository produces no line (F4).
- D3 — **Command.** `keel --install --target <t>`. The target is `claude` when `CLAUDE.md` carries the managed import, `opencode` when `.opencode/commands` exists, and `codex` otherwise (F6): the managed `AGENTS.md` with neither of the other two surfaces is exactly what a Codex install leaves.
- D4 — **Authorization and deferral.** The line says one of three things:
  - `standing-authorized (authorize: protocol-refresh)`;
  - `ask before running it; keel/config.yaml does not standing-authorize protocol-refresh`;
  - when `keel/guard.json` exists, `deferred while a task's write guard is active`, whatever is authorized, because the refresh writes outside any task's Touch.
- D5 — **JSON.** `protocol: {stamped, keel, file, command, authorized, deferred}` appears only when the line does, so an aligned repository's JSON is unchanged.
- D6 — **Protocol text.** One bullet in `AGENTS.md` `## Session Start` and one in the bootstrap. The bullet says: under `protocol-refresh`, run the refresh `keel context` names before other work, never while a write guard is active, report it, and leave the diff uncommitted; otherwise ask. Committing it is a separate action, which a declared `commit` may cover like any other commit and which does not ride along.
