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
  "keel chat notice   (what is unread and addressed to you, for any host; always exits 0)",
  "keel chat hook session-start|user-prompt-submit|file-changed|session-end   (Claude Code hook; JSON on stdin)",
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
};
const REPEATED = { "--member": "members" };
const SWITCHES = { "--json": "json", "--peek": "peek", "--all": "all", "--mine": "mine", "--follow": "follow" };

function parseChatArgs(argv) {
  const options = { positionals: [], members: [], json: false, peek: false, all: false, mine: false, follow: false };
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
function follow(where, role, group, initial, options) {
  let last = initial.length ? initial[initial.length - 1].id : "";
  const timer = setInterval(() => {
    const records = store.readLog(where, group);
    const fresh = displayRecords(records).filter((record) => record.id > last);
    if (!fresh.length) return;
    for (const record of fresh) out(options.json ? JSON.stringify(publicRecord(record)) : formatLine(record));
    last = records[records.length - 1].id;
    if (!options.peek && role) store.advanceCursor(where, role, group, last);
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

function runChat(argv) {
  try {
    const options = parseChatArgs(argv);
    const cwd = path.resolve(options.repo || process.cwd());
    if (!options.positionals.length || options.positionals[0] === "help") {
      out(`Usage:\n  ${USAGE.join("\n  ")}`);
      return 0;
    }
    if (options.positionals[0] === "hook") {
      const result = notice.hook(options.positionals[1], readStdin());
      if (result.stdout) process.stdout.write(result.stdout);
      if (result.stderr) process.stderr.write(result.stderr);
      return result.code;
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
