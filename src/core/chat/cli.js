"use strict";

// `keel chat` (issue #187): the host-neutral command line every session and
// the owner use. Any agent that can run a shell command can take part; no
// host integration is needed to post or read.

const fs = require("fs");
const path = require("path");
const store = require("./store");
const { displayRecords, formatLine, parseSince, since } = require("./view");
const { migrateIfNeeded } = require("./migrate");
const notice = require("./notice");
const { relativeAge } = require("./view");

const { ChatError } = store;

const USAGE = [
  "keel chat role [--set <name>] [--alias <alias>] [--json]",
  "keel chat group create <group> [--member <role>]...",
  "keel chat group add|remove <group> <role>",
  "keel chat group archive <group>",
  "keel chat group list [--all] [--json]   (also: keel chat list)",
  "keel chat post <group> <text...> [--reply-to <id>] [--json]   (also: keel chat <group> <text...>)",
  "keel chat dm <role> <text...> [--json]",
  "keel chat <group> [--since <90s|15m|2h|3d|date>] [--follow] [--peek] [--json]   (view; advances your read position unless --peek)",
  "keel chat unread [--json]",
  "keel chat read [<group>] [--json]",
  "keel chat show <id> [--json]",
  "keel chat todo <group> --assignee <role> [--issue <n>] <text...> [--json]",
  "keel chat todos [<group>] [--mine] [--json]",
  "keel chat done <id>",
  "keel chat edit <id> <text...>",
  "keel chat retract <id>",
  "keel chat search <text...> [--group <group>] [--json]",
  "keel chat archive sync|pull [--json]   (keep the chat on this repository's orphan keel-chat branch)",
  "keel chat bridge add|remove [--repo <path>]   (list or unlist this project for this machine's Slack bridge)",
  "keel chat bridge run [--once]   (the bridge process; --once sends what is pending and exits; Node 22+)",
  "keel chat bridge install|uninstall|start|stop   (the macOS login item that keeps the bridge running)",
  "keel chat bridge pause <30m|2h|1d> | resume",
  "keel chat bridge status [--json]",
  "keel chat notice   (what is unread and addressed to you, for any host; always exits 0)",
  "keel chat notice --check   (for schedulers: no output; exit 0 only when something addressed to you is unread, else 1)",
  "keel chat hook session-start|user-prompt-submit|file-changed|session-end   (Claude Code hook; JSON on stdin)",
  "keel chat wake add [--host codex] [--thread <id>] [--max-per-hour <n>] [--compact-at <tokens>]   (this machine starts a Codex turn when something addressed to this worktree's role arrives)",
  "keel chat wake remove   (stop waking this worktree's role on this machine)",
  "keel chat wake status [--json]",
  "keel chat wake run --once [--worktree <path>]   (what the waker's LaunchAgent runs)",
  "Every command takes --repo <path> to act on another repository.",
];

const VALUED = {
  "--set": "set",
  "--alias": "alias",
  "--reply-to": "replyTo",
  "--repo": "repo",
  "--assignee": "assignee",
  "--issue": "issue",
  "--group": "group",
  "--since": "since",
  "--worktree": "worktree",
  "--thread": "thread",
  "--host": "host",
  "--max-per-hour": "maxPerHour",
  "--compact-at": "compactAt",
};
const REPEATED = { "--member": "members" };
const SWITCHES = { "--json": "json", "--peek": "peek", "--all": "all", "--mine": "mine", "--follow": "follow", "--once": "once", "--mail": "mail", "--check": "check" };

function parseChatArgs(argv) {
  const options = { positionals: [], members: [], json: false, peek: false, all: false, mine: false, follow: false, once: false, mail: false, check: false };
  for (const key of Object.values(VALUED)) options[key] = null;
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--") {
      options.positionals.push(...argv.slice(index + 1));
      break;
    }
    if (arg in SWITCHES) {
      options[SWITCHES[arg]] = true;
      continue;
    }
    const eq = arg.indexOf("=");
    const flag = arg.startsWith("--") && eq > 0 ? arg.slice(0, eq) : arg;
    if (flag in VALUED || flag in REPEATED) {
      let value;
      if (flag !== arg) {
        value = arg.slice(eq + 1);
      } else {
        index += 1;
        if (index >= argv.length) throw new ChatError(`${arg} requires a value.`);
        value = argv[index];
      }
      if (flag in REPEATED) {
        options[REPEATED[flag]].push(value);
        continue;
      }
      const key = VALUED[flag];
      if (options[key] !== null) throw new ChatError(`${flag} was provided more than once.`);
      options[key] = value;
      continue;
    }
    if (arg.startsWith("--")) throw new ChatError(`Unknown option for keel chat: ${arg}`);
    options.positionals.push(arg);
  }
  return options;
}

function out(text) {
  process.stdout.write(text.endsWith("\n") ? text : `${text}\n`);
}

function readStdin() {
  if (process.stdin.isTTY) return "";
  try {
    return fs.readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

function publicRecord(record) {
  const { refs, ...rest } = record;
  return refs && refs.length ? record : rest;
}

// A mentioned member that is offline gets the record when it next starts;
// nothing launches it (D10), so the poster is told.
function offlineMentions(where, record) {
  return (record.mentions || [])
    .filter((role) => role !== store.ALL && !role.includes("/") && role !== record.from)
    .filter((role) => notice.presenceOf(where, role).state === "offline");
}

function postResult(where, record, json) {
  const offline = offlineMentions(where, record);
  if (json) {
    out(JSON.stringify({ id: record.id, group: record.group, from: record.from, mentions: record.mentions, offline }));
    return;
  }
  const lines = [`Posted ${record.id} to ${record.group}.`];
  for (const role of offline) lines.push(`Queued for ${role}: offline; it will see this when its session next starts.`);
  out(lines.join("\n"));
}

function textFrom(words) {
  const text = words.join(" ");
  return text.trim() ? text : readStdin();
}

function runGroup(where, options) {
  const [action, group, member] = options.positionals.slice(1);
  if (action === "list" || action === undefined) {
    const groups = store.listGroups(where, { includeArchived: options.all });
    if (options.json) out(JSON.stringify({ groups }));
    else if (!groups.length) out("No groups. Create one with `keel chat group create <group>`.");
    else out(groups.map((g) => `${g.name}${g.archived ? " (archived)" : ""}: ${g.members.join(", ")}`).join("\n"));
    return 0;
  }
  const actor = store.requireRole(where);
  if (!group) throw new ChatError(`keel chat group ${action} needs a group name.`);
  switch (action) {
    case "create": {
      const members = store.createGroup(where, actor, group, options.members);
      out(options.json ? JSON.stringify({ group, members }) : `Created ${group}: ${members.join(", ")}.`);
      return 0;
    }
    case "add":
    case "remove": {
      if (!member) throw new ChatError(`keel chat group ${action} needs a role.`);
      store.changeMember(where, actor, group, member, action === "add" ? "join" : "leave");
      out(`${action === "add" ? "Added" : "Removed"} ${member} ${action === "add" ? "to" : "from"} ${group}.`);
      return 0;
    }
    case "archive":
      store.archiveGroup(where, actor, group);
      out(`Archived ${group}. Its history stays readable.`);
      return 0;
    default:
      throw new ChatError(`Unknown keel chat group action ${JSON.stringify(action)}: use create, add, remove, archive, or list.`);
  }
}

function presenceLine(where, members) {
  const now = Date.now();
  const parts = [...members].sort().map((role) => {
    const { state, last_active: last } = notice.presenceOf(where, role, now);
    if (!last) return `${role} (offline, never seen)`;
    return state === "online" ? `${role} (online)` : `${role} (${state}, ${relativeAge(last, now)})`;
  });
  return `Members: ${parts.join(", ") || "none"}`;
}

function runView(where, group, options) {
  const role = store.currentRole(where);
  let threshold = null;
  if (options.since !== null) {
    threshold = parseSince(options.since);
    if (threshold === null) throw new ChatError(`--since ${JSON.stringify(options.since)} is not a duration (90s, 15m, 2h, 3d) or a date.`);
  }
  const { records: raw, state } = store.view(where, role, group, { peek: options.peek });
  const records = since(displayRecords(raw), threshold);
  if (options.json) {
    out(JSON.stringify({ group, members: [...state.members].sort(), records: records.map(publicRecord) }));
  } else {
    out([`# ${group}${state.archived ? " (archived)" : ""}`, presenceLine(where, state.members), ...records.map((record) => formatLine(record))].join("\n"));
  }
  if (options.follow) follow(where, role, group, raw, options);
  return 0;
}

// Keeps printing records as they arrive until interrupted. Polling the log
// directory, rather than a file watcher, behaves the same on every platform
// and over a synced folder.
// Remembers every id already accounted for rather than the last one: a
// record can arrive with an id that sorts earlier — written by a machine
// whose clock runs behind, or landing between the first read and the first
// poll — and comparing against the newest id would skip it for good (#196).
function follow(where, role, group, initial, options) {
  const known = new Set(initial.map((record) => record.id));
  const timer = setInterval(() => {
    const records = store.readLog(where, group);
    const fresh = records.filter((record) => !known.has(record.id));
    if (!fresh.length) return;
    for (const record of fresh) known.add(record.id);
    const freshIds = new Set(fresh.map((record) => record.id));
    for (const record of displayRecords(records).filter((shown) => freshIds.has(shown.id))) {
      out(options.json ? JSON.stringify(publicRecord(record)) : formatLine(record));
    }
    if (!options.peek && role) store.advanceCursor(where, role, group, records[records.length - 1].id);
  }, 500);
  const stop = () => {
    clearInterval(timer);
    process.exitCode = 0;
  };
  process.once("SIGINT", stop);
  process.once("SIGTERM", stop);
}

function dispatch(where, options) {
  const [command, ...rest] = options.positionals;
  switch (command) {
    case "role": {
      let role = store.currentRole(where);
      if (options.set !== null) role = store.setRole(where, options.set);
      if (options.alias !== null) {
        if (!role) throw new ChatError("Bind a role before adding an alias: `keel chat role --set <name>`.");
        store.addAlias(where, role, options.alias);
      }
      const aliases = role ? store.readMember(where.root, role).aliases : [];
      if (options.json) out(JSON.stringify({ role, aliases, worktree: where.worktree, store: where.root }));
      else out(role ? `Chat role: ${role}${aliases.length ? ` (aliases: ${aliases.join(", ")})` : ""}` : "This worktree has no chat role. Bind one with `keel chat role --set <name>`.");
      return 0;
    }
    case "group":
      return runGroup(where, options);
    case "list":
      return runGroup(where, { ...options, positionals: ["group", "list"] });
    case "post": {
      const [group, ...words] = rest;
      if (!group) throw new ChatError("keel chat post needs a group.");
      postResult(where, store.post(where, { group, text: textFrom(words), replyTo: options.replyTo }), options.json);
      return 0;
    }
    case "dm": {
      const [target, ...words] = rest;
      if (!target) throw new ChatError("keel chat dm needs a role.");
      postResult(where, store.directPost(where, target, textFrom(words)), options.json);
      return 0;
    }
    case "unread": {
      const role = store.requireRole(where);
      const records = store.unread(where, role);
      if (options.json) out(JSON.stringify({ role, unread: records.map(publicRecord) }));
      else out(records.length ? records.map((r) => `${r.group} ${formatLine(r)}`).join("\n") : `keel chat: nothing unread for role \`${role}\`.`);
      return 0;
    }
    case "read": {
      const role = store.requireRole(where);
      const records = store.readGroups(where, role, rest[0] || null);
      if (options.json) out(JSON.stringify({ role, notice: store.DATA_NOTICE, records: records.map(publicRecord) }));
      else if (!records.length) out(`keel chat: nothing unread for role \`${role}\`.`);
      else out([`> ${store.DATA_NOTICE}`, "", ...records.map((r) => `${r.group} ${formatLine(r)}`)].join("\n"));
      return 0;
    }
    case "show": {
      const id = rest[0];
      if (!id) throw new ChatError("keel chat show needs a record id.");
      const record = store.findRecord(where, id);
      if (!record) throw new ChatError(`No record ${id}.`);
      const readers = store.readersOf(where, record);
      if (options.json) out(JSON.stringify({ record: publicRecord(record), readers }));
      else out([`${record.group} ${formatLine(record)}`, `read by: ${readers.join(", ") || "nobody yet"}`].join("\n"));
      return 0;
    }
    case "todo": {
      const [group, ...words] = rest;
      if (!group) throw new ChatError("keel chat todo needs a group.");
      if (options.assignee === null) throw new ChatError("keel chat todo needs --assignee <role>.");
      postResult(where, store.todo(where, { group, assignee: options.assignee, issue: options.issue, text: textFrom(words), replyTo: options.replyTo }), options.json);
      return 0;
    }
    case "todos": {
      const assignee = options.mine ? store.requireRole(where) : null;
      const todos = store.openTodos(where, { group: rest[0] || null, assignee });
      if (options.json) out(JSON.stringify({ todos: todos.map(publicRecord) }));
      else out(todos.length ? todos.map((r) => `${r.group} ${formatLine(r)}`).join("\n") : "No open todos.");
      return 0;
    }
    case "done": {
      if (!rest[0]) throw new ChatError("keel chat done needs a todo id.");
      const record = store.done(where, rest[0]);
      out(options.json ? JSON.stringify({ id: record.id, target: record.target }) : `Closed todo ${record.target}.`);
      return 0;
    }
    case "edit":
    case "retract": {
      const [id, ...words] = rest;
      if (!id) throw new ChatError(`keel chat ${command} needs a record id.`);
      const record = store.amend(where, id, command, command === "edit" ? textFrom(words) : "");
      out(options.json ? JSON.stringify({ id: record.id, target: record.target }) : `${command === "edit" ? "Edited" : "Retracted"} ${id}; the original record is kept.`);
      return 0;
    }
    case "search": {
      const results = store.search(where, rest.join(" "), { group: options.group });
      if (options.json) out(JSON.stringify({ results: results.map(publicRecord) }));
      else out(results.length ? results.map((r) => `${r.group} ${formatLine(r)}`).join("\n") : "No matches.");
      return 0;
    }
    case "notice": {
      const role = store.currentRole(where);
      const text = role ? notice.noticeText(where, role) : "";
      if (options.json) out(JSON.stringify({ role, notice: text }));
      else if (text) out(text);
      return 0;
    }
    case "bridge":
      return runBridge(where, rest, options);
    case "archive": {
      const archive = require("./archive");
      if (rest[0] === "sync") {
        const result = archive.sync(where);
        if (options.json) out(JSON.stringify(result));
        else {
          const lines = [`keel chat archive: ${result.changed ? "committed" : "already up to date at"} ${result.commit ? result.commit.slice(0, 12) : "nothing"} on keel-chat${result.imported ? `; imported ${result.imported} file${result.imported === 1 ? "" : "s"} from ${result.remote}` : ""}${result.pushed ? `; pushed to ${result.remote}` : ""}.`];
          if (result.refused) lines.push(result.refused);
          if (result.conflicts.length) lines.push(`These records differ between this machine and the archive; the local copy was kept: ${result.conflicts.join(", ")}`);
          out(lines.join("\n"));
        }
        return 0;
      }
      if (rest[0] === "pull") {
        const result = archive.pull(where);
        out(options.json ? JSON.stringify(result) : `keel chat archive: restored ${result.imported} file${result.imported === 1 ? "" : "s"} from the keel-chat archive.`);
        return 0;
      }
      throw new ChatError("keel chat archive needs sync or pull.");
    }
    case "help":
    case undefined:
      out(`Usage:\n  ${USAGE.join("\n  ")}`);
      return 0;
    default: {
      // `keel chat <group>` views; `keel chat <group> <text...>` posts.
      if (rest.length) {
        postResult(where, store.post(where, { group: command, text: rest.join(" "), replyTo: options.replyTo }), options.json);
        return 0;
      }
      return runView(where, command, options);
    }
  }
}

function runBridge(where, rest, options) {
  const bridge = require("./bridge");
  const lifecycle = require("./lifecycle");
  const [action] = rest;
  if (action !== "status") bridge.requireWebSocket();
  switch (action) {
    case "add": {
      const added = bridge.addProject(where);
      out(`This machine's bridge will serve ${added} when keel/chat.json sets slack.enabled to true.`);
      return 0;
    }
    case "remove":
      out(`This machine's bridge no longer serves ${bridge.removeProject(where)}.`);
      return 0;
    case "status": {
      const status = bridge.fullStatus();
      if (options.json) {
        out(JSON.stringify(status));
        return 0;
      }
      const lines = [`keel chat bridge: ${status.installed ? "installed as a login item" : "not installed"}; ${status.running ? `running (pid ${status.pid}), ${status.connected ? "connected" : "not connected"}` : "not running"}${status.paused ? `, paused until ${status.paused_until}` : ""}.`];
      if (status.running) lines.push(`Serving ${status.projects.length} project${status.projects.length === 1 ? "" : "s"}; last event ${status.last_event || "none yet"}; ${status.unposted} waiting to send; ${status.ignored} ignored from unregistered senders.`);
      else lines.push("Slack messages are not reaching this machine's sessions; local chat still works and nothing is lost.");
      out(lines.join("\n"));
      return 0;
    }
    case "install":
      out(`Installed ${lifecycle.install()}; the bridge now starts at login and restarts if it stops. See it under System Settings > General > Login Items.`);
      return 0;
    case "uninstall":
      out(`Removed ${lifecycle.uninstall()}; the bridge no longer runs on this machine.`);
      return 0;
    case "start":
      lifecycle.start();
      out("Started the bridge.");
      return 0;
    case "stop":
      lifecycle.stop();
      out("Stopped the bridge until `keel chat bridge start` or your next login. Messages wait; nothing is lost.");
      return 0;
    case "pause": {
      const until = lifecycle.pause(rest[1]);
      out(`Paused the bridge until ${until.toISOString()}. Messages wait and are delivered afterwards. \`keel chat bridge resume\` ends it early.`);
      return 0;
    }
    case "resume":
      lifecycle.resume();
      out("Resumed the bridge.");
      return 0;
    case "run": {
      const log = (line) => process.stderr.write(`keel chat bridge: ${line}\n`);
      (options.once ? bridge.runOnce(log) : bridge.run(log)).then(
        (code) => { process.exitCode = code; },
        (error) => {
          process.stderr.write(`keel chat: ${error.message}\n`);
          process.exitCode = error instanceof ChatError ? 2 : 1;
        }
      );
      return undefined;
    }
    default:
      throw new ChatError(`Unknown keel chat bridge action ${JSON.stringify(action)}: use add, remove, install, uninstall, start, stop, pause, resume, status, or run.`);
  }
}

function runWake(cwd, options) {
  const wake = require("./wake");
  const action = options.positionals[1];
  switch (action) {
    case "add": {
      const added = wake.add(store.requireLocation(cwd), options);
      const lines = [`Registered a waker for ${added.role} in ${added.worktree}: an addressed record in a group declaring chat-reply starts one ${added.host} turn (at most ${added.max_per_hour} an hour, compacting at ${added.compact_at} tokens). LaunchAgent: ${added.plist}.`];
      if (added.groups.length) lines.push(`Groups it wakes for: ${added.groups.join(", ")}.`);
      else lines.push("This worktree declares no chat-reply:<group> in keel/config.yaml, so nothing will wake it until it does: a woken turn could not answer, because a chat message grants nothing.");
      out(lines.join("\n"));
      return 0;
    }
    case "remove": {
      const removed = wake.remove(store.requireLocation(cwd));
      out(`Removed the waker for ${removed.role} in ${removed.worktree}; nothing starts a turn for it any more. Its log stays at ${removed.log}.`);
      return 0;
    }
    case "status": {
      const registrations = wake.status();
      if (options.json) {
        out(JSON.stringify({ registrations }));
        return 0;
      }
      if (!registrations.length) {
        out("No wakers on this machine. Register one in a worktree with `keel chat wake add`.");
        return 0;
      }
      out(registrations.map((entry) => `${entry.role} in ${entry.worktree}: ${entry.installed ? "installed" : "not installed"}; thread ${entry.thread || "not started"}; last turn ${entry.last_turn || "never"}; ${entry.turns_last_hour}/${entry.max_per_hour} turns in the last hour${entry.held ? " (held)" : ""}. Log: ${entry.log}`).join("\n"));
      return 0;
    }
    case "run": {
      if (!options.once) throw new ChatError("keel chat wake run needs --once: each trigger runs once and exits.");
      const result = wake.runOnce(options.worktree || cwd);
      if (options.json) out(JSON.stringify(result));
      return 0;
    }
    default:
      throw new ChatError(`Unknown keel chat wake action ${JSON.stringify(action)}: use add, remove, status, or run.`);
  }
}

function runChat(argv) {
  try {
    const options = parseChatArgs(argv);
    const cwd = path.resolve(options.repo || process.cwd());
    if (!options.positionals.length || options.positionals[0] === "help") {
      out(`Usage:\n  ${USAGE.join("\n  ")}`);
      return 0;
    }
    if (options.positionals[0] === "hook") {
      const result = notice.hook(options.positionals[1], readStdin(), { mail: options.mail });
      if (result.stdout) process.stdout.write(result.stdout);
      if (result.stderr) process.stderr.write(result.stderr);
      return result.code;
    }
    // `notice --check` is what a scheduler runs before deciding to start a
    // model turn (#194): no output, no file written — not even presence or
    // the 5.83 migration — and 0 only when something would wake the role.
    if (options.positionals[0] === "notice" && options.check) return notice.check(cwd);
    // The waker (#203) runs from launchd outside any repository and names its
    // worktree; it is not the role's session, so it marks no presence.
    if (options.positionals[0] === "wake") return runWake(cwd, options);
    // The bridge serves every listed project on this machine, and launchd
    // starts it in `/`; only `add` and `remove` act on the current repository.
    if (options.positionals[0] === "bridge" && !["add", "remove"].includes(options.positionals[1])) {
      return runBridge(null, options.positionals.slice(1), options);
    }
    // A notice is read by hosts on every prompt: outside a repository it says
    // nothing and still exits 0.
    if (options.positionals[0] === "notice" && !store.locate(cwd)) return 0;
    const where = store.requireLocation(cwd);
    migrateIfNeeded(where);
    const role = store.currentRole(where);
    if (role) notice.touchPresence(where, role);
    return dispatch(where, options);
  } catch (error) {
    if (!(error instanceof ChatError)) throw error;
    process.stderr.write(`keel chat: ${error.message}\n`);
    return 2;
  }
}

module.exports = {
  CHAT_USAGE: USAGE,
  runChat,
};
