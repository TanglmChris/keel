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
  "keel chat role [--set <name>] [--alias <alias>] [--prune] [--unset] [--json]   (--prune: drop bindings to removed worktrees; --unset: drop this worktree's)",
  "keel chat role --park <role> [--reason <text>] | --unpark <role>   (a role parked on purpose is not nudged or reported by the patrol)",
  "keel chat role --rename <old> <new> [--json]   (the chat reads <old> as <new>; bindings and per-role state move to <new>)",
  "keel chat group create <group> [--member <role>]...",
  "keel chat group add|remove <group> <role> [--listen]   (--listen: receives the group, may ack and close its todos, does not post)",
  "keel chat group archive <group>",
  "keel chat group list [--all] [--json]   (also: keel chat list)",
  "keel chat post <group> <text...> [--reply-to <id>] [--supersedes <id>] [--ack] [--no-stamp] [--not-a-loop <why>] [--json]   (also: keel chat <group> <text...>; Keel stamps the time unless --no-stamp)",
  "keel chat ack <id>                       acknowledge a record that asks (a reply also counts)",
  "keel chat acks [--mine] [--json]         records still waiting on an acknowledgement",
  "keel chat summary --since <90s|15m|2h|3d|date> [--group <group>] [--json]   (what changed, per group and sender; reads without marking read)",
  "keel chat wait <group> --commit <sha> [--branch <name>] [--remote <name>] [note...]   (or --issue <n> --closed: what this role waits for; keel patrol tells it when it holds)",
  "keel chat waits [--json]                 waits not yet met",
  "keel chat dm <role> <text...> [--no-stamp] [--not-a-loop <why>] [--json]",
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
  "keel chat bot add|remove <name> | list   (the Slack bots this machine holds Keychain tokens for, as bot:<name> and app:<name>)",
  "keel chat notice   (what is unread and addressed to you, for any host; always exits 0)",
  "keel chat notice --check   (for schedulers: no output; exit 0 only when something addressed to you is unread, else 1)",
  "keel chat hook session-start|user-prompt-submit|post-tool-use|file-changed|session-end   (Claude Code hook; JSON on stdin)",
  "keel chat wake add [--host codex] [--thread <id>] [--max-per-hour <n>] [--compact-at <tokens>]   (this machine starts a Codex turn when something addressed to this worktree's role arrives)",
  "keel chat wake remove   (stop waking this worktree's role on this machine)",
  "keel chat wake status [--json]",
  "keel chat wake run --once [--worktree <path>]   (what the waker's LaunchAgent runs)",
  "keel chat wake now <role>   (resume a role whose Claude Code CLI session has ended: claude --bg --resume <its id>)",
  "Every command takes --repo <path> to act on another repository.",
];

const VALUED = {
  "--set": "set",
  "--alias": "alias",
  "--rename": "rename",
  "--park": "park",
  "--unpark": "unpark",
  "--reason": "reason",
  "--reply-to": "replyTo",
  "--supersedes": "supersedes",
  "--not-a-loop": "notALoop",
  "--repo": "repo",
  "--assignee": "assignee",
  "--issue": "issue",
  "--group": "group",
  "--since": "since",
  "--commit": "commit",
  "--remote": "remote",
  "--branch": "branch",
  "--worktree": "worktree",
  "--thread": "thread",
  "--host": "host",
  "--max-per-hour": "maxPerHour",
  "--compact-at": "compactAt",
};
const REPEATED = { "--member": "members" };
const SWITCHES = { "--json": "json", "--peek": "peek", "--all": "all", "--mine": "mine", "--follow": "follow", "--once": "once", "--mail": "mail", "--check": "check", "--ack": "ack", "--listen": "listen", "--closed": "closed", "--stamp": "stamp", "--no-stamp": "noStamp", "--help": "help", "-h": "help", "--prune": "prune", "--unset": "unset" };

function parseChatArgs(argv) {
  const options = { positionals: [], members: [], json: false, peek: false, all: false, mine: false, follow: false, once: false, mail: false, check: false, ack: false, listen: false, closed: false, stamp: false, noStamp: false, help: false, prune: false, unset: false };
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

// The time comes from Keel's clock, never the author's estimate (#298 D3).
// It is the default since replies without `--stamp` carried hand-typed times
// (#349); `--no-stamp` opts out, and a text that already opens with a stamp
// is left as it is.
const OPENING_STAMP = /^\[\d{2}-\d{2} \d{2}:\d{2}\]/;
const MARKDOWN_BLOCK = /^(?:#{1,6}\s|[-*+]\s|>|```|\d+[.)]\s|\|)/;

function stamped(text, options) {
  if (options.stamp && options.noStamp) throw new ChatError("--stamp and --no-stamp cannot both be given.");
  if (options.noStamp || !String(text || "").trim() || OPENING_STAMP.test(String(text).trimStart())) return text;
  const now = store.isoLocal(new Date());
  const stamp = `[${now.slice(5, 10)} ${now.slice(11, 16)}]`;
  // A first line that opens a Markdown block keeps its line start (#349 D3).
  return MARKDOWN_BLOCK.test(String(text).trimStart()) ? `${stamp}\n${String(text).trimStart()}` : `${stamp} ${text}`;
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

function ackLines(acks) {
  const list = (roles) => roles.join(", ") || "none";
  return [
    `acknowledged: ${list(acks.acknowledged)}`,
    `read, not acknowledged: ${list(acks.readNotAcknowledged)}`,
    `not read: ${list(acks.unread)}`,
  ];
}

function summaryLines({ groups, waitingAcks }, sinceText) {
  if (!groups.length && !waitingAcks.length) return [`keel chat: nothing changed since ${sinceText}.`];
  const first = (text) => String(text || "").split("\n")[0];
  const lines = [`Since ${sinceText}:`];
  for (const { group, senders } of groups) {
    lines.push(`${group}:`);
    for (const sender of senders) {
      lines.push(`  ${sender.role}: ${sender.messages} message${sender.messages === 1 ? "" : "s"}`);
      for (const t of sender.todosOpened) lines.push(`    todo for ${t.assignee} (${t.state}) ${t.id}: ${first(t.text)}`);
      for (const t of sender.todosClosed) lines.push(`    closed todo from ${t.from} ${t.id}: ${first(t.text)}`);
      for (const x of sender.supersedes) lines.push(`    ${x.id} superseded ${x.supersedes}: ${first(x.text)}`);
    }
  }
  if (waitingAcks.length) {
    lines.push("Waiting on an acknowledgement:");
    for (const a of waitingAcks) lines.push(`  ${a.group} ${a.id} from ${a.from}, waiting on ${a.waiting.join(", ")}: ${first(a.text)}`);
  }
  return lines;
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

// A woken role whose desktop session has no running process reads nothing
// until something resumes it (#331 D3), so the poster is given the step.
function asleepTargets(where, record) {
  return wokenRoles(where, record).map((role) => notice.asleep(where, role)).filter(Boolean);
}

function wokenRoles(where, record) {
  const bound = Object.values(store.readJsonFile(path.join(where.root, "roles.json"))).filter(Boolean);
  const candidates = [...new Set([...bound, ...(record.mentions || []), ...(record.assignee ? [record.assignee] : [])])];
  return candidates.filter((role) => store.wakes(record, role)).sort();
}

function boundRoles(where) {
  return new Set(Object.values(store.readJsonFile(path.join(where.root, "roles.json"))).filter(Boolean));
}

// `keel chat role --park/--unpark` (#316 D1, D3).
function runPark(where, options) {
  if (options.park !== null && options.unpark !== null) throw new ChatError("Give --park or --unpark, not both.");
  const role = options.park !== null ? options.park : options.unpark;
  if (options.park !== null) {
    if (!boundRoles(where).has(role)) {
      throw new ChatError(`No worktree is bound to ${role}, so there is nothing to park; \`keel chat role\` in its worktree shows its name.`);
    }
    const record = notice.park(where, role, store.currentRole(where), options.reason);
    if (options.json) out(JSON.stringify(record));
    else out(`Parked ${role}${options.reason ? `: ${options.reason}` : ""}. The patrol leaves it alone and posters are told, until \`keel chat role --unpark ${role}\` or its session runs again.`);
    return 0;
  }
  const removed = notice.unpark(where, role);
  const waiting = store.unread(where, role).filter((record) => store.wakes(record, role)).sort((a, b) => (a.id < b.id ? -1 : 1));
  if (options.json) {
    out(JSON.stringify({ role, unparked: removed, waiting: waiting.length, since: waiting.length ? waiting[0].created : null }));
    return 0;
  }
  const head = removed ? `Unparked ${role}.` : `${role} was not parked.`;
  out(waiting.length
    ? `${head} ${waiting.length} addressed record(s) waited since ${waiting[0].created}; ${role} reads them with \`keel chat unread\`.`
    : `${head} Nothing addressed to it waited.`);
  return 0;
}

function postResult(where, record, json) {
  const parked = wokenRoles(where, record).map((role) => notice.parkOf(where, role)).filter(Boolean);
  const isParked = (role) => parked.some((entry) => entry.role === role);
  const asleep = asleepTargets(where, record).filter((entry) => !isParked(entry.role));
  const offline = offlineMentions(where, record).filter((role) => !isParked(role) && !asleep.some((entry) => entry.role === role));
  if (json) {
    out(JSON.stringify({ id: record.id, group: record.group, from: record.from, mentions: record.mentions, offline, asleep, parked }));
    return;
  }
  const lines = [`Posted ${record.id} to ${record.group}.`];
  // A parked role is told nothing new by the post; the poster is (#316 D5).
  for (const entry of parked) {
    lines.push(`${entry.role} is parked since ${entry.at}${entry.by ? ` by ${entry.by}` : ""}${entry.reason ? `: ${entry.reason}` : ""}; `
      + "this waits until it is unparked or its session runs again — route anything urgent through the coordinator.");
  }
  for (const role of offline) lines.push(`Queued for ${role}: offline; it will see this when its session next starts.`);
  for (const entry of asleep.filter((item) => item.cli)) {
    lines.push(`${entry.role}'s CLI session ${entry.session} has no running process, so this record alone wakes nothing; `
      + `resume it with \`keel chat wake now ${entry.role}\` (#348).`);
  }
  for (const entry of asleep.filter((item) => !item.cli)) {
    lines.push(`${entry.role}'s desktop session ${entry.session} has no running process, so this record alone wakes nothing (#331). `
      + notice.wakeStep(entry.session, "You have unread keel chat records; run `keel chat unread`."));
  }
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
    else out(groups.map((g) => `${g.name}${g.archived ? " (archived)" : ""}: ${g.members.map((m) => (g.listeners.includes(m) ? `${m} (listen)` : m)).join(", ")}`).join("\n"));
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
      store.changeMember(where, actor, group, member, action === "add" ? "join" : "leave", { listen: options.listen });
      out(`${action === "add" ? "Added" : "Removed"} ${member} ${action === "add" ? "to" : "from"} ${group}${action === "add" && options.listen ? " as listen-only" : ""}.`);
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
      if (options.park !== null || options.unpark !== null) return runPark(where, options);
      if (options.prune) {
        // Bindings to removed worktrees (#301 D4).
        const pruned = require("./drift").pruneBindings(where);
        if (options.json) out(JSON.stringify({ pruned }));
        else out(pruned.length ? pruned.map((entry) => `Pruned ${entry.role} from ${entry.worktree}.`).join("\n") : "No binding points at a removed worktree.");
        return 0;
      }
      if (options.unset) {
        // The calling worktree's binding, which `--prune` keeps while it exists (#476 D4).
        const roles = store.readJsonFile(path.join(where.root, "roles.json"));
        const unbound = roles[where.worktree] || null;
        if (unbound) {
          delete roles[where.worktree];
          store.writeRoles(where, roles);
        }
        if (options.json) out(JSON.stringify({ unbound: unbound || null, worktree: where.worktree }));
        else out(unbound ? `Unbound ${unbound} from ${where.worktree}.` : "This worktree has no chat role.");
        return 0;
      }
      if (options.rename !== null && options.rename !== undefined) {
        // `--rename <old> <new>` (#376 D7).
        if (!rest[0]) throw new ChatError("keel chat role --rename needs the old and the new name: --rename <old> <new>.");
        const rename = require("./rename");
        const result = rename.rename(where, store.currentRole(where), String(options.rename).toLowerCase(), String(rest[0]).toLowerCase());
        out(options.json ? JSON.stringify(result) : rename.render(result));
        return 0;
      }
      let role = store.currentRole(where);
      if (options.set !== null) role = store.setRole(where, options.set);
      // The session that binds a role becomes its session (#415 D3).
      const bound = options.set !== null && role ? notice.recordBinding(where, role) : null;
      if (options.alias !== null) {
        if (!role) throw new ChatError("Bind a role before adding an alias: `keel chat role --set <name>`.");
        store.addAlias(where, role, options.alias);
      }
      const aliases = role ? store.readMember(where.root, role).aliases : [];
      if (options.json) out(JSON.stringify({ role, aliases, worktree: where.worktree, store: where.root }));
      else out(role ? `Chat role: ${role}${aliases.length ? ` (aliases: ${aliases.join(", ")})` : ""}${bound ? `\n${bound}` : ""}` : "This worktree has no chat role. Bind one with `keel chat role --set <name>`.");
      return 0;
    }
    case "group":
      return runGroup(where, options);
    case "list":
      return runGroup(where, { ...options, positionals: ["group", "list"] });
    case "post": {
      const [group, ...words] = rest;
      if (!group) throw new ChatError("keel chat post needs a group.");
      postResult(where, store.post(where, { group, text: stamped(textFrom(words), options), replyTo: options.replyTo, supersedes: options.supersedes, ack: options.ack, notALoop: options.notALoop }), options.json);
      return 0;
    }
    case "ack": {
      const id = rest[0];
      if (!id) throw new ChatError("keel chat ack needs a record id.");
      const record = store.ack(where, id);
      out(options.json ? JSON.stringify({ id: record.id, target: id }) : `Acknowledged ${id}.`);
      return 0;
    }
    case "acks": {
      const from = options.mine ? store.requireRole(where) : null;
      const rows = store.openAcks(where, { from });
      if (options.json) out(JSON.stringify({ records: rows.map(({ record, acks }) => ({ ...publicRecord(record), acks })) }));
      else if (!rows.length) out("keel chat: no record is waiting on an acknowledgement.");
      else out(rows.map(({ record, acks }) => [`${record.group} ${formatLine(record)}`, ...ackLines(acks).map((line) => `  ${line}`)].join("\n")).join("\n"));
      return 0;
    }
    case "summary": {
      if (options.since === null) throw new ChatError("keel chat summary needs --since <90s|15m|2h|3d|date>.");
      const threshold = parseSince(options.since);
      if (threshold === null) throw new ChatError(`--since ${JSON.stringify(options.since)} is not a time; use 90s, 15m, 2h, 3d, or a date.`);
      const role = store.requireRole(where);
      if (options.group !== null) store.checkGroup(options.group);
      const digest = store.summary(where, role, threshold, { group: options.group });
      const sinceText = store.isoLocal(new Date(threshold));
      if (options.json) out(JSON.stringify({ since: sinceText, ...digest }));
      else out(summaryLines(digest, sinceText).join("\n"));
      return 0;
    }
    case "wait": {
      const [group, ...words] = rest;
      if (!group) throw new ChatError("keel chat wait needs a group.");
      const record = store.wait(where, {
        group, commit: options.commit, branch: options.branch, remote: options.remote, issue: options.issue,
        closed: options.closed, text: words.join(" "),
      });
      out(options.json ? JSON.stringify({ id: record.id, condition: record.condition }) : `Waiting: ${store.describeCondition(record.condition)} (${record.id}).`);
      return 0;
    }
    case "waits": {
      const waits = store.openWaits(where);
      if (options.json) out(JSON.stringify({ waits: waits.map((w) => ({ id: w.id, group: w.group, from: w.from, condition: w.condition, text: w.text, created: w.created })) }));
      else out(waits.length ? waits.map((w) => `${w.group} ${w.id} ${w.from} waits for ${store.describeCondition(w.condition)}${w.text ? `: ${w.text}` : ""}`).join("\n") : "keel chat: nobody is waiting.");
      return 0;
    }
    case "dm": {
      const [target, ...words] = rest;
      if (!target) throw new ChatError("keel chat dm needs a role.");
      postResult(where, store.directPost(where, target, stamped(textFrom(words), options), { notALoop: options.notALoop }), options.json);
      return 0;
    }
    case "unread": {
      const role = store.requireRole(where);
      // Newest first (#252 D3): the latest word is the one to read first.
      const records = store.unread(where, role).reverse();
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
      const acks = record.ack === "requested" ? store.ackStatus(where, record) : null;
      if (options.json) out(JSON.stringify({ record: publicRecord(record), readers, ...(acks ? { acks } : {}) }));
      else out([`${record.group} ${formatLine(record)}`, `read by: ${readers.join(", ") || "nobody yet"}`, ...(acks ? ackLines(acks) : [])].join("\n"));
      return 0;
    }
    case "todo": {
      const [group, ...words] = rest;
      if (!group) throw new ChatError("keel chat todo needs a group.");
      if (options.assignee === null) throw new ChatError("keel chat todo needs --assignee <role>.");
      postResult(where, store.todo(where, { group, assignee: options.assignee, issue: options.issue, text: textFrom(words), replyTo: options.replyTo, ack: options.ack }), options.json);
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
        postResult(where, store.post(where, { group: command, text: rest.join(" "), replyTo: options.replyTo, supersedes: options.supersedes, ack: options.ack }), options.json);
        return 0;
      }
      return runView(where, command, options);
    }
  }
}

// The machine's bot list (chat-shared-bots D1). It needs no repository and
// shows only whether each Keychain entry exists, never its value.
function runBot(rest) {
  const bridge = require("./bridge");
  const lifecycle = require("./lifecycle");
  const [action, name] = rest;
  switch (action) {
    case "add":
      if (!name) throw new ChatError("keel chat bot add needs a bot name.");
      out(`Listed bot ${bridge.addBot(name)}. Store its tokens as Keychain accounts bot:${name} and app:${name} of service keel-chat-slack, map its Slack user id to a role in each project's keel/chat.json slack.bots, and restart the bridge.`);
      return 0;
    case "remove":
      if (!name) throw new ChatError("keel chat bot remove needs a bot name.");
      out(`Unlisted bot ${bridge.removeBot(name)}; its Keychain entries are untouched. Restart the bridge to stop using it.`);
      return 0;
    case "list": {
      const bots = bridge.readBots();
      if (!bots.length) {
        out("No bots listed on this machine. Add one with `keel chat bot add <name>`.");
        return 0;
      }
      for (const bot of bots) {
        const tokens = lifecycle.botTokens(bot);
        out(`${bot}: bot token ${tokens.bot ? "stored" : "missing"}, app token ${tokens.app ? "stored" : "missing"}`);
      }
      return 0;
    }
    default:
      throw new ChatError(`Unknown keel chat bot action ${JSON.stringify(action)}: use add, remove, or list.`);
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
      for (const app of status.bots || []) {
        const parts = [`Bot ${app.bot}: ${app.state}`];
        if (app.reason) parts.push(app.reason);
        if (app.state === "verified") parts.push(app.roles.length ? `serves ${app.roles.join(", ")}` : "serves no role: no project's slack.bots maps its id");
        if (app.state === "verified") parts.push(app.direct ? "direct messages connected" : `direct messages ${app.direct_note || "not connected"}`);
        if (app.invite && app.invite.length) parts.push(`invite it to ${app.invite.join(", ")}; until then it posts through the shared app there`);
        lines.push(`${parts.join("; ")}.`);
      }
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
      out(lifecycle.start() ? "Started the bridge." : "The bridge is already loaded; launchd keeps it running.");
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
    case "now": {
      // One step for a role whose CLI session ended (#348 D3).
      const role = options.positionals[2];
      if (!role) throw new ChatError("keel chat wake now needs a role.");
      store.checkName(role, "Role");
      const where = store.requireLocation(cwd);
      const presence = store.readJsonFile(path.join(where.root, "presence", `${role}.json`));
      if (!presence.cli_session) throw new ChatError(`${role} has recorded no Claude Code CLI session, so there is nothing to resume.`);
      const entry = notice.asleep(where, role);
      if (!entry || !entry.cli) {
        out(`${role}'s CLI session ${presence.cli_session} is running; a record addressed to it wakes it, so nothing was resumed.`);
        return 0;
      }
      const resumed = notice.resumeCli(entry, where);
      if (resumed.removed) throw new ChatError(`${role}'s recorded CLI ${resumed.output}.`);
      if (resumed.moved) throw new ChatError(`${role}'s recorded CLI ${resumed.output}`);
      out(`${resumed.ok ? "Resumed" : "Could not resume"} ${role}'s CLI session ${entry.session} in ${entry.worktree}.${resumed.output ? `\n${resumed.output}` : ""}`);
      return resumed.ok ? 0 : 1;
    }
    default:
      throw new ChatError(`Unknown keel chat wake action ${JSON.stringify(action)}: use add, remove, status, run, or now.`);
  }
}

function runChat(argv) {
  try {
    const options = parseChatArgs(argv);
    const cwd = path.resolve(options.repo || process.cwd());
    if (!options.positionals.length || options.positionals[0] === "help" || options.help) {
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
    // The bot list belongs to the machine, like the bridge.
    if (options.positionals[0] === "bot") return runBot(options.positionals.slice(1));
    // A notice is read by hosts on every prompt: outside a repository it says
    // nothing and still exits 0.
    if (options.positionals[0] === "notice" && !store.locate(cwd)) return 0;
    const where = store.requireLocation(cwd);
    migrateIfNeeded(where);
    const role = store.currentRole(where);
    if (role) notice.commandPresence(where, role);
    // Two live sessions on one role share its name and cursor (#369 D3).
    if (role && ["post", "dm", "todo", "unread", "read"].includes(options.positionals[0])) {
      const twins = notice.twinWarning(where, role);
      if (twins) process.stderr.write(`keel chat: ${twins}\n`);
    }
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
