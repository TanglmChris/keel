# Review result

The uncapped requirement permits any finite downstream stall and expects the accepted datum to remain visible until consumed. The original fixture exercised exactly two stalled clocks. Starting from the public output hold rule, the independent oracle expected datum 7 to remain visible through cycle 4 when the destination next becomes ready. The defective queue dropped it on the previous clock, so the cycle 4 transfer never occurs.

The capped requirement permits no more than two stalled clocks. That same trace is excluded by the explicit premise. The pilot's correct implementation also passes clocks 0 through 16, providing a positive check that the oracle accepts a working fixture. The finite probe gives an executed counterexample to one claim. It does not prove correctness for all possible streams or establish a benefit across all reviews.

Replay with `python3 evidence/pilot.py` from this change directory. The captured output reports timed oracle and fixture execution (0.109 ms). The pilot did not use independently timed human reviewers.

Existing Verify, Evidence and Review express the distinction without a gate change. Current Review already asks whether behavior evidence proves the claimed Acceptance. This pilot makes the missing premise explicit in review evidence. A later protocol change would require stronger evidence that the current rule or its adoption systematically misses this case.
