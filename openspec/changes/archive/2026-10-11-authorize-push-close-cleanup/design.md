## Context

Issue #257 and the owner's decision on it (2026-10-11): add the three names, and have the write guard enforce the push branch. Two follow-up choices were put to the owner on 2026-10-11 and answered: the push check runs whenever `push:<glob>` is declared, not only while a task is active; and a push whose target branch the guard cannot determine is refused with the explicit form to use.

## Facts

- F1 — `src/core/config.js` keeps the closed vocabulary in `STANDING_AUTHORIZATION_ACTIONS`, the required-scope actions in `SCOPED_AUTHORIZATION_ACTIONS`, and each scope's form and pattern in `AUTHORIZATION_SCOPES`; `classifyAuthorizationEntry` refuses a scope on an unscoped action and a missing scope on a scoped one, and one bad entry voids the declaration.
- F2 — `bin/keel.js` `printStandingAuthorizationSurface` prints one line per action and a `scope carried` line saying Keel does not enforce scopes.
- F3 — `plugins/keel/scripts/pretooluse-guard.js` is a standalone hook script, never spawns the keel CLI, always exits 0, and denies through hook output. `plugins/keel/hooks/hooks.json` registers it for `Edit|Write|NotebookEdit` only, and returns early for any other tool.
- F4 — The published guard spec states that non-file-edit tools are not intercepted and that `Bash` is disciplinary, and the standing-authorization spec states that a scope is never enforced.
- F5 — Codex's guard capability is reported `manual` (keel-touch-write-guard, "Unsupported targets report manual").

## Decisions

- D1 — `push` takes an optional scope: bare `push` keeps its meaning; `push:<glob>` may repeat, one glob per entry, with the glob drawn from branch-name characters plus `*`. A declaration holding both a bare `push` and a `push:<glob>` is refused, because the bare form would silently widen the scoped one.
- D2 — Globs match a branch name with the Touch guard's semantics: `*` within one `/`-separated segment, `**` across segments. `refs/heads/` is stripped before matching.
- D3 — The push check is independent of the task manifest and of whether the rest of the declaration is valid: the hook reads `push:` entries itself, so a typo elsewhere that voids the declaration fails toward more checking, not less (owner, 2026-10-11).
- D4 — The hook finds `git push` in a `Bash` command by splitting on `&&`, `||`, `;`, `|`, and newlines, skipping leading `VAR=value` assignments, and accepting `git` global options `-C <path>` and `-c <k=v>`. A target is determined from an explicit refspec (`dst` of `src:dst`, `src` alone, `HEAD` as the current branch, `:dst` as a delete) or, with no refspec, from `git rev-parse --abbrev-ref @{push}` in the resolved directory.
- D5 — The target is undetermined, and the push refused with `git push origin <branch>` named, when the command uses `--all`, `--branches`, `--mirror`, or `--tags`, an option the hook does not know, shell expansion (`$`, backticks) in the push segment, a `cd`/`pushd` before a push that needs the current branch, a tag refspec, or when `@{push}` does not resolve (owner, 2026-10-11).
- D6 — `issue-close:<owner>/<repo>` uses the `issue:` form and pattern; `cleanup:scratch` accepts exactly `scratch` as its scope. Both are carried, not enforced, like `issue:`.
- D7 — Claude only. Codex's guard stays `manual` (F5); `hooks/codex.json` is not changed.
