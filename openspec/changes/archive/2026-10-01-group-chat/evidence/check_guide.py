import re, subprocess, sys
from pathlib import Path
root = Path(sys.argv[1])
help_text = subprocess.run(["node", str(root / "bin/keel.js"), "chat", "help"], capture_output=True, text=True).stdout
missing = []
for doc in ("docs/chat-slack-setup.md", "docs/chat-slack-setup.zh-CN.md", "README.md", "README.zh-CN.md"):
    text = (root / doc).read_text(encoding="utf-8")
    for line in re.findall(r"keel chat [^`\n|]*", text):
        words = line.split()
        sub = words[2] if len(words) > 2 else None
        if sub and not sub.startswith(("<", "\"", "[")) and sub not in ("soc",) and not sub.startswith("--"):
            if f"keel chat {sub}" not in help_text and f"| {sub}" not in help_text and f"|{sub}" not in help_text and f"{sub}|" not in help_text:
                missing.append((doc, sub))
        for token in words[2:]:
            if token.startswith("--") and token.split("=")[0] not in help_text:
                missing.append((doc, token))
        if sub == "bridge" and len(words) > 3:
            for action in words[3:]:
                if re.fullmatch(r"[a-z]+", action) and action not in help_text:
                    missing.append((doc, f"bridge {action}"))
print("checked", len(re.findall(r"keel chat", " ".join((root / d).read_text(encoding="utf-8") for d in ("docs/chat-slack-setup.md", "docs/chat-slack-setup.zh-CN.md")))), "mentions")
print("missing:", sorted(set(missing)) or "none")
