## 1. Freeze the synthetic comparison

- [x] 1.1 Record reusable prompts, behavior checks and blinded scoring protocol
  - Covers:
    - D1
    - D2
    - D3
  - Touch:
    - openspec/changes/freeze-defensive-review-pilot/evidence/pilot.py
    - openspec/changes/freeze-defensive-review-pilot/evidence/protocol.md
  - Verify:
    - Strategy: evidence-first
    - Reason: This slice freezes experimental inputs and calibrates their oracles using known outputs before any model request.
    - M1: Replay the Python calibration for all four workloads. Each positive passes and each designated negative control fails its specific behavior check.
    - M2: Verify 16 unique condition cells and opaque run IDs, stable ordering and instructions, and that reviewer inputs omit assigned models and instruction variants.
  - Evidence:
    - Contract: keel-task-capsule/v1 sha256:e2c57a5e347b20a2b5ca3dde6bc2506a442030f532df0ba31f0fe758bba64d83 (keel 5.231.9)
    - M1: All four positive controls passed. Their four faulty controls failed the prespecified assertions preserve-order, reject-invalid-limit, ambiguous-replay and concealed-read-error.
    - M2: pilot.py calibrate verified 16 distinct cells and unique run IDs, paired prompt equality apart from the tested guidance, and reviewer field exclusion. Controller JSON SHA-256 was 08d0d8aca041853f37c49f3dfe01e20bb246c976afb677b2a1fd28319232cf97 and the ID-sorted reviewer sheet a3f26fae3424ddfa7bd4dd4b28bb5ee1bd5f8323665ecfdbef797c9aba22c67f.
    - Review:
      - Status: pass
      - Acceptance check: Each named fault triggers its own assertion. The fixed controller view and reviewer view can be regenerated without inference.
      - Scope check: Only this change and its two evidence files. No product or model runtime configuration changed.
      - Findings: Durable owner: https://github.com/TanglmChris/keel/issues/533 for budget approval, live samples and independent blind scoring.
    - Blocker: none
    - Reauthorizations: none

## Invalidates

- None.

## Expectation Coverage

- E1: Reproducible inputs and blinded review before model sampling (D1, D2). Covered by: 1.1
- E2: Authorized model sampling and conclusions (D3). Durable owner: https://github.com/TanglmChris/keel/issues/533
