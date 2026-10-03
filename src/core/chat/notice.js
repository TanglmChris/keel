"use strict";

// What a session is told about the chat, and when it is woken (issue #187,
// design D9, D10).
//
// Only a record that needs this role — a mention by name or alias, a todo
// assigned to it, a message in its direct group — touches `signal/<role>`,
// the file a host watches to wake an idle session. `@all` and plain messages
// are counted at the next prompt instead, so a busy group cannot keep every
// session awake.
//
// `keel chat notice` prints the notice for any host and always exits 0;
// `keel chat hook <event>` wraps the same text for Claude Code. Neither moves a
// cursor: a notice is a pointer that stays true until the role reads.

const fs = require("fs");
const path = require("path");
const store = require("./store");
const { relativeAge } = require("./view");

const NOTICE_LIMIT = 5;

function firstLine(text) {
  const line = String(text || "").split("\n").find((part) => part.trim()) || "";
  return line.length > 120 ? `${line.slice(0, 117)}...` : line;
}

function noticeText(where, role, now = Date.now()) {
  const records = store.unread(where, role);
  if (!records.length) return "";
  const waking = records.filter((record) => store.wakes(record, role));
  const others = new Map();
  for (const record of records) {
    if (waking.includes(record)) continue;
    others.set(record.group, (others.get(record.group) || 0) + 1);
  }
  const lines = [
    `keel chat: ${records.length} unread for role \`${role}\`, ${waking.length} addressed to you.`,
  ];
  for (const record of waking.slice(0, NOTICE_LIMIT)) {
    lines.push(`- ${record.id} in ${record.group} from \`${record.from}\`, ${relativeAge(record.created, now)}: ${firstLine(record.text)}`);
  }
  if (waking.length > NOTICE_LIMIT) lines.push(`- and ${waking.length - NOTICE_LIMIT} more addressed to you.`);
  if (others.size) {
    lines.push(`Other unread: ${[...others].map(([group, count]) => `${group}: ${count} unread`).join(", ")}.`);
  }
  lines.push(
    "Read with `keel chat read` (everything) or `keel chat <group>`; reply with "
      + "`keel chat post <group> <text> --reply-to <id>`.",
    store.DATA_NOTICE
  );
  return lines.join("\n");
}

function presenceFile(where, role) {
  return path.join(where.root, "presence", `${role}.json`);
}

// Presence is written only by its own role, so it never conflicts (D1).
function touchPresence(where, role, state = "online", host = null) {
  const previous = store.readJsonFile(presenceFile(where, role));
  const record = {
    state,
    last_active: store.isoLocal(new Date()),
    host: host || previous.host || null,
  };
  try {
    store.writeJsonAtomic(where, presenceFile(where, role), record);
  } catch {
    // Presence is a convenience: failing to record it must not fail a command.
  }
}

const ONLINE_WINDOW_MS = 24 * 60 * 60 * 1000;

// `online`, `idle`, or `offline`, with the time of last activity (D10).
function presenceOf(where, role, now = Date.now()) {
  const record = store.readJsonFile(presenceFile(where, role));
  const time = Date.parse(record.last_active || "");
  if (Number.isNaN(time)) return { state: "offline", last_active: null };
  if (record.state === "offline") return { state: "offline", last_active: record.last_active };
  return { state: now - time <= ONLINE_WINDOW_MS ? "online" : "idle", last_active: record.last_active };
}

function signalPath(where, role) {
  return path.join(where.root, "signal", role);
}

function ensureSignal(where, role) {
  const signal = signalPath(where, role);
  fs.mkdirSync(path.dirname(signal), { recursive: true });
  if (!fs.existsSync(signal)) fs.writeFileSync(signal, "");
  return signal;
}

// For a Slack-enabled project, whether this machine's bridge is carrying the
// chat, so a session does not assume the owner's phone can reach it (D18).
function bridgeLine(where) {
  let settings;
  try {
    settings = require("./config").slackSettings(where.worktree);
  } catch {
    return null;
  }
  if (!settings.enabled) return null;
  const status = require("./bridge").fullStatus();
  if (!status.running) {
    return "keel chat bridge: not running on this machine, so Slack messages are not reaching this session "
      + "(local chat still works). `keel chat bridge start`, or `keel chat bridge install` once, brings it up.";
  }
  if (status.paused) return `keel chat bridge: paused until ${status.paused_until}; messages wait until then.`;
  return `keel chat bridge: running${status.connected ? " and connected" : ", reconnecting"}, serving ${status.projects.length} project${status.projects.length === 1 ? "" : "s"}.`;
}

const HOST_EVENTS = {
  "session-start": "SessionStart",
  "user-prompt-submit": "UserPromptSubmit",
  "file-changed": "FileChanged",
  "session-end": "SessionEnd",
};

// Claude Code hook entry. Silent, and exit 0, wherever there is no role —
// including outside any repository — because exit 2 from FileChanged is the
// wake signal and must mean only "something addressed to you arrived".
const MAIL_POINTER = "Direct messages can also be read with the 5.83 `keel mail read`.";

function hook(event, input, { mail = false } = {}) {
  if (!(event in HOST_EVENTS)) return { code: 0 };
  let payload = {};
  try {
    payload = JSON.parse(input || "{}") || {};
  } catch {
    payload = {};
  }
  let where = null;
  let role = null;
  try {
    where = store.locate(payload.cwd || process.cwd());
    role = where ? store.currentRole(where) : null;
  } catch {
    role = null;
  }
  if (!where || !role) return { code: 0 };
  if (event === "session-end") {
    touchPresence(where, role, "offline");
    return { code: 0 };
  }
  touchPresence(where, role, "online", mail ? null : "claude-code");
  const chatText = noticeText(where, role);
  const text = chatText && mail ? `${chatText}\n${MAIL_POINTER}` : chatText;
  if (event === "session-start") {
    const output = {
      hookSpecificOutput: { hookEventName: "SessionStart", watchPaths: [ensureSignal(where, role)] },
    };
    const context = [bridgeLine(where), text].filter(Boolean).join("\n");
    if (context) output.hookSpecificOutput.additionalContext = context;
    return { code: 0, stdout: `${JSON.stringify(output)}\n` };
  }
  if (event === "user-prompt-submit") {
    if (!text) return { code: 0 };
    return {
      code: 0,
      stdout: `${JSON.stringify({ hookSpecificOutput: { hookEventName: "UserPromptSubmit", additionalContext: text } })}\n`,
    };
  }
  // file-changed
  const waking = store.unread(where, role).some((record) => store.wakes(record, role));
  return waking ? { code: 2, stderr: `${text}\n` } : { code: 0 };
}

// The model-free question a scheduler asks before starting a turn (#194):
// is anything that would wake this role unread? Exit 0 for yes, 1 for no —
// and 1 wherever there is no repository or role, since then there is
// nothing to answer. Reads only; writes nothing.
function check(cwd) {
  try {
    const where = store.locate(cwd);
    const role = where ? store.currentRole(where) : null;
    if (!where || !role) return 1;
    return store.unread(where, role).some((record) => store.wakes(record, role)) ? 0 : 1;
  } catch {
    return 1;
  }
}

module.exports = {
  NOTICE_LIMIT,
  check,
  bridgeLine,
  hook,
  noticeText,
  presenceOf,
  signalPath,
  touchPresence,
};
