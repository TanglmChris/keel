"use strict";

// One-time migration of the 5.83 mailbox (issue #180) into chat direct groups
// (issue #187, design D7). Runs at the first `keel chat` or `keel mail`
// command in a repository whose `<git common dir>/keel-mailbox/` exists.
//
// Each 5.83 message becomes a `message` record in `dm-<from>--<to>`, keeping
// its original time; mail under `new/` stays unread for the recipient, mail
// under `done/` is read; `roles.json` bindings carry over. The old directory
// is renamed, never deleted, so nothing a user had is lost.
//
// Two processes may start at once. The first rename — `keel-mailbox` to a
// per-process staging name — is atomic, so exactly one of them migrates and
// the other finds nothing to do.

const fs = require("fs");
const path = require("path");
const store = require("./store");

function parseOld(text) {
  const match = text.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!match) return null;
  const message = { refs: [] };
  let inRefs = false;
  for (const line of match[1].split("\n")) {
    const item = line.match(/^\s+-\s+(.*)$/);
    if (inRefs && item) {
      message.refs.push(unquote(item[1]));
      continue;
    }
    inRefs = false;
    const field = line.match(/^([a-z_]+):\s?(.*)$/);
    if (!field) continue;
    if (field[1] === "refs") {
      inRefs = true;
      continue;
    }
    message[field[1]] = unquote(field[2]);
  }
  message.body = match[2].replace(/^\n/, "").replace(/\s+$/, "");
  return message;
}

function unquote(raw) {
  const text = raw.trim();
  if (!text.startsWith('"')) return text;
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

function readOld(staging) {
  const messages = [];
  let roles = [];
  try {
    roles = fs.readdirSync(staging).filter((name) => /^[a-z0-9][a-z0-9-]{0,31}$/.test(name));
  } catch {
    return messages;
  }
  for (const role of roles) {
    for (const state of ["new", "done"]) {
      const dir = path.join(staging, role, state);
      let names = [];
      try {
        names = fs.readdirSync(dir).filter((name) => name.endsWith(".md"));
      } catch {
        continue;
      }
      for (const name of names) {
        let parsed = null;
        try {
          parsed = parseOld(fs.readFileSync(path.join(dir, name), "utf8"));
        } catch {
          continue;
        }
        const date = parsed ? new Date(Date.parse(parsed.created)) : null;
        if (!parsed || !parsed.from || !date || Number.isNaN(date.getTime())) continue;
        messages.push({ ...parsed, to: parsed.to || role, read: state === "done", date });
      }
    }
  }
  return messages.sort((a, b) => a.date - b.date);
}

function migrateIfNeeded(where) {
  const old = path.join(where.common, "keel-mailbox");
  if (!fs.existsSync(old)) return null;
  const staging = path.join(where.common, `keel-mailbox.migrating-${process.pid}`);
  try {
    fs.renameSync(old, staging);
  } catch {
    return null; // Another process is migrating it.
  }

  const roles = store.readJsonFile(path.join(staging, "roles.json"));
  const current = store.readJsonFile(path.join(where.root, "roles.json"));
  const merged = { ...roles, ...current };
  if (Object.keys(merged).length) store.writeRoles(where, merged);

  const messages = readOld(staging);
  const ids = new Map();
  const lastRead = new Map(); // `${group}\t${role}` -> id of the last read message before any unread
  const blocked = new Set();
  for (const message of messages) {
    if (message.from === message.to) continue;
    const group = store.directName(message.from, message.to);
    if (!store.groupState(store.readLog(where, group)).exists) {
      const before = new Date(message.date.getTime() - 1);
      for (const member of [message.from, message.to]) {
        store.writeRecord(where, { group, kind: "join", from: message.from, target: member }, before);
      }
    }
    const text = message.subject ? `${message.subject}\n\n${message.body}` : message.body;
    const record = store.writeRecord(where, {
      group,
      kind: "message",
      from: message.from,
      reply_to: ids.get(message.reply_to) || null,
      refs: [...message.refs, `mail:${message.id}`],
      origin: "migrated",
      text,
    }, message.date);
    ids.set(message.id, record.id);
    const key = `${group}\t${message.to}`;
    if (!message.read) blocked.add(key);
    else if (!blocked.has(key)) lastRead.set(key, record.id);
  }
  for (const [key, id] of lastRead) {
    const [group, role] = key.split("\t");
    store.advanceCursor(where, role, group, id);
  }

  const stamp = new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d+Z$/, "Z");
  fs.renameSync(staging, path.join(where.common, `keel-mailbox.migrated-${stamp}`));
  return { messages: messages.length };
}

module.exports = {
  migrateIfNeeded,
};
