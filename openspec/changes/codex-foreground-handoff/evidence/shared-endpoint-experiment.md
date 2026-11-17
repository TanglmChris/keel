# Native shared-endpoint candidate — owner review before App restart

## Measured boundary

Linux App package 26.1023.51421 contains a native websocket URL override,
`CODEX_APP_SERVER_WS_URL`. Its transport accepts `ws+unix:` URLs; using a
localhost hostname avoids the App's nonlocal SOCKS routing. The socket path
and request path are separated by the colon in the URL pathname.
`native-app-routing.json` identifies the exact bundled modules by SHA-256 and
records the routing conditions. This is a build-specific implementation fact,
not a documented stable public setting or a completed App acceptance test.

The local-daemon flag is NOT sufficient evidence by itself: it requires empty
startup config overrides, while this App's normal local transport supplies a
plugin override. The URL route is selected earlier and does not depend on
that empty-overrides branch. FORCE_CLI must not be enabled.

The App's own native CLI read-only daemon/version probe returned the existing
running 0.167.2 daemon. Native app-server proxy successfully passed HTTP
Upgrade, initialize and read-only owned thread/read to that same socket;
proxy-websocket.json records this. The earlier JSONL-only probe timed out
because proxy forwards raw bytes rather than translating JSONL to WebSocket.
No service was started or restarted for either probe.

Current App parent process 914946 and stdio child 915503 had none of the four
checked transport variables set. Normal desktop launcher is `chatgpt %U`.
Available projects report only local hosts; no configured SSH project was
shown. Official remote-connections documentation establishes an SSH setup
route, but not that such a route is already configured here.

## Concrete proposed experiment — NOT EXECUTED

1. Owner/coordinator schedules an idle window for ALL local App chats, not
   only #541/Kaiwu. Preserve current work and wait for active tools/turns to
   finish. No forced interruption or process killing.
2. Quit the existing App normally. This affects this maintenance chat and
   all other local chats; therefore it must not be done without approval.
3. In a separate terminal, start the App once with a process-local override:

   ```sh
   env CODEX_APP_SERVER_WS_URL='ws+unix://localhost/home/tlm/.codex/app-server-control/app-server-control.sock:/rpc' chatgpt
   ```

   Do not set FORCE_CLI or CLI_PATH, change the default desktop launcher,
   install packages, change SSH, restart/bootstrap a daemon, or expose TCP.
   The URL reaches the existing Unix socket using its existing OS permission
   boundary; it does not create a second writer host or a second dispatcher.
4. Before touching production identities, verify App backend identity and use
   only the existing owned fixtures. Confirm real App input and background
   requests see one execution instance, and that two-direction busy queueing,
   reviewer/cwd and claims behave correctly. Failure preserves all records.
5. App exit must leave the already-running daemon able to execute an owned
   fixture operation; App return must reconnect to that same daemon and
   original fixture id. Native persistent daemon management and system restart
   acceptance remain separate later checks; this experiment proves neither.

## Rollback

Quit the experimental App normally after its turns/tools finish, then launch
`chatgpt` from the normal launcher without this environment override. No
configuration file is changed, so removing the per-process variable restores
the original startup route. Do not delete threads, histories, worktrees or
delivery claims. Do not restart unrelated daemons. A rollback does not permit
two endpoints to execute an active thread simultaneously.

## Authorization still needed

The current diagnosis authorizes read-only probes, not changing the App
connection or restarting all local chats. The owner must approve the specific
idle-window experiment above. If the owner declines, retain this evidence and
report the unverified actual-App startup boundary; do not call it an upstream
impossibility and do not substitute App-only execution.

Sources: https://learn.chatgpt.com/docs/remote-connections and
https://learn.chatgpt.com/docs/developer-commands for public transport/SSH
context; the installed native App routing and proxy measurements for the
build-specific candidate. No user configuration or package bytes were changed.
