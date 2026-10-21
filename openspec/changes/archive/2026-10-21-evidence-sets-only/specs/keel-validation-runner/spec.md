## MODIFIED Requirements

### Requirement: The suite states what kind of evidence ran
The runner MUST classify every registered scenario as either deterministic or run against a stand-in host. It MUST derive the stand-in markers from Keel's own sources. A scenario counts as run against a stand-in host only where its code sets a marker; naming a marker in order to remove or read it does not count. When `--all` or `--group` passes, it MUST print an `evidence:` line that gives both counts, says `none on a real host`, and names `docs/host-contract.md`. The two counts MUST add up to the verified count.

#### Scenario: A scenario that reaches a stand-in through a helper, a hook payload or a script is counted as one
- **WHEN** `validate_plugin.py --evidence` runs against the registry
- **THEN** `shift-cli-self-shift`, `chat-claude-hooks`, `codex-receiving` and `update-pack-install` are listed as run against a stand-in host, and `version-alignment` as deterministic
- **AND THEN** the two counts add up to the number of registered scenarios

#### Scenario: A scenario that only removes host variables is deterministic
- **WHEN** a scenario reaches the host's variables only through `chat_environment`, which removes them so that the suite does not inherit the running session's host, as `chat-core` does
- **THEN** `validate_plugin.py --evidence` lists it as deterministic

#### Scenario: A passing run states its evidence
- **WHEN** `validate_plugin.py --group docs` passes
- **THEN** its last line starts with `evidence:`, its two counts add up to the verified count, and it says `none on a real host` and names `docs/host-contract.md`
