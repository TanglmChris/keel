# Hardware lens

Applies when: the change touches Verilog/SystemVerilog interfaces, protocol, reset, clocking/CDC, valid-ready/backpressure, arbitration, CSR/register fields, or RTL verification — for example when Touch includes `.v`/`.sv`/`.vh`/`.svh` or the change artifacts describe a module interface, protocol, or testbench.

Domain lens for Verilog/SystemVerilog work. Use during alignment, execution, and review when hardware protocol, timing, reset, or verification assumptions may be implicit.

## Material risk surface

Treat these as deep-path candidates when the change touches them: signals, module interfaces, reset, valid-ready, backpressure, ordering, arbitration, CSR or protocol fields, CDC, reset crossing, timing assumptions, security/permission paths, random behavior, keys, authentication, and testbench/formal expectations. Ask only questions that materially affect Acceptance, verification checks, Touch, specs, design decisions, or non-goals; stop when the task contract can be written without guessing.

## Durable placement

- specs for observable protocol behavior, ordering guarantees, register/CSR behavior, and error cases.
- design.md for timing assumptions, reset/CDC rationale, arbitration choices, verification strategy, and trade-offs.
- tasks.md for Covers, verification, Touch, and stop/autonomy details.

## Evidence expectations

Prefer behavior evidence appropriate to the layer: simulation or testbench evidence for interface, reset, valid-ready, backpressure, ordering, and protocol behavior; lint or static checks for structural safety when they are part of Acceptance; formal or assertion evidence for invariants tests cannot exhaustively cover; golden traces or waveform references only when stable and tied to Acceptance.

## Execution and review checks

While implementing and reviewing, prove behavior at the interface: drive reset entry and exit, valid-ready handshakes including stall and backpressure, and ordering through simulation before trusting lint; a protocol or CSR field change needs testbench evidence for both legal and illegal accesses. Watch for silent X-propagation, unregistered CDC crossings, and new reset-domain assumptions introduced by the change. In review, reject waveform screenshots without a repeatable run command, require assertion or formal evidence for invariants simulation cannot exhaustively cover, and confirm any golden trace update carries an explicit rationale tied to Acceptance.
