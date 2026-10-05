## Context

Issue #221.

## Facts

- F1 — In rtl_ppa_prj, codex_comp, codex_mux, codex_wb, and codex_win_chk started at 10-04 17:02; the last three logged `You’ve hit your usage limit` within five minutes, and so did codex_mix_entry (`.claude/worktrees/codex*/runs/*/codex.log`).
- F2 — Of the nine runs, only codex_a2's log carries an `exit=` line, and four left no `LAST.md`; codex_a2 nonetheless finished with `exit=0` and identical signatures.
- F3 — The dsh template contains `cd {dir} &&`, so a command run as printed changes the calling shell's directory unless it runs in a subshell.

## Decisions

- D1 — The printed command is `( <filled template> ); echo $? > <result>.exit`. The subshell keeps a `cd` in a template from moving the caller (F3), and `$?` after it is the template's own status. The exit file sits beside the result so the two are found together. Keel still launches nothing.
- D2 — The parallel-quota fact goes into the codex entry with its date and source, as every pitfall does. Keel does not limit or schedule runs; the fact is there for the session deciding how many to start.
