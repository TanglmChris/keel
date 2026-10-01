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
const lifecycle = require("./lifecycle");

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

async function postRecord(ctx, project, record, channel) {
  const { where } = project;
  const call = (method, params) => slack.callWithRetry(method, params, ctx.token, {
    onWait: (name, seconds) => ctx.log(`Slack asked to wait ${seconds}s before ${name}.`),
  });
  if (record.kind === "done" || record.kind === "edit" || record.kind === "retract") {
    const target = readPosted(where, record.target);
    if (!target || !target.ts) {
      // The target never reached Slack (it predates the mapping): nothing to
      // change there, and nothing to retry.
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
  const posted = { channel, ts: response.ts, thread_ts: params.thread_ts || null };
  writePosted(where, record.id, posted);
  rememberTs(project, channel, response.ts, record.id);
  // Another project on this machine that maps the same channel gets the
  // record now, without waiting for Slack to echo it back (D16).
  for (const other of ctx.projects) {
    if (other === project || !other.channelGroups.has(channel)) continue;
    importKeelRecord(ctx, other, channel, params.metadata.event_payload, { ts: response.ts, text: record.text, thread_ts: params.thread_ts });
  }
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

async function flushOutbound(ctx) {
  let posted = 0;
  for (const project of ctx.projects) {
    for (const { record, channel } of pendingOutbound(project)) {
      await postRecord(ctx, project, record, channel);
      posted += 1;
    }
  }
  return posted;
}

function unpostedCount(projects) {
  return projects.reduce((sum, project) => sum + pendingOutbound(project).length, 0);
}

// --- inbound --------------------------------------------------------------------

// channel|ts -> record id, for threads, edits, deletions, and reactions.
function buildTsIndex(project) {
  project.tsIndex = new Map();
  const dir = path.join(project.where.root, "bridge", "posted");
  let names = [];
  try {
    names = fs.readdirSync(dir).filter((name) => name.endsWith(".json"));
  } catch {
    return;
  }
  for (const name of names) {
    const posted = readPosted(project.where, name.slice(0, -5));
    if (posted && posted.ts && posted.channel && !posted.kind) {
      project.tsIndex.set(`${posted.channel}|${posted.ts}`, name.slice(0, -5));
    }
  }
}

function rememberTs(project, channel, ts, id) {
  if (project.tsIndex) project.tsIndex.set(`${channel}|${ts}`, id);
}

function recordAt(project, channel, ts) {
  return ts ? project.tsIndex.get(`${channel}|${ts}`) || null : null;
}

function tsToIso(ts) {
  return store.isoLocal(new Date(Math.round(Number(ts) * 1000)));
}

// Undo what outbound added around a Keel record's text, so a rebuilt record
// reads like the original.
function unwrapText(project, text, kind) {
  let result = String(text || "");
  if (project.settings.owner) result = result.replace(new RegExp(`^<@${project.settings.owner}> `), "");
  result = result.replace(/^↳ reply to \S+\n/, "");
  if (kind === "todo") result = result.replace(/^☐ todo → [^:]*: /, "");
  return result;
}

function importKeelRecord(ctx, project, channel, payload, message) {
  const { where } = project;
  if (!payload || !payload.id || store.findRecord(where, payload.id)) return false;
  const same = payload.project === where.project;
  // Membership and archive belong to each project; another project's are not
  // imported into this one.
  if (!same && !store.READABLE_KINDS.has(payload.kind)) return false;
  const group = project.channelGroups.get(channel);
  if (!group) return false;
  store.writeRecord(where, {
    id: payload.id,
    group,
    kind: payload.kind || "message",
    from: same ? payload.from : `${payload.project}/${payload.from}`,
    created: tsToIso(message.ts),
    mentions: Array.isArray(payload.mentions) ? payload.mentions : [],
    reply_to: payload.reply_to || null,
    assignee: payload.assignee || null,
    issue: payload.issue || null,
    target: payload.target || null,
    origin: same ? "slack" : `remote:${payload.project}`,
    text: unwrapText(project, message.text, payload.kind),
  });
  writePosted(where, payload.id, { channel, ts: message.ts, thread_ts: message.thread_ts || null, origin: "slack" });
  rememberTs(project, channel, message.ts, payload.id);
  return true;
}

async function metadataOf(ctx, channel, event) {
  if (event.metadata && event.metadata.event_type) return event.metadata;
  const history = await slack.callWithRetry("conversations.history", {
    channel, latest: event.ts, inclusive: true, limit: 1, include_all_metadata: true,
  }, ctx.token);
  const found = (history.messages || []).find((message) => message.ts === event.ts);
  return (found && found.metadata) || null;
}

async function handleBotMessage(ctx, channel, event) {
  // This bridge's own posts without a record — its online and stopped
  // notices — carry nothing to import.
  if (event.bot_id && event.bot_id === ctx.self.bot_id && !event.metadata) return;
  const metadata = await metadataOf(ctx, channel, event);
  if (!metadata || metadata.event_type !== METADATA_TYPE) return;
  const payload = metadata.event_payload || {};
  for (const project of projectsFor(ctx, channel)) {
    // This bridge's own post, for this project, is already the local record.
    if (event.bot_id === ctx.self.bot_id && payload.project === project.where.project) continue;
    importKeelRecord(ctx, project, channel, payload, event);
  }
}

const MENTION = /(^|[^\w@/])@([A-Za-z0-9][A-Za-z0-9/-]*)/g;

// A person typing in Slack gets no autocomplete, so an `@word` that names no
// member is left as text rather than refused (D16).
function lenientMentions(project, group, text) {
  const state = store.groupState(store.readLog(project.where, group));
  const aliases = store.aliasMap(project.where.root);
  const mentions = [];
  for (const match of String(text).matchAll(MENTION)) {
    const token = match[2].replace(/[-/]+$/, "").toLowerCase();
    let role = null;
    if (token === store.ALL || token === store.OWNER || token.includes("/") || state.members.has(token)) role = token;
    else if (aliases[token] && state.members.has(aliases[token])) role = aliases[token];
    if (role && !mentions.includes(role)) mentions.push(role);
  }
  return mentions;
}

function humanText(project, event) {
  let text = String(event.text || "").replace(/<@([A-Z0-9]+)(\|[^>]*)?>/g, (match, user) => {
    const role = project.settings.members[user];
    return role ? `@${role}` : match;
  });
  for (const file of event.files || []) {
    const link = file.permalink || file.url_private || "";
    text += `${text ? "\n" : ""}📎 ${file.name || file.title || "file"}${link ? `: ${link}` : ""}`;
  }
  return text;
}

function handleHumanMessage(ctx, channel, event) {
  let imported = false;
  let registered = false;
  for (const project of projectsFor(ctx, channel)) {
    const role = project.settings.members[event.user];
    if (!role) continue;
    registered = true;
    if (recordAt(project, channel, event.ts)) continue;
    const group = project.channelGroups.get(channel);
    let text = humanText(project, event);
    let replyTo = null;
    if (event.thread_ts && event.thread_ts !== event.ts) {
      replyTo = recordAt(project, channel, event.thread_ts);
      if (!replyTo) text = `↳ reply to Slack message ${event.thread_ts}\n${text}`;
    }
    const record = store.writeRecord(project.where, {
      group,
      kind: "message",
      from: role,
      created: tsToIso(event.ts),
      mentions: lenientMentions(project, group, text),
      reply_to: replyTo,
      origin: "slack",
      text,
    }, new Date(Math.round(Number(event.ts) * 1000)));
    writePosted(project.where, record.id, { channel, ts: event.ts, thread_ts: event.thread_ts || null, origin: "slack" });
    rememberTs(project, channel, event.ts, record.id);
    imported = true;
  }
  // Someone no project registered: never relayed, only counted (D16).
  if (!registered && event.user !== ctx.self.user_id) ctx.stats.ignored += 1;
  return imported;
}

function authorOf(project, message) {
  if (message.user && project.settings.members[message.user]) return project.settings.members[message.user];
  return null;
}

function handleChanged(ctx, channel, event) {
  const message = event.message || {};
  if (message.bot_id && message.bot_id === ctx.self.bot_id) return;
  for (const project of projectsFor(ctx, channel)) {
    const id = recordAt(project, channel, message.ts);
    if (!id) continue;
    const record = store.findRecord(project.where, id);
    if (!record) continue;
    const author = message.bot_id ? record.from : authorOf(project, message);
    if (!author || author !== record.from) continue;
    const text = message.bot_id ? unwrapText(project, message.text, record.kind) : humanText(project, message);
    const { displayRecords } = require("./view");
    const current = displayRecords(store.readLog(project.where, record.group)).find((r) => r.id === id);
    if (current && current.text === text) continue;
    store.writeRecord(project.where, { group: record.group, kind: "edit", from: record.from, target: id, origin: "slack", text });
  }
}

function handleDeleted(ctx, channel, event) {
  const previous = event.previous_message || {};
  if (previous.bot_id && previous.bot_id === ctx.self.bot_id) return;
  const ts = event.deleted_ts || previous.ts;
  for (const project of projectsFor(ctx, channel)) {
    const id = recordAt(project, channel, ts);
    if (!id) continue;
    const record = store.findRecord(project.where, id);
    if (!record) continue;
    const already = store.readLog(project.where, record.group).some((r) => r.kind === "retract" && r.target === id);
    if (already) continue;
    store.writeRecord(project.where, { group: record.group, kind: "retract", from: record.from, target: id, origin: "slack", text: "" });
  }
}

function handleReaction(ctx, event) {
  if (event.reaction !== "white_check_mark" || !event.item || event.user === ctx.self.user_id) return;
  const channel = event.item.channel;
  for (const project of projectsFor(ctx, channel)) {
    const role = project.settings.members[event.user];
    if (!role) continue;
    const id = recordAt(project, channel, event.item.ts);
    const record = id ? store.findRecord(project.where, id) : null;
    if (!record || record.kind !== "todo") continue;
    const log = store.readLog(project.where, record.group);
    if (log.some((r) => r.kind === "done" && r.target === id)) continue;
    store.writeRecord(project.where, { group: record.group, kind: "done", from: role, target: id, origin: "slack" });
  }
}

function projectsFor(ctx, channel) {
  return ctx.projects.filter((project) => project.channelGroups.has(channel));
}

async function handleEvent(ctx, event) {
  if (!event) return;
  ctx.stats.last_event = store.isoLocal(new Date());
  if (event.type === "reaction_added") {
    handleReaction(ctx, event);
    return;
  }
  if (event.type !== "message") return;
  const channel = event.channel;
  if (!projectsFor(ctx, channel).length) return;
  switch (event.subtype) {
    case "message_changed":
      handleChanged(ctx, channel, event);
      break;
    case "message_deleted":
      handleDeleted(ctx, channel, event);
      break;
    case undefined:
    case "file_share":
    case "thread_broadcast":
    case "bot_message":
      if (event.bot_id || event.subtype === "bot_message") await handleBotMessage(ctx, channel, event);
      else handleHumanMessage(ctx, channel, event);
      break;
    default:
      break; // channel_join and the like carry nothing for the chat
  }
  for (const project of projectsFor(ctx, channel)) noteSeen(project, channel, event.ts);
}

// --- catch-up -------------------------------------------------------------------

function seenFile(project, channel) {
  return path.join(project.where.root, "bridge", "seen", `${channel}.json`);
}

function lastSeen(project, channel) {
  return store.readJsonFile(seenFile(project, channel)).ts || null;
}

function noteSeen(project, channel, ts) {
  if (!ts) return;
  const current = lastSeen(project, channel);
  if (current && Number(current) >= Number(ts)) return;
  store.writeJsonAtomic(project.where, seenFile(project, channel), { ts });
}

// Pages each mapped channel's history (and threads with new replies) from the
// last ts this machine processed, oldest first, through the same handlers as
// live events. Internal apps keep the higher history limits (design F2).
async function catchUp(ctx) {
  const channels = new Set(ctx.projects.flatMap((project) => [...project.channelGroups.keys()]));
  for (const channel of channels) {
    const seen = projectsFor(ctx, channel).map((project) => lastSeen(project, channel));
    const oldest = seen.some((ts) => !ts) ? null : seen.reduce((a, b) => (Number(a) < Number(b) ? a : b));
    const messages = [];
    let cursor = null;
    do {
      const page = await slack.callWithRetry("conversations.history", {
        channel, oldest: oldest || undefined, include_all_metadata: true, limit: 200, cursor: cursor || undefined,
      }, ctx.token);
      messages.push(...(page.messages || []));
      cursor = page.response_metadata && page.response_metadata.next_cursor;
    } while (cursor);
    for (const message of messages.reverse()) {
      await handleEvent(ctx, { type: "message", channel, ...message });
      if (message.reply_count && (!oldest || Number(message.latest_reply || 0) > Number(oldest))) {
        const replies = await slack.callWithRetry("conversations.replies", {
          channel, ts: message.ts, oldest: oldest || undefined, include_all_metadata: true,
        }, ctx.token);
        for (const reply of replies.messages || []) {
          if (reply.ts !== message.ts) await handleEvent(ctx, { type: "message", channel, ...reply });
        }
      }
    }
  }
}

// --- the running process --------------------------------------------------------

function statusFile() {
  return path.join(keelHome(), "chat", "bridge", "status.json");
}

function machineName() {
  return (process.env.KEEL_CHAT_MACHINE || os.hostname().split(".")[0] || "this-machine").trim();
}

function writeStatus(ctx) {
  const status = {
    pid: process.pid,
    machine: machineName(),
    connected: Boolean(ctx.connected),
    projects: ctx.projects.map((project) => project.where.worktree),
    last_event: ctx.stats.last_event,
    ignored: ctx.stats.ignored,
    unposted: unpostedCount(ctx.projects),
    updated: store.isoLocal(new Date()),
  };
  const file = statusFile();
  try {
    fs.mkdirSync(path.dirname(file), { recursive: true });
    const temp = `${file}.${process.pid}.tmp`;
    fs.writeFileSync(temp, `${JSON.stringify(status, null, 2)}\n`);
    fs.renameSync(temp, file);
  } catch {
    // Status is for people; failing to write it must not stop the relay.
  }
}

function readStatus() {
  let status = {};
  try {
    status = JSON.parse(fs.readFileSync(statusFile(), "utf8"));
  } catch {
    return { running: false };
  }
  let running = false;
  try {
    process.kill(status.pid, 0);
    running = true;
  } catch {
    running = false;
  }
  return { ...status, running, connected: running && Boolean(status.connected) };
}

function fullStatus() {
  const status = readStatus();
  const until = lifecycle.pausedUntil();
  return {
    installed: lifecycle.installed(),
    running: false,
    connected: false,
    projects: [],
    last_event: null,
    ignored: 0,
    unposted: 0,
    ...status,
    paused: Boolean(until),
    paused_until: until ? new Date(until).toISOString() : null,
  };
}

function prepareProjects() {
  const projects = servedProjects();
  for (const project of projects) {
    project.channelGroups = new Map();
    for (const [group, channel] of Object.entries(project.settings.channels)) {
      if (!project.channelGroups.has(channel)) project.channelGroups.set(channel, group);
    }
    buildTsIndex(project);
  }
  return projects;
}

async function createContext(log, { needApp }) {
  requireWebSocket();
  const { bot, app } = lifecycle.tokens();
  if (needApp && !app) throw lifecycle.missingTokens("app-level token");
  if (!bot) throw lifecycle.missingTokens("bot token");
  const ctx = {
    log,
    token: bot,
    appToken: app,
    projects: prepareProjects(),
    stats: { ignored: 0, last_event: null },
    connected: false,
    stopping: false,
    self: {},
  };
  const auth = await slack.callWithRetry("auth.test", {}, bot);
  ctx.self = { bot_id: auth.bot_id || null, user_id: auth.user_id || null };
  return ctx;
}

async function runOnce(log) {
  const ctx = await createContext(log, { needApp: false });
  const posted = await flushOutbound(ctx);
  writeStatus(ctx);
  log(`Bridge pass done: ${ctx.projects.length} project${ctx.projects.length === 1 ? "" : "s"} served, ${posted} record${posted === 1 ? "" : "s"} sent.`);
  return 0;
}

// Events are handled one at a time, in arrival order, so a reply never lands
// before the message it answers.
function socketSession(ctx) {
  return new Promise((resolve) => {
    let queue = Promise.resolve();
    slack.callWithRetry("apps.connections.open", {}, ctx.appToken).then((opened) => {
      if (ctx.stopping) return resolve();
      const socket = new WebSocket(opened.url);
      ctx.socket = socket;
      socket.onmessage = (message) => {
        let data = null;
        try {
          data = JSON.parse(typeof message.data === "string" ? message.data : String(message.data));
        } catch {
          return;
        }
        if (data.envelope_id) socket.send(JSON.stringify({ envelope_id: data.envelope_id }));
        if (data.type === "hello") {
          ctx.connected = true;
          writeStatus(ctx);
          queue = queue.then(() => catchUp(ctx)).then(() => writeStatus(ctx)).catch((error) => ctx.log(`catch-up failed: ${error.message}`));
          return;
        }
        if (data.type === "disconnect") {
          socket.close();
          return;
        }
        if (data.type === "events_api" && data.payload) {
          queue = queue
            .then(() => handleEvent(ctx, data.payload.event))
            .then(() => writeStatus(ctx))
            .catch((error) => ctx.log(`event failed: ${error.message}`));
        }
      };
      socket.onclose = () => {
        ctx.connected = false;
        ctx.socket = null;
        writeStatus(ctx);
        resolve();
      };
      socket.onerror = () => {};
    }, (error) => {
      ctx.log(`could not open a Socket Mode connection: ${error.message}`);
      resolve();
    });
  });
}

function packageVersion() {
  try {
    return JSON.parse(fs.readFileSync(path.resolve(__dirname, "..", "..", "..", "package.json"), "utf8")).version || null;
  } catch {
    return null;
  }
}

// One line to every mapped channel, so the people in it know whether this
// machine's sessions can hear them (D18).
async function announce(ctx, text) {
  const channels = new Set(ctx.projects.flatMap((project) => [...project.channelGroups.keys()]));
  for (const channel of channels) {
    try {
      await slack.call("chat.postMessage", { channel, text, username: "keel bridge", unfurl_links: false }, ctx.token);
    } catch (error) {
      ctx.log(`could not announce in ${channel}: ${error.message}`);
    }
  }
}

const RESTART_EXIT = 75;

async function run(log) {
  const ctx = await createContext(log, { needApp: true });
  const machine = machineName();
  const version = packageVersion();
  let exitCode = 0;
  let flushing = false;
  const flush = async () => {
    if (flushing || ctx.stopping || lifecycle.pausedUntil()) return;
    flushing = true;
    try {
      await flushOutbound(ctx);
    } catch (error) {
      log(`sending failed, will retry: ${error.message}`);
    } finally {
      flushing = false;
    }
  };
  let stopped = null;
  const stop = (reason) => {
    if (stopped) return stopped;
    ctx.stopping = true;
    clearInterval(timer);
    clearInterval(archiveTimer);
    stopped = (async () => {
      if (reason) await Promise.race([announce(ctx, `:red_circle: ${machine} bridge stopped${reason === "signal" ? "" : ` (${reason})`}; this machine's sessions will catch up when it restarts.`), slack.sleep(5000)]);
      if (ctx.socket) ctx.socket.close();
    })();
    return stopped;
  };
  // Every ten minutes while connected, each project with archiving on is
  // synced to its keel-chat branch (D19).
  const archiveTimer = setInterval(() => {
    if (!ctx.connected || ctx.stopping) return;
    const archive = require("./archive");
    for (const project of ctx.projects) {
      if (!archive.archiveSettings(project.where.worktree).automatic) continue;
      try {
        const result = archive.sync(project.where);
        if (result.refused) log(`${project.where.project}: ${result.refused}`);
      } catch (error) {
        log(`${project.where.project}: archive sync failed: ${error.message}`);
      }
    }
  }, 10 * 60 * 1000);
  archiveTimer.unref();
  // Each second: honor a pause, notice a Keel upgrade, and send what is new.
  const timer = setInterval(() => {
    const current = packageVersion();
    if (version && current && current !== version) {
      log(`Keel changed from ${version} to ${current}; exiting so launchd restarts the bridge on the new version.`);
      exitCode = RESTART_EXIT;
      stop(`restarting for Keel ${current}`);
      return;
    }
    if (lifecycle.pausedUntil()) {
      if (ctx.socket) ctx.socket.close();
      return;
    }
    flush();
  }, 1000);
  process.once("SIGTERM", () => stop("signal"));
  process.once("SIGINT", () => stop("signal"));
  await announce(ctx, `:large_green_circle: ${machine} bridge online, relaying ${ctx.projects.length} project${ctx.projects.length === 1 ? "" : "s"}.`);
  await flush();
  let backoff = 1000;
  while (!ctx.stopping) {
    if (lifecycle.pausedUntil()) {
      await slack.sleep(500);
      continue;
    }
    const opened = Date.now();
    await socketSession(ctx);
    if (ctx.stopping || lifecycle.pausedUntil()) continue;
    backoff = Date.now() - opened > 30000 ? 1000 : Math.min(backoff * 2, 30000);
    await slack.sleep(backoff);
  }
  if (stopped) await stopped;
  ctx.connected = false;
  writeStatus(ctx);
  return exitCode;
}

module.exports = {
  METADATA_TYPE,
  addProject,
  keelHome,
  readPosted,
  readRegistry,
  fullStatus,
  readStatus,
  removeProject,
  requireWebSocket,
  run,
  runOnce,
  servedProjects,
  writePosted,
};
