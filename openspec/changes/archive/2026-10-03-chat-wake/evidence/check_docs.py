"""Task 1.3 M2: the five documents describe `keel chat wake` and keep the no-polling warning."""
import re
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
docs = ["docs/chat-slack-setup.md", "docs/chat-slack-setup.zh-CN.md", "docs/codex-validation.md", "README.md", "README.zh-CN.md"]
statements = {
    "names keel chat wake": r"keel chat wake add",
    "needs chat-reply": r"chat-reply",
    "one thread with compaction": r"(compact|压缩)",
    "keeps the no-polling warning": r"(not poll the chat with the model|must not poll the chat with the model|不要让模型定期)",
}
failures = []
# Wake statements must sit in a section (## or ###) that names the waker;
# the no-polling warning may be anywhere in the document.
for doc in docs:
    text = (root / doc).read_text()
    blocks = re.split(r"\n(?=#{2,3} )", text)
    wake_text = "\n".join(block for block in blocks if "keel chat wake" in block)
    for name, pattern in statements.items():
        haystack = text if name == "keeps the no-polling warning" else wake_text
        if not re.search(pattern, haystack):
            failures.append(f"{doc}: lacks {name}")
validation = (root / "docs/codex-validation.md").read_text()
if "nothing wakes an idle Codex session" in validation:
    failures.append("docs/codex-validation.md: still says nothing wakes an idle Codex session")
usage = subprocess.run(["node", str(root / "bin/keel.js"), "chat", "help"], capture_output=True, text=True).stdout
for command in ("keel chat wake add", "keel chat wake remove", "keel chat wake status"):
    if command not in usage:
        failures.append(f"keel chat help lacks {command}")
print(f"checked {len(docs)} documents x {len(statements)} statements, plus codex-validation wording and keel chat help")
print("failures: " + ("; ".join(failures) if failures else "none"))
sys.exit(1 if failures else 0)
