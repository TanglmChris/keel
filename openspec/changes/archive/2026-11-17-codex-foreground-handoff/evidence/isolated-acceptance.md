# Real shared App/native acceptance

Task 2.5, owner approvals D12 and D13. Original failed global idle window remains
historically negative. This successful experiment used a separate private App
profile and the existing native backend, avoiding interruption of existing chats.
It is not a production deployment or an original App configuration change.

Installed Linux App 26.1023.51421 connected through the build-specific process
WebSocket URL to native 0.167.2. Private fixture original id:
`01a1e9ad-eaaf-71f1-9052-6d7e331d10ba`. Two isolated launches, both normally
closed. No daemon restart, force kill, original-App restart, Goal change or
production registration write. Loopback diagnostic ports 41169/34053 are closed.

## Behavior actually proved

- Actual rendered frontend input started native turn
  01a1e9b9-dc14-7f92-ba0e-b0249ff9ce08; the same backend saw active and the public
  CLI returned waiting. After its sleep completed, addressed backend delivery
  executed on the same id. Initial keyboard Enter only inserted newlines; the
  visible Send button made the actual submission at 13:37:12.172 UTC.
- When background work is active, this App's normal action is native **Guide**
  (`引导`), not a new independent turn. It can update the current request; it
  must not be represented as a guaranteed separate queued turn. A preliminary
  early Guide arrived before its tool started and changed the response, so that
  alone was not proof of preserving an in-flight tool.
- The final in-flight test subscribed on the same actual backend and received
  item/started for a real sleep before actual rendered Guide input. That single
  command completed normally, exit 0, duration 14965ms; there was no replacement
  tool or concurrent writer. The same turn retained both user messages and
  returned INFLIGHT_NATIVE_SERIAL_DONE after completion. Authoritative evidence:
  `inflight-notification-serial.json` and `inflight-native-serial-result.txt`.
- Native thread/read history was insufficient to observe the in-progress item.
  The failed history-only probe is retained in
  `inflight-history-probe-negative.txt`; terminal safety used actual notifications,
  not foreign notLoaded/null or historical completion.
- First isolated App normally quit at 13:45:16 UTC. With it absent and backend
  pid/start unchanged, public CLI delivered app-closed-proof and native execution
  completed NATIVE_BACKEND_WITH_APP_CLOSED. See `isolated-closed-proof.json`.
- Second launch reopened the original fixture through the actual sidebar. Its
  rendered UI showed the closed-App reply and in-flight test reply; original
  history ids were all retained. Older virtualized content need not be currently
  mounted in the DOM. Public duplicate delivery returned already-delivered with
  the same original claim/turn, no extra work. See `isolated-reopen-ui.json` and
  `isolated-reopen-policy.json`.
- Native cold read/resume without policy overrides retained original id/cwd,
  auto_review/on-request/workspaceWrite, networkAccess false. Actual original
  backend rollout contexts also retained auto_review and original cwd, recorded
  in `isolated-policy-contexts.json`. App added its normal private visualization
  writable root; workspace-write permissions were not replaced by full access.

## Global configuration incident and exact recovery

Native project opening added only the unique private fixture project's trust
section to the backend config, even with private frontend Codex home. The App
was normally closed and the experiment paused when the hash difference was found.
In-memory removal matched the exact original hash. The owner explicitly approved
D13's temporary sole test entry, final reopen and precise cleanup; no inference
or automatic rollback authorization was used.

After final normal close, removing exactly that section restored SHA256
21c3179b626798cf33fd2b73c1a517198eb72ea45de1404468625bc56009366d.
All three production registry hashes and original App/backend identities match.
No other config bytes were changed by cleanup. See `isolated-config-delta.json`
and `isolated-final-state.json`. The native backend owns config/trust; a private
frontend profile does not make backend trust changes private. The runbook must
make this explicit instead of promising an entirely isolated backend account.

The private-home App's optional Local Work executor reported missing authentication;
the tested native Codex shared transport and tools worked without copying secrets.
Discard reason: enabling unrelated ChatGPT Local Work in that disposable profile
is outside this Codex role feature. No login or credential copying was attempted.

## Publication boundaries

The unmodified original default App still uses its original stdio runtime. This
test proves a real native shared-window route and a safe bounded validation;
it does not prove an atomic global Quit fence exists. Production operators must
choose their authorized connection/profile and let each original owned writer
finish/release before same-id recovery. Native writer refusal remains a stop.

Thread-level reviewer and explicit same-id cwd recovery are product CLI changes;
dedicated-window connection is an opt-in native host configuration, never an
automatic global switch. Cross-version/macOS/native Goal admission transactions
were not verified here. Existing Goals/tools in the original App were untouched.
Kaiwu production acceptance remains chief/flow's separate #546 responsibility.

`isolated-shared-real.json` is marked as a preliminary probe; its initial four-turn
predicate was not sufficient for reverse UI acceptance. Final acceptance relies
on the explicit native in-flight, closed-App, real reopened UI and policy/claim
assertions above. No preliminary script success is promoted as full proof.
