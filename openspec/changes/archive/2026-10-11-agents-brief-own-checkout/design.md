## Context

Issue #262, and a reproduction on 2026-10-11 with the issue's worktree layout.

## Facts

- F1 — `worktreeRefusal` in `src/core/agents.js` compares the top level and git common directory of `--dir` with those of `repo`, which is `--repo` or `process.cwd()`. It reads no path prefix. The logic is the same in 5.95.3, the version the issue was reported on.
- F2 — Reproduced with `<repo>/.claude/worktrees/code-review-524201` and `<repo>/.claude/worktrees/dsh_review_rtl_r3`: run from the first or from `<repo>`, the dsh helper brief is written; run from inside the second, it is refused as "this session's own checkout".
- F3 — Claude Code exposes no variable naming the session's directory to a command it runs, so Keel cannot tell the session's checkout from the directory it was started in.

## Decisions

- D1 — The comparison stays as it is (F1). The refusal stops claiming to know the session's checkout (F3): it names the checkout it compared against and whether it came from `--repo` or the current directory, and says to run from the session's own checkout or pass `--repo`.
