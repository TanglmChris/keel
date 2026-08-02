## ADDED Requirements

### Requirement: A non-concrete required field names the token that made it non-concrete

Keel MUST name the matched unfilled-slot token when a required task field — `Covers`, `Verify`, `Evidence`, or the expanded v3 `Commands` — is judged non-concrete because of one, and MUST state that the token may be fenced in inline code when it is literal text rather than an unfilled slot. Keel MUST keep the unqualified diagnostic only when the field is empty or explicitly `none`/`pending`, where there is no token to name.

This is the same rule already required of a non-concrete `M<n>` check, and the diagnostics MUST NOT be phrased as two different events.

Naming the token MUST NOT change the verdict or the reported diagnostic code. A field carrying an unfilled token is not concrete both before and after; only the explanation changes.

#### Scenario: An unfilled slot in a required field is named
- **WHEN** a required task field carries an unfilled-slot token outside inline code
- **THEN** the diagnostic names the matched token
- **AND THEN** the diagnostic states that the token may be fenced in inline code when it is literal text
- **AND THEN** the field is still reported as not concrete

#### Scenario: An empty required field keeps the unqualified diagnostic
- **WHEN** a required task field is empty or explicitly `none` or `pending`
- **THEN** the diagnostic states that the field must be concrete without naming a token

#### Scenario: A prose token is reported rather than tolerated
- **WHEN** a required field carries an unfilled-token form inside ordinary prose, such as a numeric range written with bare angle brackets
- **THEN** the field is judged non-concrete and the matched span is named
- **AND THEN** the accepted repair is to reword or to fence the text, not a widened token pattern
