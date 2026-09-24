## ADDED Requirements

### Requirement: A scenario that constructs an environment removes only what it named

A scenario that builds a modified environment in order to assert a behavior MUST remove
only the thing it named. Removing a container because it holds the named thing also
removes that container's other contents, and on a host where those contents include the
runtime the scenario needs, the scenario fails for a reason that has nothing to do with
its subject — while its diagnostic still names the subject. Such a scenario MUST also
verify the precondition its assertion depends on before asserting the behavior, and report
a precondition it cannot satisfy as a skip naming the missing runtime, never as a failure
attributed to the tool under test.

#### Scenario: A named tool is removed from PATH without removing its neighbours

- **WHEN** a scenario needs a PATH on which a named tool does not resolve
- **THEN** every other executable on that PATH still resolves at the same search position, including the interpreter the scenario's own child processes require
- **AND THEN** the named tool does not resolve under any extension the host's lookup would consider

#### Scenario: A fixture that removed the interpreter reports a skip that names it

- **WHEN** a scenario has built its environment and the interpreter it needs does not resolve on it
- **THEN** it reports the skip contract, and the reason names the missing runtime
- **AND THEN** no failure is reported against the tool the scenario was constructed to assert about

#### Scenario: The construction is proven on a fixture carrying the layout, from both sides

- **WHEN** the suite asserts that this construction removes only what it named
- **THEN** it builds a directory holding both the named tool and the runtime, so the assertion holds on a host where the two never shared one
- **AND THEN** it asserts that the runtime survived and that the named tool is gone, because a construction that produced an empty directory would satisfy the second assertion alone
