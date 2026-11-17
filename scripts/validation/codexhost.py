"""Public Codex CLI against an isolated WebSocket stand-in, not a real model host."""
import subprocess
from validation.common import ROOT, report

CODEX_HOST_EVIDENCE = {"hook_event_name": "PreToolUse", "transport": "stand-in WebSocket"}

def validate_codex_managed_host_scenario() -> int:
    result = subprocess.run(["node", "--test", str(ROOT / "scripts/test_codex_host.js")], cwd=ROOT, capture_output=True, text=True, timeout=45)
    if result.returncode:
        report(result.stdout + result.stderr)
        return 1
    report("codex-managed-host scenario passed (" + CODEX_HOST_EVIDENCE["transport"] + "; native hook payload policy).")
    return 0
