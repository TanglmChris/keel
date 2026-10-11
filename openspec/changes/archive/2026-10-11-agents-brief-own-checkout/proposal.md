## Why

Issue #262: on 5.95.3, a review session in rtl_ppa_prj asked `keel agents brief dsh --mode helper --dir <repo>/.claude/worktrees/dsh_review_rtl_r3`. It was refused because `--dir … is this session's own checkout`. The directory was a separate worktree. The issue guessed that the check treats anything under `.claude/worktrees/` as the session's checkout.

Reproduced on 5.99.1 with the issue's layout, that guess is wrong. With the command run from the session's worktree or the main checkout, the brief is written. It is refused only when the command runs from inside the helper worktree itself. The check compares `--dir` with the checkout the command runs in, `--repo` or the current directory. The refusal calls that checkout "this session's own checkout", which Keel cannot know, so a session whose shell had moved into the helper read a false sentence about where the problem was.

## What Changes

- The refusal names the checkout it compared against and where that came from (`--repo` or the current directory). It says to run the command from the session's own checkout or pass `--repo <it>`.
- A scenario fixes the issue's layout as accepted: a helper worktree under `<repo>/.claude/worktrees/`, briefed from a sibling session worktree.

## Capabilities

### Modified Capabilities
- `keel-external-agents`: the write-boundary refusal names the checkout it compared against.

## Impact

`src/core/agents.js`, `scripts/validate_plugin.py`, the published spec, and the changelog.
