## Context

The letter-and-digit rule (#347 D1) was meant to keep dates such as `20261018` out of the list; it also dropped the 2% of short shas that are all digits.

## Facts

- F1 — `noteCommits` (`src/core/shift.js`) applies `looksLikeSha` to pairs and bare tokens alike.
- F2 — CI run 39211624782 drew `02607471` as the 8-digit prefix of a fixture commit and failed the scenario.

## Decisions

- D1 — A pair's sha is any 7–40 hex digits. A bare token with a letter and a digit is listed as before; a bare all-digit token is listed only when `git rev-parse --verify <token>^{commit}` resolves.
