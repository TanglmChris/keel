"use strict";

// `keel chat role --rename <old> <new>` (#376). The log is never rewritten:
// `renames.json` records the identity and the store reads every role field
// through it (D1, D2). What moves is the per-role state outside the log (D5).
const fs = require("fs");
const path = require("path");
const store = require("./store");

const { ChatError } = store;

function exists(file) {
  try {
    fs.statSync(file);
    return true;
  } catch {
    return false;
  }
}

function list(dir) {
  try {
    return fs.readdirSync(dir).sort();
  } catch {
    return [];
  }
}

// Whether the store knows `role` at all: bound, a member file, a member of
// some group, or state of its own.
function known(where, role) {
  if (store.knownRoles(where).has(role)) return true;
  return ["cursors", "presence", "parked", "shift"].some((dir) => list(path.join(where.root, dir))
    .some((name) => name === role || name.startsWith(`${role}.`)));
}

function check(where, actor, old, name) {
  store.checkName(old, "Role");
  store.checkName(name, "Role");
  if (name === "keel" || old === "keel") throw new ChatError("Role name keel is reserved for Keel's own system records.");
  if (old === name) throw new ChatError(`Role ${old} cannot be renamed to itself.`);
  const renames = store.readRenames(where.root);
  if (renames[old]) throw new ChatError(`Role ${old} was already renamed to ${store.canonicalRole(where.root, old)}.`);
  if (store.canonicalRole(where.root, name) !== name) {
    throw new ChatError(`Role ${name} is a former name of ${store.canonicalRole(where.root, name)}; rename to that role instead.`);
  }
  if (!known(where, old)) throw new ChatError(`There is no role ${old} in this repository's chat.`);
  if (![old, name, store.OWNER].includes(actor)) {
    throw new ChatError(`Only a worktree bound to ${old} or ${name}, or the owner (KEEL_CHAT_ROLE=owner), can rename ${old}.`);
  }
  const bound = Object.values(store.readRoles(where.root));
  if (bound.includes(old) && bound.includes(name)) {
    throw new ChatError(`Roles ${old} and ${name} are both bound to worktrees, so a rename would merge two live roles; `
      + `rebind one of the worktrees with \`keel chat role --set\` first.`);
  }
}

function rename(where, actor, old, name) {
  check(where, actor, old, name);
  const root = where.root;
  const moved = [];
  const kept = [];

  const renames = store.readRenames(root);
  for (const [from, to] of Object.entries(renames)) if (to === old) renames[from] = name;
  renames[old] = name;
  store.writeJsonAtomic(where, path.join(root, "renames.json"), renames);

  const roles = store.readRoles(root);
  for (const [worktree, role] of Object.entries(roles)) {
    if (role !== old) continue;
    roles[worktree] = name;
    moved.push(`binding of ${worktree}`);
  }
  store.writeJsonAtomic(where, path.join(root, "roles.json"), roles);

  // Aliases join the new role's (D5).
  const former = store.readMember(root, old).aliases;
  if (exists(path.join(root, "members", `${old}.json`))) {
    const member = store.readMember(root, name);
    for (const alias of former) if (!member.aliases.includes(alias) && alias !== name) member.aliases.push(alias);
    store.writeJsonAtomic(where, path.join(root, "members", `${name}.json`), member);
    fs.rmSync(path.join(root, "members", `${old}.json`), { force: true });
    moved.push(`members/${old}.json`);
  }

  const moveFile = (from, to, edit = null) => {
    const source = path.join(root, from);
    if (!exists(source)) return;
    if (exists(path.join(root, to))) {
      kept.push(`${to} (${from} left in place)`);
      return;
    }
    fs.mkdirSync(path.dirname(path.join(root, to)), { recursive: true });
    if (edit) {
      store.writeJsonAtomic(where, path.join(root, to), edit(store.readJsonFile(source)));
      fs.rmSync(source, { force: true });
    } else {
      fs.renameSync(source, path.join(root, to));
    }
    moved.push(from);
  };
  const withRole = (value) => (value && typeof value === "object" && value.role ? { ...value, role: name } : value);

  // Cursors: the later id per group wins.
  for (const group of list(path.join(root, "cursors", old))) {
    const mine = store.readCursor(where, old, group);
    if (mine) store.advanceCursor(where, name, group, mine);
    moved.push(`cursors/${old}/${group}`);
  }
  fs.rmSync(path.join(root, "cursors", old), { recursive: true, force: true });

  moveFile(`presence/${old}.json`, `presence/${name}.json`);
  moveFile(`presence/${old}.sessions.json`, `presence/${name}.sessions.json`);
  moveFile(`parked/${old}.json`, `parked/${name}.json`, withRole);
  moveFile(`shift/${old}.md`, `shift/${name}.md`);
  moveFile(`shift/queue/${old}.json`, `shift/queue/${name}.json`, withRole);
  moveFile(`patrol/${old}.json`, `patrol/${name}.json`);
  for (const file of list(path.join(root, "shift", "history"))) {
    if (file.startsWith(`${old}-`) && /^\d/.test(file.slice(old.length + 1))) {
      moveFile(`shift/history/${file}`, `shift/history/${name}-${file.slice(old.length + 1)}`);
    }
  }
  for (const file of list(path.join(root, "shift", "transcripts", old))) {
    moveFile(`shift/transcripts/${old}/${file}`, `shift/transcripts/${name}/${file}`);
  }
  if (!list(path.join(root, "shift", "transcripts", old)).length) fs.rmSync(path.join(root, "shift", "transcripts", old), { recursive: true, force: true });

  // Segments concatenate, in start order.
  const segmentsOf = (role) => {
    const value = store.readJsonFile(path.join(root, "shift", "segments", `${role}.json`));
    return Array.isArray(value.segments) ? value.segments : null;
  };
  const oldSegments = segmentsOf(old);
  if (oldSegments) {
    const segments = [...(segmentsOf(name) || []), ...oldSegments].sort((a, b) => String(a.started).localeCompare(String(b.started)));
    store.writeJsonAtomic(where, path.join(root, "shift", "segments", `${name}.json`), { segments });
    fs.rmSync(path.join(root, "shift", "segments", `${old}.json`), { force: true });
    moved.push(`shift/segments/${old}.json`);
  }

  // The patrol log is appended to the new role's.
  const log = path.join(root, "patrol", "log", `${old}.log`);
  if (exists(log)) {
    fs.appendFileSync(path.join(root, "patrol", "log", `${name}.log`), fs.readFileSync(log));
    fs.rmSync(log, { force: true });
    moved.push(`patrol/log/${old}.log`);
  }
  const nudgesFile = path.join(root, "patrol", "nudges.json");
  const nudges = store.readJsonFile(nudgesFile);
  if (nudges && nudges[old]) {
    if (nudges[name]) kept.push(`patrol/nudges.json ${name} (${old}'s entry dropped)`);
    else {
      nudges[name] = nudges[old];
      moved.push(`patrol/nudges.json ${old}`);
    }
    delete nudges[old];
    store.writeJsonAtomic(where, nudgesFile, nudges);
  }

  // What describes the old session only is dropped.
  fs.rmSync(path.join(root, "signal", old), { force: true });
  const tickFile = path.join(root, "tick", "state.json");
  const tick = store.readJsonFile(tickFile);
  if (tick && tick.woken && tick.woken[old]) {
    delete tick.woken[old];
    store.writeJsonAtomic(where, tickFile, tick);
  }

  return { old, role: name, moved, kept, mentions: mentionsOf(where.worktree, old) };
}

// Lines of the files Keel reads but does not own that still name `old` (D6).
function mentionsOf(worktree, old) {
  const word = new RegExp(`(^|[^a-z0-9-])${old}($|[^a-z0-9-])`);
  const found = [];
  for (const relative of ["keel/config.yaml", "keel/chat.json"]) {
    let text = "";
    try {
      text = fs.readFileSync(path.join(worktree, relative), "utf8");
    } catch {
      continue;
    }
    text.split(/\r?\n/).forEach((line, index) => {
      if (word.test(line)) found.push({ file: relative, line: index + 1, text: line.trim() });
    });
  }
  return found;
}

function render(result) {
  const lines = [`Renamed role ${result.old} to ${result.role}: the chat now reads ${result.old} as ${result.role}, and @${result.old} mentions it.`];
  if (result.moved.length) lines.push(`Moved to ${result.role}: ${result.moved.join(", ")}.`);
  if (result.kept.length) lines.push(`Kept ${result.role}'s own: ${result.kept.join(", ")}.`);
  if (result.mentions.length) {
    lines.push(`Still naming ${result.old}; Keel does not edit these, so update them by hand:`);
    for (const m of result.mentions) lines.push(`  ${m.file}:${m.line}: ${m.text}`);
  }
  return lines.join("\n");
}

module.exports = { rename, render };
