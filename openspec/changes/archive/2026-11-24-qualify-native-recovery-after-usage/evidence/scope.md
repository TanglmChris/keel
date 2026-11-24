# Scope of the native checkpoint probe

Run `python3 -u evidence/probe.py` from this archived change on Linux with Codex 0.171.0, Claude Code 2.1.325, Git, and Python pexpect present. The fixture uses real native clients, synthetic loopback model responses, temporary profiles and one disposable worktree. It passes no real provider credentials. Native trust is exercised only in the disposable Claude profile and only for that fixture worktree.

The fixture observes a Codex write, its following native tool receipt and structured usage-limit turn failure. It terminates the isolated source host, checks its process has exited and runs a Claude background session in the same worktree. One explicitly allowed fixture tool verifies the original marker is exactly one line before creating a separate artifact.

The fixture drives the transition itself. It checks neither production writer fencing nor network effects, resource budgeting, the inverse direction, surviving child processes, live account quotas, or Keel automatic dispatch. Those remain part of #544.
