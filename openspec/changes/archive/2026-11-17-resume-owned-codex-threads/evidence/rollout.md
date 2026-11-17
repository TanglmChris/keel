# 5.229.1 published rollout

- PR #532 passed exact-head Full gates and repository automation merged it as 6a14ae1f80932a41d13b7e3e6fbe53814cfc5f39.
- Local npm test: baseline and 426 scenarios pass (278 deterministic, 148 stand-in); real model evidence is separately recorded in real-second-round.json.
- Published release: https://github.com/TanglmChris/keel/releases/tag/v5.229.1 (2026-11-17). Exact npm version resolves to 5.229.1.
- Authorized update: keel --update --source @christang/keel@5.229.1 completed. CLI, enabled Claude plugin and enabled Codex plugin all report 5.229.1. Existing sessions may retain loaded skills until reload/new session.
- Installed codex-host.js bytes equal the real-host-tested source. Installed default-host status succeeds against Codex Desktop/0.167.2. No unrelated sessions were interrupted.
- Installed Zod is 4.6.7; installed-prefix npm audit reports zero vulnerabilities.
- Follow-up: installed OpenSpec is 1.17.0 although the shipped shrinkwrap locks 1.14.0. Global strict spec validation reports 10 pass / 27 fail due to pre-existing length warnings; repository-locked OpenSpec strict validation passes all 37. Durable owner: https://github.com/TanglmChris/keel/issues/534 . No speculative workaround applied.
- Existing kaiwu-ip chat notified as authorized, with release, actual two-round evidence and ownership/deadline limits. Downstream isolated systemd validation and production activation remain owned by kaiwu #546. No kaiwu files or roles were modified here.
- Semantic review: pass for the published recovery and Zod repair; native hook trust boundaries remain as documented. #527 remains deferred.
