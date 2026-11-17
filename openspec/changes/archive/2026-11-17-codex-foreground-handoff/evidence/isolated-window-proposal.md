# One isolated native App window: proposed authorization delta

This proposal is not executed. Existing all-idle original-App restart permission
does not authorize the additional concurrent App instance described here.

Purpose: test a real App frontend against the existing native persistent backend
without interrupting current App/IECC work. This could validate the supported
team-window route before any production migration. It does not silently change
the original App connection, adopt production threads or close issue #541.

Installed App 26.1023.51421 bootstrap-BLyztc2V.js SHA256
8f8a874100677b81b6b1e0bfd87501aefea7ee5693ac778e90744720a1df0181:
the source reads CODEX_ELECTRON_USER_DATA_PATH in sP, sets Electron userData
before requestSingleInstanceLock (offsets 581783, 619596, 620008).
This proves the installed path selection and ordering, not actual parallel-launch
or isolated frontend acceptance. Main native URL transport was separately probed.

Exact added scope requested:

1. Launch exactly one additional installed /usr/lib/chatgpt/ChatGPT process in
   a new /tmp/keel541-isolated-* directory with private userData and private
   child-process Codex home. Set only that process's native
   CODEX_APP_SERVER_WS_URL to
   ws+unix://localhost/home/tlm/.codex/app-server-control/app-server-control.sock:/rpc.
   Its profile/home directories are new and contain no copied authentication,
   config, Goal, production registration or history databases.
2. Use only freshly created, explicitly owned private fixture thread ids in the
   existing backend for real frontend input, busy serial behavior and identity /
   reviewer/cwd/claim checks. No production thread resume or registry migration.
3. If real UI automation needs a diagnostic browser endpoint, it must be scoped
   to this isolated process only, bound to 127.0.0.1 with an ephemeral port and
   this private profile. No endpoint on the original App, no global setting or
   app-byte patch, no remote/network exposure. Read actual UI and operate only
   fixture input and the isolated window's normal Quit.
4. Snapshot original App/backend identities and relevant production registry /
   configuration hashes. Verify the isolated process identity, profile and
   backend connection before sending any fixture input. If original-instance
   redirection, unexpected stdio backend, authentication setup, unsupported UI
   or required production/config change appears, record the result and stop.
   Do not copy credentials or start/restart a daemon to make it pass.
5. After fixture turns/tools finish, normally quit only the identified isolated
   App. Verify the same backend continues a private fixture while it is closed;
   optionally reopen that same private profile once to verify original fixture
   history/policy/claims. At most one isolated App may run at a time, no watcher
   or permanent service is installed. Budget is one bounded 30-minute experiment,
   maximum two isolated launches (initial + one persistence reopen).
6. If normal Quit cannot be verified or needs interruption, preserve evidence
   and report the isolated process as recovery-needed; do not force-kill it.
   Keep the original App/backend, active tools, IECC rounds and Goals untouched.
   Dispose of disposable directories only after normal shutdown and evidence
   preservation; no global/profile reset or restoration writes are authorized.

Primary risks: an extra window can steal focus; concurrent App support is only
source-indicated until measured; the existing backend and account are shared,
so test thread creation/model calls remain real and must stay inside the stated
fixtures. Shared transport is a candidate, not proof of safe production recovery.

If approved, first author a concrete execution capsule, record its fingerprint,
then execute the bounded experiment. If rejected, continue independent CLI work
and retain the original natural-idle route. No repeated old 20-minute window.

Owner of this decision: human project owner in this chat.
Durable issue: https://github.com/TanglmChris/keel/issues/541 .

Subsequent owner decision D13 explicitly authorizes only the measured private-project trust entry and its exact cleanup, plus the final second reopen/normal-close deadline. All other limits remain. See design.md and isolated-config-delta.json.
