## ADDED Requirements

### Requirement: A rejection becomes a Reauthorizations entry the author writes, not a gate write
A task's `Evidence` MAY carry a `Reauthorizations` entry, sibling to `Blocker`, in which the author records in their own words what a gate rejected during this task and what changed in response. No gate MAY write this entry on any outcome, passing or failing; recording a rejection MUST remain solely the task author's act, on the same trust boundary as `Findings` and the rest of Evidence.

`task-complete` MUST validate only the entry's shape. An absent entry, `none`, or `pending` MUST NOT produce a problem. Any other content MUST be concrete: not empty, and carrying no unfilled `<slot>`/`TODO`/`TBD`/`placeholder` token. `task-complete` MUST NOT judge whether a rejection factually occurred, and MUST NOT require the entry's presence or its count to match any other record, because no gate writes on a failing outcome and nothing else records how many times one occurred.

A concrete `Reauthorizations` entry MUST NOT by itself fail or block `task-complete`, unlike a concrete `Blocker`. Presence is a log entry, not a stop condition; a task that recorded real rejections and resolved them MUST still be able to complete.

A `Reauthorizations` entry that spans more than one line MUST be read from its label line to the next sibling Evidence entry at the same or shallower indentation, the same extent `reviewValue()` already computes for the four Review entries, so a wrapped entry is not truncated at its first line.

#### Scenario: An absent entry needs nothing
- **WHEN** a task's `Evidence` declares no `Reauthorizations` entry at all
- **THEN** `task-complete` reports no `reauthorizations-shape` problem

#### Scenario: A bare none needs nothing
- **WHEN** a task's `Evidence` reads `Reauthorizations: none`
- **THEN** `task-complete` reports no `reauthorizations-shape` problem

#### Scenario: A wrapped concrete record is accepted whole
- **WHEN** a task's `Evidence` records one or more concrete `Reauthorizations` entries, wrapped across several indented lines
- **THEN** `task-complete` reports no `reauthorizations-shape` problem
- **AND THEN** the verdict is the one it returns for the identical text joined onto a single line

#### Scenario: An unfilled slot is refused
- **WHEN** a task's `Evidence` `Reauthorizations` entry carries an unfilled `<slot>` token rather than concrete text
- **THEN** `task-complete` reports a `reauthorizations-shape` problem naming the unfilled token

#### Scenario: A concrete record does not block completion
- **WHEN** a task's `Evidence` `Reauthorizations` entry is concrete and every other required check passes
- **THEN** `task-complete` still passes, unlike a concrete `Blocker` entry
