## Why

`Durable owner:` exists to say that someone is still responsible after this task ends, and the gate backs it with an existence check. For the most natural landing place — the change's own `design.md` — that check is true when it runs and false forever after, because archiving moves the directory. Nothing in `task-complete`, `change-close`, or the archive step says so.

Measured across this repository's 35 archived changes (2026-09-05, 5.42.0): 10 declarations name a path inside a live change directory — 8 `Durable owner:` and 2 `Resolved here:` — and **all 10 are dead**, because every one of them points at the change that wrote it. Zero point at a different change. The field report (issue #100, from `chip_sec_flow_v2`) measured the same shape independently: 36 such pointers, 35 dead, and the one survivor was the change still in flight. This is not an occasional slip; it is what archiving does.

A pointer that must break is worse than none, because the Review reads as closed while the trail ends halfway. The gate's own standard already covers this case in words — `keel/HANDOFF.md` is refused although it exists, because "existence is necessary, not sufficient" — and a self-pointer is the same fact arriving one step later.

The issue's second half is that a tracker reference is accepted on shape alone and never fetched. That stays true and is deliberate: a gate that reached the network would stop being local, offline, and deterministic, which is the property its verdict rests on. What it should not do is let the author believe otherwise.

## What Changes

- A `Durable owner:` or `Resolved here:` naming a path inside the change's **own** directory is refused. The refusal says the directory moves when the change is archived, so the pointer is guaranteed to break, and names what to write instead.
- The refusal applies wherever a durable owner closes an entry — Review `Findings`, `## Expectation Coverage`, `## Invalidates` — because they share one verdict function and a form refused in one must be refused in all.
- A path inside a **different** live change directory is unchanged and still accepted. The protocol names a new OpenSpec change as a legitimate follow-up owner, no measured pointer of that shape exists, and refusing it would refuse a form the protocol endorses.
- The accepted-forms text — one constant all three refusals quote — says what each form is worth: a path is checked for existence at the moment it is cited and not re-checked afterwards, and a tracker reference is accepted on shape alone because gates run offline and never fetch it. This is the same slice as the refusal above, not a second one: the refusal has to name what to write instead, so it quotes that sentence.

## Capabilities

### Modified Capabilities
- `keel-expectation-slice-evidence-gates`: the "A durable owner may be any file the repository keeps, and a refusal names what it accepts" requirement states that existence is necessary and not sufficient, and names one exception. It gains the second: a path the change is about to move is not durable, and the requirement states what the existence check is and is not worth.

## Impact

- Affected code: `src/core/gates.js` — `durableOwnerVerdict()`, `resolutionEvidenceVerdict()`, `DURABLE_OWNER_FORMS`, and the callers that pass a change name.
- Affected tests: `scripts/validate_plugin.py` — a new scenario for the self-pointer refusal across all three consumers, and for the cross-change path staying accepted.
- Direction is **stricter**: a declaration that passed now fails, in the one shape that was guaranteed to become false. No existing declaration in this repository is affected, because every change carrying one is archived and the gates refuse an archived change rather than recompiling it.
- No new dependency, no schema change, no network access added.
