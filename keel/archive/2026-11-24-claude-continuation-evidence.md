# Claude background continuation evidence for #544

Measured on November 24, 2026 with Claude Code 2.1.325 on Linux against the Keel 5.231.5 candidate. Each run used a fresh temporary checkout, a separate home and Claude config, and a native trust prompt for that checkout only. The native client called a local fixture with a synthetic credential. These observations cover the recorded native client and process behavior.

## Correlating a resource failure

A fixture returned a generic HTTP 429 to one background request. The native job was listed as `status: idle`, `state: blocked`. The persisted assistant error was `rate_limit`, and the transcript filename matched the listed native session ID. After `claude stop` returned 0, the original session process identity (PID and Linux start time) had no live process. A generic rate-limit receipt carries no verified account-budget exhaustion or permission to choose a fallback.

## Duplicate tool receipts and durable effects

A separate fixture allowed only one predeclared script that appended one line in the temporary checkout. The local provider requested that tool once, then returned generic 429 on the next request. The native transcript contained two successful `tool_result` entries for the same `tool_use_id` and the correlated `rate_limit` error. The file contained exactly one appended line before and after native stop. The tool result is a durable evidence reference. The repeated receipt count is not an execution count, and the filesystem is independent evidence of the actual effect.

## Stopping a tool in progress

In two separate runs, an otherwise idle fixture started a harmless counting process, once as an ordinary Bash child and once in its own session. While the job was `busy/working`, the original session and the named tool process were observed by PID and start time. Both process identities ceased to be live after native stop in both samples. This establishes cleanup for these two Linux fixtures. Other native tasks can have effects not represented by the observed processes, including already committed changes and external operations without receipts.

## Contract implications

Bind native observations to the stable Keel task, its execution attempt and the native session. Correlate duplicate tool receipts by native session and tool-use ID, and reconcile the actual resource before considering replay. Keep absent receipts, conflicting observations and unverified writer release visible as unknown. Cross-harness writer fencing and budget-aware continuation remain owned by [#544](https://github.com/TanglmChris/keel/issues/544).
