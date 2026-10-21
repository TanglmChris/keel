## Decisions

- **D1** — Count a set, not a mention. For each derived marker `M`, the code counts it only in one of these forms:
  - `"M":` or `'M':`, as a dict key;
  - `["M"] =`, as an item assignment;
  - `M=`, in shell or keyword form;
  - `.M =`, as an attribute assignment.

  `hook_event_name` is matched the same way, because a payload is a dict that sets it. A path join ending in a host program's name still counts as it stands: writing such a file is the stand-in. Reading a variable, such as `os.environ.get("CLAUDE_PID")`, and removing one, such as a name in a tuple of variables to strip, no longer count.
- **D2** — Evidence. `release-evidence-classes` keeps all its current assertions and adds one: `chat-core` is deterministic. `chat-core` reaches the host variables only through `chat_environment`, which strips them. The existing stand-in assertions keep the new rule honest in the other direction.
