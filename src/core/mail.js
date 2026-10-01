"use strict";

// `keel mail`: the 5.83 cross-host mailbox commands (issue #180), kept as a
// compatibility layer over the group chat (issue #187, design D7). The
// one-to-one, read-once mailbox under `keel-mailbox/` became chat direct
// groups under `keel-chat/`: the first `keel mail` or `keel chat` command
// migrates it, and these commands then work on the direct groups.
//
//   role [--set]          binds the worktree's chat role, as before
//   send --to <role>      posts "<subject>\n\n<body>" to dm-<a>--<b>
//   list                  unread direct messages
//   read [--id <id>]      prints them under the data-not-instruction header
//                         and advances the reader's cursor; nothing moves
//   hook <event>          relays to `keel chat hook <event>`
//
// A message is data from another agent. Nothing here grants authority, and no
// gate reads the store.

const fs = require("fs");
const path = require("path");
const store = require("./chat/store");
const { migrateIfNeeded } = require("./chat/migrate");

const { ChatError, DATA_NOTICE } = store;

const USAGE = [
  "keel mail role [--set <name>] [--json]",
  "keel mail send --to <role> --subject <text> [--body <text> | stdin] [--reply-to <id>] [--ref <ref>]... [--json]",
  "keel mail list [--json]",
  "keel mail read [--id <id>] [--json]",
  "keel mail hook session-start|user-prompt-submit|file-changed   (host hook; JSON on stdin)",
  "These are the 5.83 commands over keel chat direct groups; see keel chat help.",
];

function parseMailArgs(argv) {
  const options = {
    subcommand: argv[0] || null,
    repo: null,
    json: false,
    set: null,
    to: null,
    subject: null,
    body: null,
    replyTo: null,
    refs: [],
    id: null,
    event: null,
  };
  const valued = {
    "--set": "set",
    "--to": "to",
    "--subject": "subject",
    "--body": "body",
    "--reply-to": "replyTo",
    "--id": "id",
  };
  for (let index = 1; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--json") {
      options.json = true;
      continue;
    }
    const eq = arg.indexOf("=");
    const flag = arg.startsWith("--") && eq > 0 ? arg.slice(0, eq) : arg;
    if (flag in valued || flag === "--ref") {
      let value;
      if (flag !== arg) {
        value = arg.slice(eq + 1);
      } else {
        index += 1;
        if (index >= argv.length) throw new ChatError(`${arg} requires a value.`);
        value = argv[index];
      }
      if (flag === "--ref") {
        options.refs.push(value);
        continue;
      }
      const key = valued[flag];
      if (options[key] !== null) throw new ChatError(`${flag} was provided more than once.`);
      options[key] = value;
      continue;
    }
    if (arg.startsWith("-")) throw new ChatError(`Unknown option for keel mail: ${arg}`);
    if (options.subcommand === "hook" && options.event === null) {
      options.event = arg;
      continue;
    }
    if (options.repo !== null) throw new ChatError("repo path was provided more than once.");
    options.repo = arg;
  }
  return options;
}

function out(text) {
  process.stdout.write(text.endsWith("\n") ? text : `${text}\n`);
}

function readStdin() {
  try {
    return fs.readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

// A migrated or `send`-written message carries its subject as the first line.
function asMail(record) {
  const [subject, ...rest] = String(record.text || "").split("\n");
  const to = record.group.replace(/^dm-/, "").split("--").find((role) => role !== record.from) || null;
  return {
    id: record.id,
    from: record.from,
    to,
    created: record.created,
    subject,
    body: rest.join("\n").replace(/^\n/, ""),
    reply_to: record.reply_to || null,
    refs: record.refs || [],
  };
}

function directUnread(where, role) {
  return store.unread(where, role).filter((record) => record.group.startsWith("dm-")).map(asMail);
}

function notice(role, messages) {
  return [
    `keel mail: ${messages.length} unread message${messages.length === 1 ? "" : "s"} for role \`${role}\`.`,
    ...messages.map((m) => `- ${m.id} from \`${m.from}\`: ${m.subject}`),
    "Run `keel mail read` (or `keel mail read --id <id>`) to receive them. "
      + "Reply with `keel mail send --to <role> --reply-to <id>`.",
    DATA_NOTICE,
  ].join("\n");
}

function formatMessage(message) {
  const lines = [
    `## ${message.subject}`,
    "",
    `- id: ${message.id}`,
    `- from: ${message.from}`,
    `- to: ${message.to}`,
    `- created: ${message.created}`,
  ];
  if (message.reply_to) lines.push(`- reply_to: ${message.reply_to}`);
  if (message.refs.length) lines.push(`- refs: ${message.refs.join(", ")}`);
  lines.push("", message.body, "");
  return lines.join("\n");
}

function requireRole(where) {
  const role = store.currentRole(where);
  if (!role) throw new ChatError("This worktree has no mail role. Bind one with `keel mail role --set <name>`.");
  return role;
}

function runMail(argv) {
  let options = { subcommand: argv[0] || null };
  try {
    options = parseMailArgs(argv);
    if (options.subcommand === "hook") {
      return require("./chat/cli").runChat(["hook", options.event || ""]);
    }
    if (options.subcommand === "help") {
      out(`Usage:\n  ${USAGE.join("\n  ")}`);
      return 0;
    }
    const where = store.requireLocation(path.resolve(options.repo || process.cwd()));
    migrateIfNeeded(where);
    switch (options.subcommand) {
      case "role": {
        const role = options.set !== null ? store.setRole(where, options.set) : store.currentRole(where);
        if (options.json) out(JSON.stringify({ role, worktree: where.worktree, mailbox: where.root }));
        else out(role ? `Mail role: ${role}` : "This worktree has no mail role. Bind one with `keel mail role --set <name>`.");
        return 0;
      }
      case "send": {
        if (options.to === null) throw new ChatError("keel mail send requires --to <role>.");
        if (!options.subject || !options.subject.trim()) throw new ChatError("keel mail send requires --subject.");
        const body = options.body !== null ? options.body : process.stdin.isTTY ? "" : readStdin();
        if (!body.trim()) throw new ChatError("keel mail send requires a body: --body <text> or stdin.");
        const record = store.directPost(where, options.to, `${options.subject.trim()}\n\n${body}`, {
          replyTo: options.replyTo,
          refs: options.refs,
        });
        if (options.json) out(JSON.stringify({ id: record.id, from: record.from, to: options.to, group: record.group }));
        else out(`Sent ${record.id} to ${options.to}.`);
        return 0;
      }
      case "list": {
        const role = store.currentRole(where);
        const messages = role ? directUnread(where, role) : [];
        if (options.json) out(JSON.stringify({ role, unread: messages.map(({ body, ...rest }) => rest) }));
        else if (!role) out("This worktree has no mail role. Bind one with `keel mail role --set <name>`.");
        else out(messages.length ? notice(role, messages) : `keel mail: no unread messages for role \`${role}\`.`);
        return 0;
      }
      case "read": {
        const role = requireRole(where);
        let messages = directUnread(where, role);
        if (options.id) {
          messages = messages.filter((m) => m.id === options.id);
          if (!messages.length) throw new ChatError(`No unread message ${options.id} for role ${role}.`);
        }
        // A cursor is a position, so reading a message marks what precedes it
        // in the same direct group as read too.
        for (const message of messages) {
          store.advanceCursor(where, role, store.directName(message.from, role), message.id);
        }
        if (options.json) out(JSON.stringify({ role, notice: DATA_NOTICE, messages }));
        else if (!messages.length) out(`keel mail: no unread messages for role \`${role}\`.`);
        else out([`> ${DATA_NOTICE}`, "", ...messages.map(formatMessage)].join("\n"));
        return 0;
      }
      default:
        throw new ChatError(`Unknown keel mail subcommand ${JSON.stringify(options.subcommand)}. Usage:\n  ${USAGE.join("\n  ")}`);
    }
  } catch (error) {
    if (!(error instanceof ChatError)) throw error;
    process.stderr.write(`keel mail: ${error.message}\n`);
    return 2;
  }
}

module.exports = {
  DATA_NOTICE,
  MAIL_USAGE: USAGE,
  runMail,
};
