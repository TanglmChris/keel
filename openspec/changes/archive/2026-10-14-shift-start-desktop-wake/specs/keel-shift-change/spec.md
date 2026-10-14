## MODIFIED Requirements

### Requirement: The coordinator starts the new shift once its note waits

`keel shift start <role>` MUST refuse while no note waits for `<role>`, and otherwise MUST post in the direct group a message that wakes `<role>` and tells it to run `keel context` and then `keel shift resume`, followed by any next-step text given. When the waiting note records `Desktop session: <id>`, the output MUST NOT say the role was woken: a session with no running process on the Claude desktop app sees no chat record (#320). It MUST instead name `get_session`, `unarchive_session`, `send_message`, the session id, and the start text, as the step that wakes it.

#### Scenario: Start before ready is refused
- **WHEN** `rtl` runs `keel shift start verify` before `verify` is ready
- **THEN** it exits non-zero and posts nothing

#### Scenario: Start wakes the role with the resume instruction
- **WHEN** `rtl` runs `keel shift start verify` after `verify` is ready
- **THEN** a message naming `keel shift resume` reaches `dm-rtl--verify` and `verify`'s signal file was touched

#### Scenario: Start for a desktop note names the wake step
- **WHEN** `verify`'s note was written on the Claude desktop app as session `local_test-320` and `rtl` runs `keel shift start verify`
- **THEN** the start record still reaches `dm-rtl--verify`, and the output names `send_message`, `get_session`, `unarchive_session`, `local_test-320`, and `keel shift resume`, and does not say `Woke`
