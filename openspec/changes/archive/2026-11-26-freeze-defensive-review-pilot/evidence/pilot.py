"""Frozen public fixtures for #533. This program never contacts a model."""
import argparse
import hashlib
import itertools
import json
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    name: str
    task: str
    starter: str
    correct: str
    fault: str
    tests: str
    detects: str


CASES = [
    Case("internal",
         "Return the names of enabled rows, in input order. The caller supplies a list of validated dicts with string name and boolean enabled fields.",
         "def enabled_names(rows):",
         "    return [row['name'] for row in rows if row['enabled']]",
         "    return sorted(row['name'] for row in rows if row['enabled'])",
         """assert enabled_names([]) == []
rows = [dict(name='z', enabled=True), dict(name='unused', enabled=False), dict(name='a', enabled=True), dict(name='z', enabled=True)]
assert enabled_names(rows) == ['z', 'a', 'z'], 'preserve-order'""",
         "preserve-order"),
    Case("external",
         "Parse a JSON-decoded limit. Accept integers 1 through 100 inclusive. Invalid inputs raise ValueError. Return the accepted integer.",
         "def parse_limit(value):",
         "    if type(value) is not int or not 1 <= value <= 100:\n        raise ValueError('limit')\n    return value",
         "    if not isinstance(value, int) or not 1 <= value <= 100:\n        raise ValueError('limit')\n    return value",
         """for n in (1, 59, 100):
    assert parse_limit(n) == n
for value in (True, False, 0, 101, '2', None, 3.0, [], {}):
    try: parse_limit(value)
    except ValueError: pass
    else: raise AssertionError('reject-invalid-limit')""",
         "reject-invalid-limit"),
    Case("delivery",
         "Call submit() once. Return its receipt on success. A TimeoutError can follow a committed external effect: report None so the caller can reconcile. Propagate all other exceptions.",
         "def deliver(submit):",
         "    try: return submit()\n    except TimeoutError: return None",
         "    try: return submit()\n    except TimeoutError: return submit()",
         """receipt = object()
assert deliver(lambda: receipt) is receipt
calls = []
def uncertain():
    calls.append('committed')
    if len(calls) == 1: raise TimeoutError()
    return receipt
outcome = deliver(uncertain)
assert calls == ['committed'], 'ambiguous-replay'
assert outcome is None
error = RuntimeError('rejected')
def rejected(): raise error
try: deliver(rejected)
except RuntimeError as exc: assert exc is error
else: raise AssertionError('lost-rejection')""",
         "ambiguous-replay"),
    Case("legacy",
         "Read names with the modern reader. Only an UnsupportedFormat exception selects the supported legacy reader. Return the chosen reader's result and propagate its errors.",
         "class UnsupportedFormat(Exception):\n    pass\n\ndef read_names(modern, legacy):",
         "    try: return modern()\n    except UnsupportedFormat: return legacy()",
         "    try: return modern()\n    except Exception: return legacy()",
         """calls = []
def legacy():
    calls.append('legacy')
    return ['old']
def unsupported(): raise UnsupportedFormat()
def damaged(): raise OSError('read failure')
assert read_names(lambda: ['new'], legacy) == ['new'] and not calls
assert read_names(unsupported, legacy) == ['old'] and calls == ['legacy']
try: read_names(damaged, legacy)
except OSError: pass
else: raise AssertionError('concealed-read-error')
assert calls == ['legacy']
try: read_names(unsupported, damaged)
except OSError: pass
else: raise AssertionError('concealed-legacy-error')""",
         "concealed-read-error"),
]

BASE = "Do not expand scope, add dependencies, redesign interfaces, or change unauthorized state, protocol, timing, reset, ordering, permission, random, key, authentication, or security boundaries."
TREATMENT = "Add validation, compatibility, retries or fallbacks only for a stated requirement, boundary contract or observed failure. Keep required safeguards and let internal invariant violations surface."
MODELS = ("gpt-6.1-sol", "gpt-6.2-sol")
STYLES = ("baseline", "traceable")
FIELDS = ("acceptance", "unsupported_branches", "hidden_failures", "lost_safeguards", "lines_and_rationale")


def schedule():
    cells = list(itertools.product(CASES, MODELS, STYLES))
    rng = random.Random(53320261126)
    rng.shuffle(cells)
    rows = []
    for case, model, style in cells:
        run_id = f"R{rng.getrandbits(40):010x}"
        prompt = ("Return only the complete Python 3 module.\n" + BASE + "\n"
                  + (TREATMENT + "\n" if style == "traceable" else "")
                  + case.task + "\n\n" + case.starter + "\n    raise NotImplementedError\n")
        rows.append(dict(run_id=run_id, fixture=case.name, model=model, style=style, prompt=prompt,
                         prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest()))
    return rows


def score_sheet(rows):
    return [dict(run_id=row["run_id"], fixture=row["fixture"], **dict.fromkeys(FIELDS))
            for row in sorted(rows, key=lambda row: row["run_id"])]


def calibrate():
    for case in CASES:
        # Both sources are the fixed controls in this file.
        for label, implementation in [("positive", case.correct), ("negative", case.fault)]:
            source = case.starter + "\n" + implementation + "\n" + case.tests
            try:
                exec(compile(source, case.name, "exec"), {})
            except AssertionError as exc:
                if label != "negative" or str(exc) != case.detects:
                    raise
            else:
                assert label == "positive", case.name
        print(case.name, "positive passed; negative detected", case.detects)
    rows = schedule()
    assert len(rows) == len({r["run_id"] for r in rows}) == 16
    assert len({(r["fixture"], r["model"], r["style"]) for r in rows}) == 16
    assert rows == schedule()
    for row in score_sheet(rows):
        assert set(row) == {"run_id", "fixture", *FIELDS}
    for case, model in itertools.product(CASES, MODELS):
        pair = {r["style"]: r["prompt"] for r in rows if r["fixture"] == case.name and r["model"] == model}
        assert pair["traceable"].replace(TREATMENT + "\n", "", 1) == pair["baseline"]
    print("16 unique paired cells; reviewer sheet excludes model, variant, prompt and execution order")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("view", choices=["calibrate", "assignments", "review"])
    view = parser.parse_args().view
    if view == "calibrate":
        calibrate()
    else:
        rows = schedule()
        print(json.dumps(rows if view == "assignments" else score_sheet(rows), indent=2))
