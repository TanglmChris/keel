#!/usr/bin/env python3
"""Replay #558's bounded test and independently derived public trace."""
from dataclasses import dataclass
from time import perf_counter


@dataclass
class Queue:
    """A one-place implementation, optionally with the deliberate defect."""

    expires: bool
    payload: int | None = None
    stalls: int = 0

    def cycle(self, offered: int | None, ready: bool) -> tuple[bool, int | None]:
        accepts = self.payload is None
        visible = self.payload
        if accepts:
            self.payload = offered
        elif ready:
            self.payload = None
        elif self.expires:
            self.stalls += 1
            if self.stalls == 3:
                self.payload = None
        return accepts, visible


def trace(expires: bool, stalls: int) -> list[tuple[bool, int | None]]:
    queue = Queue(expires)
    return [queue.cycle(7, True)] + [
        queue.cycle(None, ready) for ready in [False] * stalls + [True]
    ]


def expected(stalls: int) -> list[int | None]:
    # Acceptance: once accepted, the same datum must remain visible until
    # the destination accepts it, even while the destination is stalled.
    return [None] + [7] * (stalls + 1)


def first_difference(observed, stalls):
    return next(
        ((cycle, want, got) for cycle, (want, (_, got)) in enumerate(
            zip(expected(stalls), observed, strict=True)) if want != got),
        None,
    )


def main():
    start = perf_counter()
    assert first_difference(trace(True, 2), 2) is None
    print("Baseline: defective queue passes when stalled for two clocks.")
    assert all(first_difference(trace(True, stalls), stalls) is None for stalls in range(3))

    stalls = 3
    mismatch = first_difference(trace(True, stalls), stalls)
    assert mismatch == (4, 7, None)
    print("Unlimited finite stalls: cycle 4 first differs, expected 7; got no valid data.")
    limit = 2
    assert stalls > limit
    print("Explicit two-clock maximum: same three-clock stimulus is outside acceptance.")
    assert all(first_difference(trace(False, stalls), stalls) is None for stalls in range(17))
    print("Positive control: correct fixture passed all tested stall lengths 0–16.")
    print(f"Replay elapsed: {(perf_counter() - start) * 1000:.3f} ms.")


if __name__ == "__main__":
    main()
