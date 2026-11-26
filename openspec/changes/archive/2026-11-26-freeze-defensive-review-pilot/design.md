## Decisions

- D1 — Freeze the public inputs, guidance contrast, randomized assignment and blind scoring criteria. One response in each of four tasks by two named models and two instruction conditions gives 16 observations. A randomized order allows operational drift to affect different cells.
- D2 — Before inference, check each test oracle against a known-correct implementation and a plausible faulty implementation. These controls demonstrate test sensitivity to a named regression. A separate reviewer must judge unnecessary behavior in otherwise correct answers.
- D3 — Record only evidence artifacts. Keep the model pilot, its budget approval and any adopted product instructions with #533.
