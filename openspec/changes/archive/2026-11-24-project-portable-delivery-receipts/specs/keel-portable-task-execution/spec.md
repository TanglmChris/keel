## ADDED Requirements

### Requirement: Project delivery evidence in the portable task query

For a todo, `keel chat show <id> --json` SHALL include a sibling `delivery` object with a `state` of `unobserved`, `acknowledged` or `unknown`. The query SHALL use local durable evidence for the assignee and the original todo ID. It SHALL preserve chat closure and consult no native runtime. Delivery evidence SHALL NOT certify successful execution or authorize dispatch.

#### Scenario: An upper client reads the same task before and after delivery
- **WHEN** a todo has no observed submission and later acquires a durable acknowledgement
- **THEN** that same query reports unobserved and then acknowledged while keeping the original todo ID and chat state

#### Scenario: A native outcome is ambiguous or not observable
- **WHEN** a matching claim lacks an acknowledgement or the local receipt cannot be interpreted
- **THEN** the query reports unknown and retains the chat task
- **WHEN** no runtime evidence was captured for an assignee
- **THEN** the query reports unobserved without starting or retrying any work
