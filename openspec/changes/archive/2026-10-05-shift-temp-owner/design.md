## Context

rtl_ppa_flow's report of 2026-10-06.

## Facts

- F1 — The three worktrees reported lay under `/private/tmp/claude-501/-Users-my-home-mac-my-github-rtl-ppa-prj/<session>/scratchpad/`. Those are sessions started in the main checkout. The flow session runs in `.claude/worktrees/rtl-workflow-dev-optimization-c6f6ee`, and its scratchpad sits under a slug ending `-c6f6ee`.
- F2 — Claude's scratchpad slug for a session is its working directory with each non-alphanumeric character replaced by `-`. This session's is `-Users-my-home-mac-my-github-keel--claude-worktrees-keel-optimization-maintenance-0cb8d4` for `/Users/my_home_mac/my_github/keel/.claude/worktrees/keel-optimization-maintenance-0cb8d4`.
- F3 — Git does not record which session created a linked worktree.

## Decisions

- D1 — A temporary linked worktree is an item only when its path matches `claude-<digits>/<slug>/<session>/scratchpad/`, with the slug equal to this worktree's path slugged as in F2. Every other temporary linked worktree is a note naming its path, which keeps it visible without blocking a shift change it may have nothing to do with (F3).
