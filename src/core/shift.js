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
const { spawn, spawnSync } = require("child_process");
const store = require("./chat/store");
const locks = require("./lock");

const REF = "keel-shift";
const USAGE = [
  "keel shift request <role> [text]      ask a role to change shift (wakes it)",
  "keel shift check [--json]             readiness check of this worktree; exit 1 if anything is loose",
  "keel shift ready [text | --file f]    store the shift note, close the request (refused while loose)",
  "                 [--role r]           ...under role r, from a worktree bound to no role (#290)",
  "                 [--force-reason r]   ...or state why the loose ends may stay",
  "                 [--wake]             ...and wake the role's next session once it starts (#293)",
  "keel shift start <role> [text]        wake the cleared role to resume (once its note waits)",
  "keel shift resume [--role r] [--json] print and consume this role's note (--role: from an unbound worktree)",
  "keel shift status [--json]            each role's shift state",
  "keel shift history [role] [--grep t]  a role's past transcripts and notes; --grep searches them (#304)",
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

// A worktree with no chat role keeps its note per worktree (shift-without-role
// D1): its directory name for a reader, a hash of its path for uniqueness.
function worktreeNotePath(where) {
  const id = require("crypto").createHash("sha256").update(where.worktree).digest("hex").slice(0, 8);
  return path.join(shiftDir(where), "worktree", `${path.basename(where.worktree)}-${id}.md`);
}

// Where this worktree's note is written: the role's when it has one.
function ownNotePath(where, role) {
  return role ? notePath(where, role) : worktreeNotePath(where);
}

// The note waiting for this worktree: its role's first, then its own.
function waitingNote(where, role) {
  for (const file of [role ? notePath(where, role) : null, worktreeNotePath(where)]) {
    if (file && fs.existsSync(file)) return file;
  }
  return null;
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
  const result = spawnSync("ps", ["-axo", "pid=,ppid=,pgid=,etime=,command="], { encoding: "utf8" });
  const table = new Map();
  for (const line of String(result.stdout || "").split("\n")) {
    const match = line.match(/^\s*(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(.*)$/);
    if (match) table.set(Number(match[1]), { pid: Number(match[1]), ppid: Number(match[2]), pgid: Number(match[3]), elapsed: match[4], command: match[5] });
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
  // The checking process and its ancestors are the session doing the check,
  // and its process group is the command line it runs in (`… | head`).
  const own = new Set();
  for (let pid = process.pid; pid && !own.has(pid); pid = (table.get(pid) || {}).ppid) own.add(pid);
  const group = (table.get(process.pid) || {}).pgid;
  const found = [];
  for (const [pid, cwd] of processDirectories()) {
    if (own.has(pid) || !inside(realpath(cwd), worktree)) continue;
    const row = table.get(pid);
    if (!row || row.pgid === group || IDLE_SHELL.test(row.command)) continue;
    found.push(row);
  }
  return found.sort((a, b) => a.pid - b.pid);
}

function temporaryRoots() {
  return [...new Set([os.tmpdir(), "/tmp", "/private/tmp", "/var/folders", "/private/var/folders"].map(realpath))];
}

// Linked worktrees under a temporary directory, split by owner
// (shift-temp-owner D1): one in a Claude scratchpad of a session started in
// this worktree is this worktree's; any other is someone else's, or unknown.
function temporaryWorktrees(where) {
  const listed = git(where.worktree, ["worktree", "list", "--porcelain"]);
  if (!listed.ok) return { own: [], other: [] };
  const trees = listed.out.split("\n").filter((line) => line.startsWith("worktree ")).map((line) => realpath(line.slice(9)));
  const main = trees[0];
  const roots = temporaryRoots();
  const slug = where.worktree.replace(/[^A-Za-z0-9]/g, "-");
  const own = [];
  const other = [];
  for (const tree of trees) {
    if (tree === main || tree === where.worktree || !roots.some((root) => inside(tree, root))) continue;
    const scratch = tree.match(/[\\/]claude-\d+[\\/]([^\\/]+)[\\/][^\\/]+[\\/]scratchpad(?:[\\/]|$)/);
    (scratch && scratch[1] === slug ? own : other).push(tree);
  }
  return { own, other };
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

  const temporary = temporaryWorktrees(where);
  for (const tree of temporary.own) items.push({ kind: "temporary-worktree", detail: tree });
  for (const tree of temporary.other) notes.push(`temporary worktree of another session, or of unknown owner, not counted: ${tree}`);

  for (const lease of locks.liveLeases(where)) {
    if (lease.worktree === where.worktree) items.push({ kind: "lock", detail: locks.describe(lease) });
  }

  if (role) {
    // A coordinator does not leave notes waiting unstarted (#289 D1): once it
    // clears, nobody is left to start them.
    for (const waiting of unstarted(where, role)) {
      items.push({
        kind: "unstarted",
        detail: `${waiting.role}: note waiting since ${waiting.since}; run \`keel shift start ${waiting.role}\` before your own shift ends`,
      });
    }
    for (const todo of store.openTodos(where, { assignee: role })) {
      if (isShift(todo)) continue;
      items.push({ kind: "open-todo", detail: `${todo.id} in ${todo.group}: ${firstLine(todo.text)}` });
    }
    for (const record of store.unread(where, role)) {
      if (isShift(record) || !store.wakes(record, role)) continue;
      // Keel's own nudges and wakes are instructions, not work left over (#307):
      // a role told to change its shift is not held back by being told.
      if (record.from === "keel-patrol" || record.from === "keel-shift") continue;
      if (record.kind === "todo" && record.assignee === role) continue;
      items.push({ kind: "unread", detail: `${record.id} in ${record.group} from ${record.from}: ${firstLine(record.text)}` });
    }
  } else {
    notes.push("this worktree has no chat role, so its chat was not checked");
  }
  return { ready: items.length === 0, worktree: where.worktree, role: role || null, items, notes };
}

// The UTC millisecond a chat record id was written at (`20261012T093944609Z-…`).
function idTime(id) {
  const m = String(id || "").match(/^(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})(\d{3})Z/);
  return m ? Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6], +m[7]) : 0;
}

// Roles whose note waits, whose latest shift request came from `coordinator`,
// and that `coordinator` has not started since the note was written.
function unstarted(where, coordinator) {
  const result = [];
  for (const file of safeList(shiftDir(where))) {
    if (!file.endsWith(".md")) continue;
    const role = file.slice(0, -3);
    if (role === coordinator || !/^[a-z0-9][a-z0-9-]{0,31}$/.test(role)) continue;
    const requests = shiftRequests(where, role);
    const latest = requests[requests.length - 1];
    if (!latest || latest.from !== coordinator) continue;
    const written = fs.statSync(path.join(shiftDir(where), file)).mtime;
    // A record's id carries its UTC time to the millisecond; `created` only to
    // the second, which lets a start from the previous round read as later
    // than a note written in the same second.
    const started = store.readLog(where, store.directName(coordinator, role)).some(
      (record) => record.from === coordinator && record.kind === "message" && isShift(record)
        && /your new shift starts now/.test(record.text || "") && idTime(record.id) > written.getTime()
    );
    if (!started) result.push({ role, since: store.isoLocal(written) });
  }
  return result.sort((a, b) => (a.role < b.role ? -1 : 1));
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
    "3. Note in the shift note any session state a clear destroys and Keel cannot see — scheduled jobs, Remote Control — so the next shift can re-create it.",
    "4. `keel shift ready \"<what you were doing, next step, what you wait on, where>\"`.",
    "5. Clear this session as `keel shift ready` says.",
    text ? `\n${text}` : "",
  ].join("\n").trim();
  return store.todo(where, { group, assignee: role, text: body, refs: [REF] });
}

function readNoteText(options) {
  if (options.file) {
    // `-` is stdin, as without --file (D1); any other failure is named (D2).
    try {
      return fs.readFileSync(options.file === "-" ? 0 : options.file, "utf8");
    } catch (error) {
      throw new ShiftError(`Cannot read the shift note from --file ${options.file}: ${error.code || error.message}.`);
    }
  }
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

// The role a note is filed under (#290 D4, D5): the worktree's, or `--role`
// when this worktree has none and that role has an open request. An unbound
// worktree refuses to file under itself while role requests are open, since
// such a note would answer none of them.
function readyRole(where, options) {
  const bound = store.currentRole(where);
  if (options.role) {
    store.checkName(options.role, "Role");
    if (bound && bound !== options.role) {
      throw new ShiftError(`This worktree is bound to role ${bound}; --role ${options.role} names another role.`);
    }
    if (!shiftRequests(where, options.role).some((r) => r.open)) {
      throw new ShiftError(`--role ${options.role}: no shift change is requested of ${options.role}, so there is no request for this note to answer.`);
    }
    return options.role;
  }
  if (!bound) {
    const open = [...new Set(shiftRequests(where).filter((r) => r.open).map((r) => r.assignee))].sort();
    if (open.length) {
      throw new ShiftError(
        `This worktree has no chat role, and shift changes are requested of ${open.join(", ")}. `
          + `If this session is one of them, run ${open.map((r) => `\`keel shift ready --role ${r} …\``).join(" or ")}; `
          + "a note filed under this worktree would answer none of the requests."
      );
    }
  }
  return bound;
}

// The Claude desktop app's session id, or null elsewhere (#319 D1). There a
// clear starts no session until a prompt arrives.
function desktopSession() {
  const id = process.env.CLAUDE_CODE_HOST_SESSION_ID;
  return process.env.CLAUDE_CODE_ENTRYPOINT === "claude-desktop" && id ? id : null;
}

function ready(where, options) {
  const role = readyRole(where, options);
  if (options.wake && !role) {
    throw new ShiftError("--wake wakes a chat role, and this worktree has none: bind one with `keel chat role --set <name>`, or name it with --role.");
  }
  // No request can name an unbound worktree, so its `ready` is a self-shift
  // that nothing wakes after the clear (#317 D1).
  if (!role && !options.forceReason) {
    throw new ShiftError(
      "This worktree has no chat role, so nothing will start the session that follows a clear: no request can name it, and --wake needs a role. "
        + "Bind one with `keel chat role --set <name>` and run `keel shift ready --wake`, or give --force-reason \"<who starts the new session>\"."
    );
  }
  const since = Date.now();
  const result = check(where, role);
  if (!result.ready && !options.forceReason) {
    throw new ShiftError(`${renderCheck(result)}\nResolve these, or give --force-reason "<why they may stay>".`);
  }
  const text = readNoteText(options).replace(/\s+$/, "");
  if (!text.trim()) throw new ShiftError("keel shift ready needs the shift note: give it as text, with --file, or on stdin.");
  const stamp = store.isoLocal(new Date());
  const desktop = desktopSession();
  const head = [
    `# Shift note: ${role || path.basename(where.worktree)}`,
    "",
    `Written ${stamp} in ${result.worktree}.`,
    desktop ? `Desktop session: ${desktop}.` : "",
    // A shift the role started itself; the patrol may nudge it to resume (#307 D4).
    options.wake ? "Self-initiated: this shift armed `keel shift ready --wake`." : "",
    !role ? `Started by hand: ${options.forceReason}.` : "",
    options.forceReason && result.items.length ? `\nLeft as is (${options.forceReason}):\n${result.items.map((item) => `- ${item.kind}: ${item.detail}`).join("\n")}` : "",
    "",
  ].join("\n");
  const note = ownNotePath(where, role);
  writeFileAtomic(note, `${head}\n${text}\n`);
  // Requests are chat records; without a role there is none to close (D2).
  const open = role ? shiftRequests(where, role).filter((r) => r.open) : [];
  const doneText = (todo) => `done — ${role} is ready for the shift change; the note waits for \`keel shift resume\`.${options.forceReason ? ` Left as is: ${options.forceReason}.` : ""}`;
  for (const todo of open) {
    if (store.currentRole(where) === role) {
      store.post(where, { group: todo.group, replyTo: todo.id, refs: [REF], text: doneText(todo) });
    } else {
      // Filed with --role from a worktree bound to no role (#290 D4): the
      // reply and the closing record are the role's own.
      store.writeRecord(where, { group: todo.group, kind: "message", from: role, reply_to: todo.id, refs: [REF], text: doneText(todo) });
      store.writeRecord(where, { group: todo.group, kind: "done", from: role, target: todo.id });
    }
  }
  const waiter = options.wake ? armWake(where, role, since) : null;
  return { role: role || null, note, closed: open.map((todo) => todo.id), waiter, startedBy: role ? null : options.forceReason, desktop, worktree: where.worktree };
}

// --- the one-shot wake (#293) -------------------------------------------------------
//
// The one exception to "Keel schedules nothing" (D7): `ready --wake` leaves a
// detached waiter that writes a single wake record once the role's next
// session has started, then exits. Its working directory is `/`, so `check`
// never counts it as this worktree's process.

const WAKE_SENDER = "keel-shift";
const WAKE_SOURCES = new Set(["clear", "startup"]);

// Zero is a valid overdue time: it flags every desktop note at once.
function overdueMs() {
  const value = Number(process.env.KEEL_SHIFT_WAKE_OVERDUE_MS);
  return process.env.KEEL_SHIFT_WAKE_OVERDUE_MS && Number.isFinite(value) && value >= 0 ? value : 15 * 60 * 1000;
}

function envMs(name, fallback) {
  const value = Number(process.env[name]);
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function armWake(where, role, since) {
  const keel = path.resolve(__dirname, "..", "..", "bin", "keel.js");
  const child = spawn(
    process.execPath,
    [keel, "shift", "wake-wait", "--role", role, "--since", String(since), "--repo", where.worktree],
    { detached: true, stdio: "ignore", cwd: path.parse(where.worktree).root },
  );
  child.unref();
  return child.pid;
}

// The role's current session start, when it is after `since` from a clear or a
// fresh start; null otherwise.
function startedSince(where, role, since) {
  const { presenceFile } = require("./chat/notice");
  const presence = store.readJsonFile(presenceFile(where, role));
  const started = Date.parse(presence.session_started || "");
  const qualifies = !Number.isNaN(started) && started >= since && WAKE_SOURCES.has(presence.session_source);
  return qualifies ? presence.session_started : null;
}

function writeWake(where, role) {
  const group = directGroup(where, WAKE_SENDER, role);
  return store.writeRecord(where, {
    group,
    kind: "message",
    from: WAKE_SENDER,
    refs: [REF],
    text: `${role}: your new shift starts now (woken by the \`keel shift ready --wake\` you ran). First run \`keel context\`, then \`keel shift resume\`.`,
  });
}

function waitForWake(where, role, since) {
  const poll = envMs("KEEL_SHIFT_WAKE_POLL_MS", 5000);
  const settle = envMs("KEEL_SHIFT_WAKE_SETTLE_MS", 15000);
  const deadline = Date.now() + envMs("KEEL_SHIFT_WAKE_TIMEOUT_MS", 2 * 60 * 60 * 1000);
  // A qualifying start must stay unchanged for `settle` (#300 D4): a host
  // run's start is reverted once its first prompt shows what it is.
  let pending = null;
  const tick = () => {
    // A note resumed by hand needs no wake; give up after the time limit.
    if (!fs.existsSync(notePath(where, role)) || Date.now() > deadline) return;
    const started = startedSince(where, role, since);
    if (!started) pending = null;
    else if (!pending || pending.value !== started) pending = { value: started, at: Date.now() };
    else if (Date.now() - pending.at >= settle) {
      writeWake(where, role);
      return;
    }
    setTimeout(tick, poll);
  };
  tick();
}

function start(where, role, text) {
  const from = requireRole(where);
  store.checkName(role, "Role");
  // A role's own start would address itself and wake nothing (#293 D4).
  if (role === from) {
    throw new ShiftError("A role does not start its own new shift; use `keel shift ready --wake`, which wakes it once the new session starts.");
  }
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

// `--role` reads a role's note from a worktree bound to no other role (#293 D5).
function resumeRole(where, named) {
  const bound = store.currentRole(where);
  if (!named) return bound;
  store.checkName(named, "Role");
  if (bound && bound !== named) {
    throw new ShiftError(`This worktree is bound to role ${bound}; --role ${named} names another role.`);
  }
  return named;
}

function resume(where, named = null) {
  const role = resumeRole(where, named);
  const note = waitingNote(where, role);
  if (!note) return { role: role || null, note: null, text: null };
  const text = fs.readFileSync(note, "utf8");
  const stamp = store.isoLocal(new Date()).replace(/[:+]/g, "");
  const history = path.join(shiftDir(where), "history", `${role || path.basename(note, ".md")}-${stamp}.md`);
  fs.mkdirSync(path.dirname(history), { recursive: true });
  fs.renameSync(note, history);
  if (!role) return { role: null, note: history, text, told: null };
  // The cold-start message has done its work once the note is read.
  for (const record of store.unread(where, role)) {
    if (isShift(record)) store.advanceCursor(where, role, record.group, record.id);
  }
  const latest = shiftRequests(where, role).pop();
  let told = null;
  if (latest && latest.from !== role) {
    const group = directGroup(where, role, latest.from);
    const text = `${role} is on shift, resumed from its shift note.`;
    told = (store.currentRole(where) === role
      ? store.post(where, { group, text, refs: [REF] })
      : store.writeRecord(where, { group, kind: "message", from: role, refs: [REF], text })).id;
  }
  return { role, note: history, text, told, waiting: role ? unstarted(where, role) : [] };
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
  const worktreeNotes = [];
  for (const [folder, prefix] of [[dir, ""], [path.join(dir, "worktree"), "worktree "]]) {
    for (const file of safeList(folder)) {
      if (!file.endsWith(".md")) continue;
      const stat = fs.statSync(path.join(folder, file));
      const row = entry(`${prefix}${file.slice(0, -3)}`);
      row.note = store.isoLocal(stat.mtime);
      // A desktop wake that never ran leaves no trace but the waiting note
      // (D2 of shift-desktop-wake-confirm).
      const desktop = fs.readFileSync(path.join(folder, file), "utf8").match(/^Desktop session: (\S+)\.$/m);
      if (desktop && Date.now() - stat.mtime.getTime() >= overdueMs()) {
        row.overdueDesktop = desktop[1];
      }
      if (prefix) {
        // The note's header names the worktree it was written in (#291 D6).
        const header = fs.readFileSync(path.join(folder, file), "utf8").match(/^Written \S+ in (.+)\.$/m);
        row.path = header ? header[1] : null;
        worktreeNotes.push({ name: file.slice(0, -3), written: stat.mtime.getTime() });
      }
    }
  }
  // A role still requested may have handed over from another worktree (#290 D6).
  for (const row of roles.values()) {
    if (row.note || !row.request || !row.request.open) continue;
    const since = Date.parse(row.request.created);
    const later = worktreeNotes.filter((n) => !Number.isNaN(since) && n.written >= since).map((n) => n.name);
    if (later.length) row.worktreeNotesSince = later;
  }
  for (const file of safeList(path.join(dir, "history"))) {
    const match = file.match(/^(.+)-(\d{4}-\d{2}-\d{2}T\d+)\.md$/);
    if (!match) continue;
    const role = entry(match[1]);
    if (!role.resumed || role.resumed < match[2]) role.resumed = match[2];
  }
  return [...roles.values()].sort((a, b) => (a.role < b.role ? -1 : 1));
}

// --- history (#304 D3, D4) -------------------------------------------------------

function transcriptText(record) {
  const content = record && record.message ? record.message.content : null;
  if (typeof content === "string") return content;
  if (Array.isArray(content)) return content.filter((part) => part && part.type === "text").map((part) => part.text).join("\n");
  return "";
}

function grepTranscript(file, needle, limit = 3) {
  const hits = [];
  const lower = needle.toLowerCase();
  for (const line of fs.readFileSync(file, "utf8").split("\n")) {
    if (!line.trim()) continue;
    let record;
    try {
      record = JSON.parse(line);
    } catch {
      continue;
    }
    if (record.type !== "user" && record.type !== "assistant") continue;
    const text = transcriptText(record);
    const at = text.toLowerCase().indexOf(lower);
    if (at < 0) continue;
    const from = Math.max(0, at - 60);
    const snippet = text.slice(from, at + needle.length + 60).replace(/\s+/g, " ");
    const hit = { timestamp: record.timestamp || null, speaker: record.type, snippet: `${from ? "…" : ""}${snippet}…` };
    // A transcript can hold the same message twice; report it once.
    if (hits.some((seen) => seen.timestamp === hit.timestamp && seen.snippet === hit.snippet)) continue;
    hits.push(hit);
    if (hits.length >= limit) break;
  }
  return hits;
}

// Transcripts Claude already keeps for a worktree (#304 D6, F5): its project
// directory is the cwd with every non-alphanumeric character turned into `-`.
function claudeTranscripts(worktree) {
  const config = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), ".claude");
  const found = [];
  for (const cwd of new Set([worktree, realpath(worktree)])) {
    const dir = path.join(config, "projects", cwd.replace(/[^A-Za-z0-9]/g, "-"));
    for (const name of safeList(dir)) {
      if (!name.endsWith(".jsonl")) continue;
      const file = path.join(dir, name);
      let first = null;
      let last = null;
      let opening = null;
      for (const line of fs.readFileSync(file, "utf8").split("\n")) {
        if (!line.trim()) continue;
        let record;
        try {
          record = JSON.parse(line);
        } catch {
          continue;
        }
        if (record.timestamp) {
          first = first || record.timestamp;
          last = record.timestamp;
        }
        if (opening === null && record.type === "user") opening = transcriptText(record);
      }
      // A host scheduled run is not the role's conversation (#300).
      if (opening && opening.trimStart().startsWith("<scheduled-task")) continue;
      if (!first) continue;
      found.push({ transcript: file, started: store.isoLocal(new Date(first)), ended: store.isoLocal(new Date(last)), found: true });
    }
  }
  return found;
}

function history(where, named, grep) {
  const role = named || store.currentRole(where);
  if (!role) throw new ShiftError("keel shift history needs a role: name it, or run it in a worktree bound to one.");
  store.checkName(role, "Role");
  const file = path.join(shiftDir(where), "segments", `${role}.json`);
  const stored = fs.existsSync(file) ? store.readJsonFile(file).segments : [];
  const recorded = Array.isArray(stored) ? stored : [];
  const known = new Set(recorded.map((segment) => segment.transcript));
  const bound = Object.entries(store.readJsonFile(path.join(where.root, "roles.json")))
    .filter(([, name]) => name === role).map(([worktree]) => worktree);
  const earlier = bound.flatMap(claudeTranscripts).filter((segment) => !known.has(segment.transcript));
  const seen = new Set();
  // Newest first; the sort is stable, so segments recorded in the same second keep their order.
  const segments = [...recorded.slice().reverse(), ...earlier]
    .filter((segment) => !seen.has(segment.transcript) && seen.add(segment.transcript))
    .sort((a, b) => Date.parse(b.started) - Date.parse(a.started))
    .map((segment) => ({ ...segment, exists: fs.existsSync(segment.transcript) }));
  const notes = safeList(path.join(shiftDir(where), "history"))
    .filter((name) => name.startsWith(`${role}-`) && name.endsWith(".md"))
    .sort().reverse().map((name) => path.join(shiftDir(where), "history", name));
  if (grep) {
    for (const segment of segments) segment.matches = segment.exists ? grepTranscript(segment.transcript, grep) : [];
  }
  return { role, segments, notes };
}

function renderHistory(result, grep) {
  const lines = [];
  for (const segment of result.segments) {
    if (grep && !segment.matches.length) continue;
    lines.push(`${segment.started} → ${segment.ended || "now"}  ${segment.transcript}${segment.found ? " (found)" : ""}${segment.exists ? "" : " (missing)"}`);
    for (const hit of segment.matches || []) lines.push(`  ${hit.timestamp || "?"} ${hit.speaker}: ${hit.snippet}`);
  }
  if (!grep) for (const note of result.notes) lines.push(`note  ${note}`);
  if (!lines.length) return grep ? `No transcript of ${result.role} mentions ${JSON.stringify(grep)}.` : `No shift history recorded for ${result.role}.`;
  return lines.join("\n");
}

function safeList(dir) {
  try {
    return fs.readdirSync(dir);
  } catch {
    return [];
  }
}

function describe(row) {
  const line = describeState(row);
  if (!row.note || !row.overdueDesktop) return line;
  return `${line}\n  desktop wake overdue: nothing has resumed it; check the wake task's run with \`list_task_runs\`, `
    + `and if it did not deliver, \`send_message\` session ${row.overdueDesktop} to run \`keel context\` and \`keel shift resume\``;
}

function describeState(row) {
  if (row.note && row.role.startsWith("worktree ")) {
    return `${row.role}: note waiting since ${row.note}; no chat role there, so tell the session in ${row.path || "that worktree"} to run \`keel shift resume\``;
  }
  // A note no request asked for is its own role's to resume (#293 D6).
  if (row.note && !row.request) {
    return `${row.role}: note waiting since ${row.note}; its own next session resumes it — woken by \`keel shift ready --wake\`, or by typing into it`;
  }
  if (row.note) return `${row.role}: note waiting since ${row.note}; another role's \`keel shift start ${row.role}\` wakes it to resume`;
  if (row.request && row.request.open) {
    const elsewhere = row.worktreeNotesSince
      ? `; a worktree note was written since (${row.worktreeNotesSince.join(", ")}) — if it is ${row.role}'s, file it with \`keel shift ready --role ${row.role}\``
      : "";
    return `${row.role}: change requested by ${row.request.from} at ${row.request.created}; not ready yet${elsewhere}`;
  }
  if (row.resumed) return `${row.role}: on shift, resumed ${row.resumed}`;
  return `${row.role}: ready was recorded without a note`;
}

// --- the command line --------------------------------------------------------------

const CLEAR_HINT = [
  "Session state a clear destroys — scheduled jobs, Remote Control — is not in Keel; if the note does not say how to re-create it, add that first.",
  "Now clear this session:",
  "- Claude desktop app: call `clear_session(\"self\")` (the owner approves it), or type /clear;",
  "- Claude Code CLI: /clear;",
  "- Codex: start a new session in this worktree.",
].join("\n");

// Who starts the new session (#293 D3): the coordinator that asked, nobody,
// or — without a chat role — the person who opens it.
function clearHint(result) {
  let last;
  if (!result.role) last = `Without a chat role nothing wakes the new session; ${result.startedBy} — tell it to run \`keel shift resume\`.`;
  else if (result.waiter && result.desktop) {
    // Nothing starts a cleared desktop session but a prompt (#319 D3). A wake
    // that fires before the clear is queued, and the app then refuses the clear
    // to keep it, so rename and clear follow the task at once. Remote Control
    // stays on: the clear is accepted with it on, and turning it off waits for
    // a person's approval (#324 D1, D2 of shift-desktop-keep-remote-control).
    last = [
      "On the Claude desktop app a clear starts no session until a prompt arrives, so the waiter alone wakes nothing (#319). "
        + "Leave Remote Control on: the clear is accepted with it on, and the app reconnects it after the clear under a new address, which a remote viewer has to open (#324). Do these in order:",
      // The app's auto-archive can take the cleared, idle session before the
      // wake, on every PR it ever had; dismissing bound PRs did not stop it, so
      // the wake unarchives first (#326 D1, D2 of shift-desktop-unarchive-wake).
      "1. Create a one-shot scheduled task with the host's `create_scheduled_task`, firing about three minutes later, "
        + `whose prompt first calls \`get_session\` on session \`${result.desktop}\` and, when it reports the session archived, calls \`unarchive_session\` on it; `
        + `then calls \`send_message\` to it with: "${result.role}: your new shift starts now. `
        + "Run `keel context` and `keel shift resume`, then restore Remote Control and this session's title as `keel shift resume` says.\" "
        + "If that send is still refused because the session is archived, it unarchives it and sends once more, and it says which path it took. "
        // The run's summary is the only trace a wake leaves, so a send that did
        // not deliver must say so there and reach the owner (D1 of
        // shift-desktop-wake-confirm).
        + "A send result of `delivered` or `queued` is a delivered wake; any other result after that retry is a failed wake: "
        + "the task then calls `PushNotification` naming the session and the result, and starts its reply with `WAKE FAILED`. "
        + "The app's auto-archive can archive the cleared session before the wake (#326); unarchiving brings back its worktree. "
        + "A task that fires before the clear gets the clear refused, so take the next two steps at once.",
      `2. Rename this session with \`set_session_title\` (for example "${result.role} · shifted ${store.isoLocal(new Date()).slice(0, 16)}"), so it reads as between shifts until the woken session renames it back.`,
      '3. Call clear_session("self").',
      "Keel creates no task. Running unattended needs `mcp__ccd_session_mgmt__set_remote_control`, `mcp__ccd_session_mgmt__get_session` "
        + "and `mcp__ccd_session_mgmt__unarchive_session` in `permissions.allow`, "
        + "and `shift-restore` under `authorize:` in keel/config.yaml so the woken session does not stop to ask.",
      // The outgoing side's confirmation is the repository's to waive (#319).
      require("./config").readStandingAuthorization(result.worktree).scopes.has("self-shift")
        ? "Standing-authorized by `self-shift` in keel/config.yaml: take these three steps now, without asking."
        : "Declaring `self-shift` under authorize: in keel/config.yaml lets a session take these three steps without asking.",
    ].join("\n");
  } else if (result.waiter) {
    last = `The wake is armed: once ${result.role}'s next session starts (after a clear or a fresh start), it gets one message to run \`keel shift resume\`. The waiter gives up after two hours.`;
  } else if (result.closed.length) last = "The coordinator's `keel shift start` then wakes the new shift.";
  else {
    last = `No request named ${result.role}, so nobody is set to start the new session: type into it, `
      + "or run `keel shift ready --wake` again with this note, which wakes it once it starts.";
  }
  const history = result.role
    ? `\nThis shift's conversation stays in its transcript; \`keel shift history ${result.role}\` finds it after the clear.`
    : "";
  return `${CLEAR_HINT}\n${last}${history}`;
}

function runShift(argv) {
  const options = { json: false, repo: process.cwd(), positionals: [], file: null, forceReason: null, role: null };
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--json") options.json = true;
    else if (arg === "--repo") options.repo = argv[++index] || "";
    else if (arg === "--file") options.file = argv[++index] || "";
    else if (arg === "--force-reason") options.forceReason = argv[++index] || "";
    else if (arg === "--role") options.role = argv[++index] || "";
    else if (arg === "--since") options.since = Number(argv[++index]);
    else if (arg === "--wake") options.wake = true;
    else if (arg === "--grep") options.grep = argv[++index] || "";
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
        const whose = result.role || "this worktree (no chat role, so no request to close)";
        const hint = clearHint(result);
        out({ ...result, clear: hint }, `Stored the shift note for ${whose} at ${result.note}${result.closed.length ? ` and closed ${result.closed.join(", ")}` : ""}.\n${hint}`);
        return 0;
      }
      case "wake-wait": {
        // Internal: the detached waiter `ready --wake` spawns.
        if (!options.role || !Number.isFinite(options.since)) throw new ShiftError("keel shift wake-wait needs --role and --since.");
        store.checkName(options.role, "Role");
        waitForWake(where, options.role, options.since);
        return 0;
      }
      case "start": {
        if (!rest[0]) throw new ShiftError("keel shift start needs the role.");
        const record = start(where, rest[0], rest.slice(1).join(" "));
        out({ id: record.id, group: record.group, role: rest[0] }, `Woke ${rest[0]} to start its new shift (${record.id} in ${record.group}).`);
        return 0;
      }
      case "resume": {
        const result = resume(where, options.role);
        if (!result.note) {
          out(result, `No shift note waits for ${result.role || "this worktree"}.`);
          return 0;
        }
        // A new shift of the patrolling role re-creates its schedule (#260).
        const { readPatrolDeclaration, patrolReminder } = require("./config");
        const patrol = readPatrolDeclaration(where.worktree);
        const remind = patrol.role && result.role === patrol.role;
        if (remind) result.patrol = { role: patrol.role, every: patrol.every, ...(patrol.hostTask ? { hostTask: patrol.hostTask } : {}) };
        // A new coordinator learns whom its previous shift left unstarted (#289 D2).
        const waiting = (result.waiting || []).map((w) => w.role);
        const still = waiting.length ? `\n\nStill waiting for \`keel shift start\`: ${waiting.join(", ")}.` : "";
        // A clear on the desktop app keeps no title (#319), and a session it
        // leaves may come back with Remote Control off (#324 D3).
        const { readStandingAuthorization } = require("./config");
        const restore = readStandingAuthorization(where.worktree).scopes.has("shift-restore");
        const remote = desktopSession() && restore
          ? "\n\nStanding-authorized by `shift-restore` in keel/config.yaml: if `get_session(\"self\")` reports Remote Control off, turn it back on with "
            + "`set_remote_control(\"self\", true)`; and rename this session back to its working title with `set_session_title`, now, without asking."
          : desktopSession()
          ? "\n\nOn the Claude desktop app a clear keeps no title and may leave Remote Control off: if `get_session(\"self\")` reports it off, turn it back on with "
            + "`set_remote_control(\"self\", true)`, and rename the session back with `set_session_title`. "
            + "Declaring `shift-restore` under authorize: in keel/config.yaml lets a woken session do this without asking."
          : "";
        out(result, `${result.text.replace(/\s+$/, "")}\n\n(The note moved to ${result.note}.)${still}${remind ? `\n\n${patrolReminder(patrol)}` : ""}${remote}`);
        return 0;
      }
      case "history": {
        const result = history(where, rest[0] || null, options.grep);
        out(result, renderHistory(result, options.grep));
        return options.grep && !result.segments.some((segment) => segment.matches.length) ? 1 : 0;
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
    if (error instanceof ShiftError || error instanceof store.ChatError || error instanceof locks.LockError) {
      process.stderr.write(`keel shift: ${error.message}\n`);
      return 1;
    }
    throw error;
  }
}

// The waiting note for a repository path, for `keel context` (D3); null when
// none waits or the path is not a repository.
function waitingFor(repo) {
  const where = store.locate(repo);
  if (!where) return null;
  const note = waitingNote(where, store.currentRole(where));
  if (!note) return null;
  return { note, since: store.isoLocal(fs.statSync(note).mtime) };
}

module.exports = { check, describe, runShift, shiftStatus: status, waitingFor };
