"use strict";

// `keel shift`: a coordinated shift change for a role's session (owner's
// decision of 2026-10-05, shift-change D1-D7). The coordinator requests it,
// the outgoing session checks for loose ends and leaves a note, clears itself,
// and the new shift resumes from the note once the coordinator starts it.
//
// Each step is a chat record in the direct group between the coordinator and
// the role, so it wakes the right session and stays reviewable. The note is
// kept in the chat store, outside every worktree, from `ready` until `resume`:
// it is transient context for a cold start, never a follow-up owner and never
// read by `keel context`.

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");
const store = require("./chat/store");

const REF = "keel-shift";
const USAGE = [
  "keel shift request <role> [text]      ask a role to change shift (wakes it)",
  "keel shift check [--json]             readiness check of this worktree; exit 1 if anything is loose",
  "keel shift ready [text | --file f]    store the shift note, close the request (refused while loose)",
  "                 [--force-reason r]   ...or state why the loose ends may stay",
  "keel shift start <role> [text]        wake the cleared role to resume (once its note waits)",
  "keel shift resume [--json]            print and consume this role's note",
  "keel shift status [--json]            each role's shift state",
  "Options: --repo <path>. See docs/shift-change.md.",
].join("\n");

class ShiftError extends Error {}

function git(cwd, args) {
  const result = spawnSync("git", args, { cwd, encoding: "utf8" });
  return { ok: result.status === 0, out: String(result.stdout || "").replace(/\s+$/, "") };
}

function realpath(file) {
  try {
    return fs.realpathSync(file);
  } catch {
    return path.resolve(file);
  }
}

function inside(child, parent) {
  return child === parent || child.startsWith(parent.endsWith(path.sep) ? parent : parent + path.sep);
}

function shiftDir(where) {
  return path.join(where.root, "shift");
}

function notePath(where, role) {
  return path.join(shiftDir(where), `${role}.md`);
}

function writeFileAtomic(file, content) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temp = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(temp, content);
  fs.renameSync(temp, file);
}

function isShift(record) {
  return (record.refs || []).includes(REF);
}

// --- the readiness check (D4) ------------------------------------------------------

// Every process: pid, parent, elapsed time, command.
function processTable() {
  const result = spawnSync("ps", ["-axo", "pid=,ppid=,etime=,command="], { encoding: "utf8" });
  const table = new Map();
  for (const line of String(result.stdout || "").split("\n")) {
    const match = line.match(/^\s*(\d+)\s+(\d+)\s+(\S+)\s+(.*)$/);
    if (match) table.set(Number(match[1]), { pid: Number(match[1]), ppid: Number(match[2]), elapsed: match[3], command: match[4] });
  }
  return table;
}

// The working directory of every process: /proc where the system has it,
// lsof otherwise.
function processDirectories() {
  const result = new Map();
  if (fs.existsSync("/proc/self/cwd")) {
    for (const entry of fs.readdirSync("/proc")) {
      if (!/^\d+$/.test(entry)) continue;
      try {
        result.set(Number(entry), fs.readlinkSync(path.join("/proc", entry, "cwd")));
      } catch {
        // Gone, or not ours to read.
      }
    }
    return result;
  }
  const listed = spawnSync("lsof", ["-a", "-d", "cwd", "-F", "pn"], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
  let pid = null;
  for (const line of String(listed.stdout || "").split("\n")) {
    if (line.startsWith("p")) pid = Number(line.slice(1));
    else if (line.startsWith("n") && pid !== null) result.set(pid, line.slice(1));
  }
  return result;
}

// An interactive shell open in the worktree, such as a terminal tab, is not
// work in progress; what it runs is, and is listed by its own entry.
const IDLE_SHELL = /^-?(?:\S*\/)?(?:zsh|bash|sh|dash|fish)(?:\s+-[il]+)*\s*$/;

function liveProcesses(worktree) {
  const table = processTable();
  // The checking process and its ancestors are the session doing the check.
  const own = new Set();
  for (let pid = process.pid; pid && !own.has(pid); pid = (table.get(pid) || {}).ppid) own.add(pid);
  const found = [];
  for (const [pid, cwd] of processDirectories()) {
    if (own.has(pid) || !inside(realpath(cwd), worktree)) continue;
    const row = table.get(pid);
    if (!row || IDLE_SHELL.test(row.command)) continue;
    found.push(row);
  }
  return found.sort((a, b) => a.pid - b.pid);
}

function temporaryRoots() {
  return [...new Set([os.tmpdir(), "/tmp", "/private/tmp", "/var/folders", "/private/var/folders"].map(realpath))];
}

function temporaryWorktrees(where) {
  const listed = git(where.worktree, ["worktree", "list", "--porcelain"]);
  if (!listed.ok) return [];
  const trees = listed.out.split("\n").filter((line) => line.startsWith("worktree ")).map((line) => realpath(line.slice(9)));
  const main = trees[0];
  const roots = temporaryRoots();
  return trees.filter((tree) => tree !== main && tree !== where.worktree && roots.some((root) => inside(tree, root)));
}

function check(where, role) {
  const items = [];
  const notes = [];
  const status = git(where.worktree, ["status", "--porcelain"]);
  for (const line of status.out.split("\n").filter(Boolean)) items.push({ kind: "uncommitted", detail: line.trim() });

  const remotes = git(where.worktree, ["remote"]).out.split("\n").filter(Boolean);
  if (!remotes.length) {
    notes.push("this repository has no remote, so unpushed commits were not checked");
  } else {
    const local = git(where.worktree, ["log", "--format=%h %s", "-n", "20", "HEAD", "--not", "--remotes"]);
    for (const line of local.out.split("\n").filter(Boolean)) items.push({ kind: "unpushed", detail: line });
  }

  if (fs.existsSync(path.join(where.worktree, "keel", "guard.json"))) {
    items.push({ kind: "task-in-progress", detail: "keel/guard.json: a task's write guard is still active; complete the task or clear the guard" });
  }

  for (const row of liveProcesses(where.worktree)) {
    items.push({ kind: "process", detail: `PID ${row.pid}, running ${row.elapsed}: ${row.command}` });
  }

  for (const tree of temporaryWorktrees(where)) items.push({ kind: "temporary-worktree", detail: tree });

  if (role) {
    for (const todo of store.openTodos(where, { assignee: role })) {
      if (isShift(todo)) continue;
      items.push({ kind: "open-todo", detail: `${todo.id} in ${todo.group}: ${firstLine(todo.text)}` });
    }
    for (const record of store.unread(where, role)) {
      if (isShift(record) || !store.wakes(record, role)) continue;
      if (record.kind === "todo" && record.assignee === role) continue;
      items.push({ kind: "unread", detail: `${record.id} in ${record.group} from ${record.from}: ${firstLine(record.text)}` });
    }
  } else {
    notes.push("this worktree has no chat role, so its chat was not checked");
  }
  return { ready: items.length === 0, worktree: where.worktree, role: role || null, items, notes };
}

function firstLine(text) {
  const line = String(text || "").split("\n")[0];
  return line.length > 100 ? `${line.slice(0, 100)}…` : line;
}

function renderCheck(result) {
  const lines = [`keel shift check: ${result.ready ? "ready" : "not ready"} (${result.worktree}${result.role ? `, role ${result.role}` : ""})`];
  for (const item of result.items) lines.push(`- ${item.kind}: ${item.detail}`);
  for (const note of result.notes) lines.push(`note: ${note}`);
  return lines.join("\n");
}

// --- the steps ---------------------------------------------------------------------

function requireRole(where) {
  return store.requireRole(where);
}

function directGroup(where, from, role) {
  const group = store.directName(from, role);
  if (!store.groupState(store.readLog(where, group)).exists) {
    store.createGroup(where, from, group, [role], { direct: true });
  }
  return group;
}

function shiftRequests(where, role = null) {
  const requests = [];
  for (const name of store.listGroupNames(where)) {
    const records = store.readLog(where, name);
    const closed = new Set(records.filter((r) => r.kind === "done").map((r) => r.target));
    for (const record of records) {
      if (record.kind !== "todo" || !isShift(record)) continue;
      if (role && record.assignee !== role) continue;
      requests.push({ ...record, open: !closed.has(record.id) });
    }
  }
  return requests.sort((a, b) => (a.id < b.id ? -1 : 1));
}

function request(where, role, text) {
  const from = requireRole(where);
  store.checkName(role, "Role");
  if (role === from) throw new ShiftError("A shift change is requested of another role, not your own.");
  const group = directGroup(where, from, role);
  const body = [
    `Shift change requested by ${from}. Wrap up, then hand over:`,
    "1. `keel shift check` until it reports ready (or decide what may stay).",
    "2. Put follow-ups where the project tracks them, and update long-lived memory you own.",
    "3. `keel shift ready \"<what you were doing, next step, what you wait on, where>\"`.",
    "4. Clear this session as `keel shift ready` says.",
    text ? `\n${text}` : "",
  ].join("\n").trim();
  return store.todo(where, { group, assignee: role, text: body, refs: [REF] });
}

function readNoteText(options) {
  if (options.file) return fs.readFileSync(options.file, "utf8");
  if (options.text) return options.text;
  if (!process.stdin.isTTY) {
    try {
      return fs.readFileSync(0, "utf8");
    } catch {
      return "";
    }
  }
  return "";
}

function ready(where, options) {
  const role = requireRole(where);
  const result = check(where, role);
  if (!result.ready && !options.forceReason) {
    throw new ShiftError(`${renderCheck(result)}\nResolve these, or give --force-reason "<why they may stay>".`);
  }
  const text = readNoteText(options).replace(/\s+$/, "");
  if (!text.trim()) throw new ShiftError("keel shift ready needs the shift note: give it as text, with --file, or on stdin.");
  const stamp = store.isoLocal(new Date());
  const head = [
    `# Shift note: ${role}`,
    "",
    `Written ${stamp} in ${result.worktree}.`,
    options.forceReason ? `\nLeft as is (${options.forceReason}):\n${result.items.map((item) => `- ${item.kind}: ${item.detail}`).join("\n")}` : "",
    "",
  ].join("\n");
  writeFileAtomic(notePath(where, role), `${head}\n${text}\n`);
  const open = shiftRequests(where, role).filter((r) => r.open);
  for (const todo of open) {
    store.post(where, {
      group: todo.group,
      replyTo: todo.id,
      refs: [REF],
      text: `done — ${role} is ready for the shift change; the note waits for \`keel shift resume\`.${options.forceReason ? ` Left as is: ${options.forceReason}.` : ""}`,
    });
  }
  return { role, note: notePath(where, role), closed: open.map((todo) => todo.id) };
}

function start(where, role, text) {
  const from = requireRole(where);
  store.checkName(role, "Role");
  if (!fs.existsSync(notePath(where, role))) {
    throw new ShiftError(`No shift note waits for ${role}: it has not run \`keel shift ready\`, or already resumed.`);
  }
  const group = directGroup(where, from, role);
  const body = [
    `${role}: your new shift starts now. First run \`keel context\`, then \`keel shift resume\` to read the note your previous shift left, then continue from it.`,
    text ? `Next: ${text}` : "",
  ].filter(Boolean).join("\n");
  return store.post(where, { group, text: body, refs: [REF] });
}

function resume(where) {
  const role = requireRole(where);
  const note = notePath(where, role);
  if (!fs.existsSync(note)) return { role, note: null, text: null };
  const text = fs.readFileSync(note, "utf8");
  const stamp = store.isoLocal(new Date()).replace(/[:+]/g, "");
  const history = path.join(shiftDir(where), "history", `${role}-${stamp}.md`);
  fs.mkdirSync(path.dirname(history), { recursive: true });
  fs.renameSync(note, history);
  // The cold-start message has done its work once the note is read.
  for (const record of store.unread(where, role)) {
    if (isShift(record)) store.advanceCursor(where, role, record.group, record.id);
  }
  const latest = shiftRequests(where, role).pop();
  let told = null;
  if (latest && latest.from !== role) {
    const group = directGroup(where, role, latest.from);
    told = store.post(where, { group, text: `${role} is on shift, resumed from its shift note.`, refs: [REF] }).id;
  }
  return { role, note: history, text, told };
}

function status(where) {
  const roles = new Map();
  const entry = (role) => {
    if (!roles.has(role)) roles.set(role, { role, request: null, note: null, resumed: null });
    return roles.get(role);
  };
  for (const todo of shiftRequests(where)) {
    entry(todo.assignee).request = { id: todo.id, from: todo.from, created: todo.created, open: todo.open };
  }
  const dir = shiftDir(where);
  for (const file of safeList(dir)) {
    if (!file.endsWith(".md")) continue;
    const stat = fs.statSync(path.join(dir, file));
    entry(file.slice(0, -3)).note = store.isoLocal(stat.mtime);
  }
  for (const file of safeList(path.join(dir, "history"))) {
    const match = file.match(/^(.+)-(\d{4}-\d{2}-\d{2}T\d+)\.md$/);
    if (!match) continue;
    const role = entry(match[1]);
    if (!role.resumed || role.resumed < match[2]) role.resumed = match[2];
  }
  return [...roles.values()].sort((a, b) => (a.role < b.role ? -1 : 1));
}

function safeList(dir) {
  try {
    return fs.readdirSync(dir);
  } catch {
    return [];
  }
}

function describe(row) {
  if (row.note) return `${row.role}: note waiting since ${row.note}; \`keel shift start ${row.role}\` wakes it to resume`;
  if (row.request && row.request.open) return `${row.role}: change requested by ${row.request.from} at ${row.request.created}; not ready yet`;
  if (row.resumed) return `${row.role}: on shift, resumed ${row.resumed}`;
  return `${row.role}: ready was recorded without a note`;
}

// --- the command line --------------------------------------------------------------

const CLEAR_HINT = [
  "Now clear this session:",
  "- Claude desktop app: call `clear_session(\"self\")` (the owner approves it), or type /clear;",
  "- Claude Code CLI: /clear;",
  "- Codex: start a new session in this worktree.",
  "The coordinator's `keel shift start` then wakes the new shift.",
].join("\n");

function runShift(argv) {
  const options = { json: false, repo: process.cwd(), positionals: [], file: null, forceReason: null };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--json") options.json = true;
    else if (arg === "--repo") options.repo = argv[++index] || "";
    else if (arg === "--file") options.file = argv[++index] || "";
    else if (arg === "--force-reason") options.forceReason = argv[++index] || "";
    else if (arg === "--help" || arg === "-h") {
      process.stdout.write(`${USAGE}\n`);
      return 0;
    } else options.positionals.push(arg);
  }
  const [action, ...rest] = options.positionals;
  const out = (value, text) => process.stdout.write(`${options.json ? JSON.stringify(value, null, 2) : text}\n`);
  try {
    const where = store.requireLocation(options.repo);
    switch (action) {
      case "request": {
        if (!rest[0]) throw new ShiftError("keel shift request needs the role.");
        const record = request(where, rest[0], rest.slice(1).join(" "));
        out({ id: record.id, group: record.group, role: rest[0] }, `Asked ${rest[0]} to change shift (${record.id} in ${record.group}).`);
        return 0;
      }
      case "check": {
        const result = check(where, store.currentRole(where));
        out(result, renderCheck(result));
        return result.ready ? 0 : 1;
      }
      case "ready": {
        const result = ready(where, { ...options, text: rest.join(" ") });
        out({ ...result, clear: CLEAR_HINT }, `Stored the shift note for ${result.role} at ${result.note}${result.closed.length ? ` and closed ${result.closed.join(", ")}` : ""}.\n${CLEAR_HINT}`);
        return 0;
      }
      case "start": {
        if (!rest[0]) throw new ShiftError("keel shift start needs the role.");
        const record = start(where, rest[0], rest.slice(1).join(" "));
        out({ id: record.id, group: record.group, role: rest[0] }, `Woke ${rest[0]} to start its new shift (${record.id} in ${record.group}).`);
        return 0;
      }
      case "resume": {
        const result = resume(where);
        if (!result.note) {
          out(result, `No shift note waits for ${result.role}.`);
          return 0;
        }
        out(result, `${result.text.replace(/\s+$/, "")}\n\n(The note moved to ${result.note}.)`);
        return 0;
      }
      case "status": {
        const rows = status(where);
        out({ roles: rows }, rows.length ? rows.map(describe).join("\n") : "No shift change recorded.");
        return 0;
      }
      default:
        process.stderr.write(`${action ? `keel shift: unknown step ${action}\n` : ""}${USAGE}\n`);
        return 2;
    }
  } catch (error) {
    if (error instanceof ShiftError || error instanceof store.ChatError) {
      process.stderr.write(`keel shift: ${error.message}\n`);
      return 1;
    }
    throw error;
  }
}

function pendingNote(where, role) {
  const note = notePath(where, role);
  if (!fs.existsSync(note)) return null;
  return store.isoLocal(fs.statSync(note).mtime);
}

module.exports = { check, pendingNote, runShift };
