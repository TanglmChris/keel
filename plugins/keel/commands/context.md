---
description: Show where Keel says this session stands — status, selected task, next action, and version agreement
---

Report the state this session is working from. The mechanism is `keel context`; this command only says what to tell the owner.

```bash
keel context
```

Tell the owner, in the language `keel/config.yaml` declares under `owner_language:`, or else the language they write in:

- the status, and the selected change and task, if any;
- the next action, or the reason there is none;
- the `Keel:` version beside the protocol version in `AGENTS.md`'s `keel:start` marker, and say plainly when they disagree;
- any `Protocol:` or `Warning:` line, as it reads.

Do not start the next action. This command reports; it decides nothing.
