"use strict";

// The Slack bridge (issue #187, design D14–D16): one process per machine that
// relays every opted-in project on that machine to Slack and back, so sessions
// on other machines and the owner's phone take part in real time.
//
// The local store stays the only source of truth. Agents never talk to Slack;
// they run `keel chat`, and the bridge carries records out and in. Each
// machine has its own Slack app (Socket Mode delivers each event to one
// connection of an app, design F1) and posts only records that originated on
// it, carrying the exact record in message metadata so other machines rebuild
// it rather than re-parse prose.
//
// Bridge state lives in each project's store under `bridge/`, in the local
// layer: `bridge/posted/<id>.json` maps a record to its channel and ts.

const fs = require("fs");
const os = require("os");
const path = require("path");
const store = require("./store");
const { slackSettings } = require("./config");
const { redact } = require("./redact");
const slack = require("./slack");

const { ChatError } = store;
const METADATA_TYPE = "keel_chat_record";
const TEXT_LIMIT = 3000;
const OUTBOUND_ORIGINS = new Set(["local", "migrated"]);

function keelHome() {
  return process.env.KEEL_HOME || path.join(os.homedir(), ".keel");
}

function registryFile() {
  return path.join(keelHome(), "chat", "projects.json");
}

function readRegistry() {
  try {
    const parsed = JSON.parse(fs.readFileSync(registryFile(), "utf8"));
    return Array.isArray(parsed.projects) ? parsed.projects.filter((entry) => typeof entry === "string") : [];
  } catch {
    return [];
  }
}

function writeRegistry(projects) {
  const file = registryFile();
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(temp, `${JSON.stringify({ projects: [...new Set(projects)].sort() }, null, 2)}\n`);
  fs.renameSync(temp, file);
}

// The registry holds paths only; each project's data stays in its own store.
function addProject(where) {
  writeRegistry([...readRegistry(), where.worktree]);
  return where.worktree;
}

function removeProject(where) {
  writeRegistry(readRegistry().filter((entry) => entry !== where.worktree));
  return where.worktree;
}

function requireWebSocket() {
  if (typeof globalThis.WebSocket !== "function") {
    throw new ChatError(
      `keel chat bridge needs Node 22 or newer for its built-in WebSocket; this is Node ${process.versions.node}. `
        + "The rest of keel chat works on this Node."
    );
  }
}

// --- served projects ----------------------------------------------------------

function servedProjects() {
  const projects = [];
  for (const entry of readRegistry()) {
    const where = store.locate(entry);
    if (!where) continue;
    const settings = slackSettings(where.worktree);
    if (!settings.enabled) continue;
    projects.push({ where, settings });
  }
  // A channel mapped by more than one served project shows senders as
  // `<project>/<role>` so readers can tell the projects apart (D3).
  const mappers = new Map();
  for (const project of projects) {
    for (const channel of Object.values(project.settings.channels)) {
      mappers.set(channel, (mappers.get(channel) || 0) + 1);
    }
  }
  for (const project of projects) project.sharedChannels = new Set([...mappers].filter(([, n]) => n > 1).map(([c]) => c));
  return projects;
}

// --- outbound -------------------------------------------------------------------

function postedFile(where, id) {
  return path.join(where.root, "bridge", "posted", `${id}.json`);
}

function readPosted(where, id) {
  try {
    return JSON.parse(fs.readFileSync(postedFile(where, id), "utf8"));
  } catch {
    return null;
  }
}

function writePosted(where, id, value) {
  store.writeJsonAtomic(where, postedFile(where, id), value);
}

function senderName(project, channel, role) {
  return project.sharedChannels.has(channel) ? `${project.where.project}/${role}` : role;
}

function bodyText(record) {
  switch (record.kind) {
    case "todo":
      return `☐ todo → ${record.assignee || "?"}${record.issue ? ` (${record.issue})` : ""}: ${record.text}`;
    case "join":
      return `${record.from} added ${record.target} to the group.`;
    case "leave":
      return `${record.from} removed ${record.target} from the group.`;
    case "archive":
      return `${record.from} archived the group; it takes no new messages.`;
    default:
      return record.text;
  }
}

// Redact, then cut, then address: the cut must not split a `[redacted]`, and
// the owner mention must survive the cut.
function slackText(project, record, text) {
  let result = redact(text);
  if (result.length > TEXT_LIMIT) {
    result = `${result.slice(0, TEXT_LIMIT)}… (cut; full text: \`keel chat show ${record.id}\`)`;
  }
  if ((record.mentions || []).includes(store.OWNER) && project.settings.owner) {
    result = `<@${project.settings.owner}> ${result}`;
  }
  return result;
}

function metadataFor(project, record) {
  const payload = { project: project.where.project, id: record.id, kind: record.kind, from: record.from, group: record.group };
  for (const key of ["mentions", "reply_to", "assignee", "issue", "target"]) {
    const value = record[key];
    if (value !== undefined && value !== null && value !== "" && !(Array.isArray(value) && !value.length)) payload[key] = value;
  }
  return { event_type: METADATA_TYPE, event_payload: payload };
}

function iconFields(project, role) {
  const icon = project.settings.icons[role];
  if (!icon) return {};
  return icon.startsWith(":") ? { icon_emoji: icon } : { icon_url: icon };
}

async function postRecord(project, record, channel, token, log) {
  const { where } = project;
  const call = (method, params) => slack.callWithRetry(method, params, token, {
    onWait: (name, seconds) => log(`Slack asked to wait ${seconds}s before ${name}.`),
  });
  if (record.kind === "done" || record.kind === "edit" || record.kind === "retract") {
    const target = readPosted(where, record.target);
    if (!target) {
      // The target never reached Slack (it predates the mapping, or came from
      // there): nothing to change, and nothing to retry.
      writePosted(where, record.id, { skipped: "target not on Slack" });
      return;
    }
    if (record.kind === "done") {
      await call("reactions.add", { channel: target.channel, timestamp: target.ts, name: "white_check_mark" });
    } else if (record.kind === "edit") {
      const original = store.findRecord(where, record.target) || {};
      await call("chat.update", { channel: target.channel, ts: target.ts, text: slackText(project, original, bodyText({ ...original, text: record.text })) });
    } else {
      await call("chat.delete", { channel: target.channel, ts: target.ts });
    }
    writePosted(where, record.id, { channel: target.channel, ts: target.ts, kind: record.kind });
    return;
  }
  const params = {
    channel,
    text: slackText(project, record, bodyText(record)),
    username: senderName(project, channel, record.from),
    metadata: metadataFor(project, record),
    unfurl_links: false,
    ...iconFields(project, record.from),
  };
  if (record.reply_to) {
    const parent = readPosted(where, record.reply_to);
    if (parent && parent.ts) params.thread_ts = parent.thread_ts || parent.ts;
    else params.text = `↳ reply to ${record.reply_to}\n${params.text}`;
  }
  const response = await call("chat.postMessage", params);
  writePosted(where, record.id, { channel, ts: response.ts, thread_ts: params.thread_ts || null });
}

// Every record that originated on this machine, in a mapped group, and not yet
// posted, in id order. The queue is derived, so it survives any restart.
function pendingOutbound(project) {
  const { where, settings } = project;
  const pending = [];
  for (const [group, channel] of Object.entries(settings.channels)) {
    for (const record of store.readLog(where, group)) {
      if (!OUTBOUND_ORIGINS.has(record.origin || "local")) continue;
      if (readPosted(where, record.id)) continue;
      pending.push({ record, channel });
    }
  }
  return pending.sort((a, b) => (a.record.id < b.record.id ? -1 : 1));
}

async function flushOutbound(projects, token, log) {
  let posted = 0;
  for (const project of projects) {
    for (const { record, channel } of pendingOutbound(project)) {
      await postRecord(project, record, channel, token, log);
      posted += 1;
    }
  }
  return posted;
}

function tokens() {
  const bot = (process.env.KEEL_SLACK_BOT_TOKEN || "").trim();
  const app = (process.env.KEEL_SLACK_APP_TOKEN || "").trim();
  return { bot: bot || null, app: app || null };
}

async function runOnce(log) {
  requireWebSocket();
  const { bot } = tokens();
  if (!bot) throw new ChatError("No Slack bot token: set KEEL_SLACK_BOT_TOKEN.");
  const projects = servedProjects();
  const posted = await flushOutbound(projects, bot, log);
  log(`Bridge pass done: ${projects.length} project${projects.length === 1 ? "" : "s"} served, ${posted} record${posted === 1 ? "" : "s"} sent.`);
  return 0;
}

module.exports = {
  METADATA_TYPE,
  addProject,
  flushOutbound,
  keelHome,
  readPosted,
  readRegistry,
  removeProject,
  requireWebSocket,
  runOnce,
  servedProjects,
  tokens,
  writePosted,
};
