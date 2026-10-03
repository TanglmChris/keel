"""Issue #194 task 1.2: each guidance document carries the four statements,
and every `keel chat` command it names exists in `keel chat help`."""
import re, subprocess, sys
from pathlib import Path
root = Path(sys.argv[1])
help_text = subprocess.run(["node", str(root / "bin/keel.js"), "chat", "help"], capture_output=True, text=True).stdout
needles = {
    "no model polling": ["poll the chat with the model", "不要让模型定期"],
    "prompt-time notice": ["prompt-time notice", "下一次对话时的提醒"],
    "gate and fresh thread": ["keel chat notice --check"],
    "fresh thread": ["fresh thread", "新线程", "新的线程"],
    "no recurring checks at start": ["recurring", "定时或循环检查"],
}
failures = []
for doc in ("docs/chat-slack-setup.md", "docs/chat-slack-setup.zh-CN.md", "docs/codex-validation.md", "README.md", "README.zh-CN.md"):
    text = (root / doc).read_text(encoding="utf-8")
    for name, options in needles.items():
        if not any(option in text for option in options):
            failures.append(f"{doc}: lacks {name}")
    for match in re.findall(r"keel chat notice --check", text):
        if "keel chat notice --check" not in help_text:
            failures.append(f"{doc}: names keel chat notice --check, which keel chat help lacks")
print("checked 5 documents x", len(needles), "statements")
print("failures:", failures or "none")
sys.exit(1 if failures else 0)
