## Decisions

- D1 — Test only a synthetic one-item ready/valid fixture. The narrow baseline allows two cycles of downstream backpressure. Derive the independent oracle from the public handshakes, and exercise three stalled clocks and final drain.
- D2 — Evaluate the same trace against a second requirement that allows at most two stalled clocks. Reject it as out of scope for that requirement. Record the observed coverage gap, rerun command, and elapsed probe time. Existing Review remains the point for judging legitimate input and evidentiary strength.
