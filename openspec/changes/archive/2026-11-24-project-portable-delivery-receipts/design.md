## Decisions

- D1 — Add a sibling `delivery` member with a `state` to todo responses from `keel chat show <id> --json`. Translate a matching durable acknowledgement to `acknowledged` and an ambiguous claim to `unknown`. Missing observation is `unobserved` for all hosts. The read asks no native host and exposes no host-specific IDs.
- D2 — Reuse the managed Codex receipt classification. Invalid registry content or an inconsistent claim that prevents classifying the outcome yields `unknown`. Preserve the original `task`, `record`, readers and other record responses. The evidence remains local and cannot schedule or authorize recovery.
