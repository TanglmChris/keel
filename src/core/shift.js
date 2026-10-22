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
const zlib = require("zlib");
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
  "keel shift await-clear --pid <pid>    wait until a desktop session's process has exited (its clear); exit 1 after --timeout-ms",
  "keel shift history [role] [--grep t]  a role's past transcripts and notes; --grep searches them (#304)",
  "                 [--show <id>]        ...or print one past shift's whole conversation, listed in claude agents or not (#397)",
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
const HOST_KEEP_AWAKE = /^(?:\S*\/)?caffeinate(?:\s|$)/;

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
    // The keep-awake the session's host runs under it (#447 D1): its parent is
    // one of the checker's ancestors, the host process itself. Not init, which
    // every orphan has for a parent and every process for an ancestor.
    if (row.ppid > 1 && own.has(row.ppid) && HOST_KEEP_AWAKE.test(row.command)) continue;
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
  // Keel reads no memory, so it cannot tell whether there is anything to
  // recheck: a reminder, never an item that holds the shift (#416 D5).
  notes.push("memory: before the hand-off note, recheck what this session wrote to memory — keep only what the next session "
    + "would get wrong without it and the repository cannot answer, and remove what this shift made untrue");
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

// The Claude Code CLI session's id and process, or null elsewhere (#357 D1).
function cliSession() {
  const id = process.env.CLAUDE_CODE_SESSION_ID;
  if (process.env.CLAUDE_CODE_ENTRYPOINT !== "cli" || !id) return null;
  const pid = Number(process.env.CLAUDE_PID);
  return { session: id, pid: Number.isInteger(pid) && pid > 1 ? pid : null };
}

// The desktop session's Claude process: the nearest ancestor whose command's
// basename is `claude`. The app's clear stops it, which is what the wake
// waits for (D1 of shift-desktop-wake-in-a-minute).
function desktopProcess() {
  const forced = Number(process.env.KEEL_SHIFT_DESKTOP_PID);
  if (process.env.KEEL_SHIFT_DESKTOP_PID && Number.isInteger(forced) && forced > 0) return forced;
  const table = processTable();
  let pid = process.ppid;
  for (let hops = 0; pid > 1 && hops < 32; hops += 1) {
    const row = table.get(pid);
    if (!row) return null;
    // The app's path holds a space ("Application Support"), so match the
    // executable's basename rather than split the command line.
    if (/(?:^|\/)claude(?:\s|$)/.test(row.command)) return pid;
    pid = row.ppid;
  }
  return null;
}

function alive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return error.code === "EPERM";
  }
}

// Blocks until the process is gone or the limit passes (D2).
function awaitClear(pid, timeoutMs) {
  const deadline = Date.now() + timeoutMs;
  const pause = new Int32Array(new SharedArrayBuffer(4));
  while (alive(pid)) {
    if (Date.now() >= deadline) return false;
    Atomics.wait(pause, 0, 0, 250);
  }
  return true;
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
  const pid = desktop ? desktopProcess() : null;
  const cli = desktop ? null : cliSession();
  // An empty slot is dropped rather than left as a blank line (#445 D3).
  const head = [
    `# Shift note: ${role || path.basename(where.worktree)}`,
    "",
    `Written ${stamp} in ${result.worktree}.`,
    desktop ? `Desktop session: ${desktop}.` : "",
    desktop && pid ? `Desktop process: ${pid}.` : "",
    cli ? `CLI session: ${cli.session}.` : "",
    cli && cli.pid ? `CLI process: ${cli.pid}.` : "",
    // A shift the role started itself; the patrol may nudge it to resume (#307 D4).
    options.wake ? "Self-initiated: this shift armed `keel shift ready --wake`." : "",
    !role ? `Started by hand: ${options.forceReason}.` : "",
    options.forceReason && result.items.length ? `\nLeft as is (${options.forceReason}):\n${result.items.map((item) => `- ${item.kind}: ${item.detail}`).join("\n")}` : "",
  ].filter((line, index) => index < 2 || line !== "").concat("").join("\n");
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
  // A CLI session cannot clear itself: its hand-over stops it once it has
  // finished and starts the next (#357 D1), so nothing waits for a clear. A
  // waiter carries it out within seconds; `keel tick` stays as the fallback (#388 D1).
  const queued = options.wake && cli ? queueHandOff(where, role, cli) : null;
  const waiter = options.wake && !queued ? armWake(where, role, since) : queued ? armHandOver(where, role) : null;
  return { role: role || null, note, closed: open.map((todo) => todo.id), waiter, queued, startedBy: role ? null : options.forceReason, desktop, pid, cli, worktree: where.worktree };
}

// --- the CLI hand-off queue (#357) --------------------------------------------------
// `ready --wake` queues an entry; the waiter it leaves and `keel tick` both carry it out (#388).

function queueFile(where, role) {
  return path.join(shiftDir(where), "queue", `${role}.json`);
}

function queueHandOff(where, role, cli) {
  const entry = { role, session: cli.session, pid: cli.pid, worktree: where.worktree, requested_at: store.isoLocal(new Date()), state: "pending" };
  store.writeJsonAtomic(where, queueFile(where, role), entry);
  return entry;
}

function handOffs(where) {
  return safeList(path.join(shiftDir(where), "queue")).filter((name) => name.endsWith(".json")).sort()
    .map((name) => store.readJsonFile(path.join(shiftDir(where), "queue", name))).filter((entry) => entry && entry.role);
}

const SHIFT_START_TEXT = (role) => `${role}: your new shift starts now. Run keel context, then keel shift resume.`;

// The old session has finished when it is gone, stopped (no status), or idle.
// `busy` and `waiting` (blocked on a question to the owner, measured) wait, and
// so does anything unknown. The job `state` labels the last message, not the
// turn: an ended turn that described pending work stayed `working` (#393).
function finished(row) {
  if (!row || !row.status) return true;
  return row.status === "idle";
}

// Every host call in the hand-over is bounded (#408 D2): a hung `claude` must
// not hold the waiter or the tick.
function hostTimeout() {
  return envMs("KEEL_SHIFT_HOST_TIMEOUT_MS", 60 * 1000);
}

// Why a host call did not answer, in words the owner can act on.
function hostTrouble(result, what) {
  if (result.error && result.error.code === "ENOENT") return "claude was not found; put it on PATH or name it with KEEL_CLAUDE";
  if (result.error && result.error.code === "ETIMEDOUT") return `\`${what}\` timed out after ${hostTimeout() / 1000} s`;
  if (result.error) return `\`${what}\` failed: ${result.error.message}`;
  return `\`${what}\` printed no session list (exit ${result.status})`;
}

function queryAgents(claude) {
  const listed = spawnSync(claude, ["agents", "--json", "--all"], { encoding: "utf8", timeout: hostTimeout() });
  try {
    const parsed = JSON.parse(listed.stdout);
    if (!listed.error && listed.status === 0 && Array.isArray(parsed)) return { rows: parsed, why: null };
  } catch {
    // not a list
  }
  return { rows: null, why: hostTrouble(listed, "claude agents --json --all") };
}

function listAgents(claude) {
  return queryAgents(claude).rows;
}

function processRunning(pid) {
  if (!Number.isInteger(pid) || pid <= 1) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch (error) {
    return error.code === "EPERM";
  }
}

// `claude stop` returns before the process exits (#395; on 2.1.304 the row
// loses its status at 0.32 s, stop returns at 0.98 s, the process exits at
// about 3.2 s), so a removal waits for the process the note recorded.
function waitForExit(pid, limitMs) {
  const deadline = Date.now() + limitMs;
  while (processRunning(pid)) {
    if (Date.now() >= deadline) return false;
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 100);
  }
  return true;
}

// Stop the old session; `claude stop` keeps its conversation. It is not resumed:
// renaming it took a resume, and a session running with Remote Control writes
// its claude.ai title back over a rename (#399 F1, F2). The new session carries
// a name of its own instead.
function retire(claude, entry, row) {
  if (row.state !== "stopped") spawnSync(claude, ["stop", row.id || entry.session.slice(0, 8)], { encoding: "utf8", timeout: hostTimeout() });
}

// The new session's name: the role and its local start time (#399 D1), which
// reaches claude.ai at creation, so each shift has a name of its own.
function sessionName(role, now = new Date()) {
  return `${role} · ${store.isoLocal(now).slice(5, 16).replace("T", " ")}`;
}

// The host's transcript of a session in `cwd`, under either spelling of the path.
function hostTranscript(cwd, session) {
  const config = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), ".claude");
  return [cwd, realpath(cwd)].map((dir) => path.join(config, "projects", dir.replace(/[^A-Za-z0-9]/g, "-"), `${session}.jsonl`))
    .find((file) => fs.existsSync(file)) || null;
}

// Keel's copy of a transcript, written now when it is missing or older (#343).
function keptCopyOf(where, role, transcript) {
  const { keptFile } = require("./chat/notice");
  const target = keptFile(where, role, transcript);
  try {
    if (!fs.existsSync(target) || fs.statSync(target).mtimeMs < fs.statSync(transcript).mtimeMs) {
      fs.mkdirSync(path.dirname(target), { recursive: true });
      const temporary = `${target}.${process.pid}.tmp`;
      fs.writeFileSync(temporary, zlib.gzipSync(fs.readFileSync(transcript)));
      fs.renameSync(temporary, target);
    }
    return target;
  } catch {
    return null;
  }
}

// After a delivered hand-over, the newest `keep` stopped background sessions in
// the role's bound worktrees stay listed; each older one is removed with
// `claude rm` once Keel's store holds its transcript (#397 D2). `claude rm`
// leaves the host's transcript (F4). Only a session with a transcript, the
// host's or Keel's copy, is a shift: one never given a prompt has neither, so
// it takes no slot and stays (#401).
function removeOldSessions(claude, where, entry, keep) {
  const bound = new Set(Object.entries(store.readJsonFile(path.join(where.root, "roles.json")))
    .filter(([, name]) => name === entry.role).map(([worktree]) => realpath(worktree)));
  const listed = listAgents(claude);
  if (!listed) return [];
  const { keptFile } = require("./chat/notice");
  const old = listed
    .filter((row) => row && row.kind === "background" && !row.status && row.cwd && bound.has(realpath(row.cwd))
      && row.sessionId && row.id !== entry.new_session)
    .map((row) => ({ row, transcript: hostTranscript(row.cwd, row.sessionId),
      kept: keptFile(where, entry.role, `${row.sessionId}.jsonl`) }))
    .filter(({ transcript, kept }) => transcript || fs.existsSync(kept))
    .sort((a, b) => (Number(b.row.startedAt) || 0) - (Number(a.row.startedAt) || 0));
  const removed = [];
  for (const { row, transcript } of old.slice(keep)) {
    // Never a session whose process still runs (#408 D1): the one just handed
    // over gets a bounded wait for the process its note recorded; any other
    // still running is left for the next hand-over.
    const handedOver = row.sessionId === entry.session;
    const pid = Number(handedOver ? entry.pid : row.pid);
    if (handedOver ? !waitForExit(pid, envMs("KEEL_SHIFT_EXIT_WAIT_MS", 15 * 1000)) : processRunning(pid)) continue;
    if (transcript && !keptCopyOf(where, entry.role, transcript)) continue;
    const gone = spawnSync(claude, ["rm", row.id || row.sessionId.slice(0, 8)], { encoding: "utf8", timeout: hostTimeout() });
    if (!gone.error && gone.status === 0) removed.push(row.id || row.sessionId.slice(0, 8));
  }
  return removed;
}

// One runner at a time per role (#388 D2): the waiter and the tick both carry
// hand-overs out, and a lock younger than two minutes is the other's.
function withHandOverLock(where, role, fn) {
  const file = path.join(shiftDir(where), "queue", `${role}.lock`);
  try {
    if (Date.now() - fs.statSync(file).mtimeMs > 2 * 60 * 1000) fs.unlinkSync(file);
  } catch {
    // no lock yet
  }
  let fd;
  try {
    fd = fs.openSync(file, "wx");
  } catch {
    return null;
  }
  try {
    return fn();
  } finally {
    fs.closeSync(fd);
    try {
      fs.unlinkSync(file);
    } catch {
      // already gone
    }
  }
}

// A failed start is tried again this many times in all (#408 D4).
const HANDOVER_ATTEMPTS = 3;

// A claimed hand-over whose runner is gone, or that has outlived the bounded
// worst case of its host calls, is settled by another runner (#408 D2).
function runnerGone(entry, now = Date.now()) {
  return !processRunning(Number(entry.runner_pid)) || !(now - Date.parse(entry.starting_at) <= 10 * 60 * 1000);
}

function actionable(entry) {
  return entry.state === "pending"
    || (entry.state === "starting" && runnerGone(entry))
    || (entry.state === "failed" && Number.isInteger(entry.attempts) && entry.attempts < HANDOVER_ATTEMPTS);
}

// The session a claimed hand-over already started, if the host lists one (#408
// D3): named for the role, in its worktree, started since the claim.
function startedFor(entry, sessions) {
  const since = Date.parse(entry.starting_at) - 5000;
  const home = realpath(entry.worktree);
  return sessions.find((row) => row && typeof row.name === "string" && row.name.startsWith(`${entry.role} · `)
    && row.sessionId !== entry.session && Number(row.startedAt) >= since && row.cwd && realpath(row.cwd) === home) || null;
}

function deliver(claude, where, entry, id, name, adopted) {
  const { readShiftDeclaration } = require("./config");
  const declared = readShiftDeclaration(entry.worktree);
  Object.assign(entry, { state: "delivered", delivered_at: store.isoLocal(new Date()), new_session: id, new_name: name });
  for (const key of ["error", "failed_at", "runner_pid"]) delete entry[key];
  if (adopted) entry.adopted = true;
  entry.removed = removeOldSessions(claude, where, entry, declared.keepOldSessions);
  if (declared.message) entry.notice = declared.message;
  store.writeJsonAtomic(where, queueFile(where, entry.role), entry);
  return entry;
}

// Under the role's lock, decide what one entry needs, and claim it as
// `starting` before any host call, so the lock is held only for this (#408 D1):
// a runner acts only on an entry nobody has claimed.
function claim(where, queued, sessions) {
  return withHandOverLock(where, queued.role, () => {
    const entry = store.readJsonFile(queueFile(where, queued.role));
    if (!entry || !actionable(entry)) return null;
    const row = sessions.find((item) => item && item.sessionId === entry.session);
    if (entry.waiting_on) {
      delete entry.waiting_on;
      store.writeJsonAtomic(where, queueFile(where, entry.role), entry);
    }
    if (entry.state === "starting") {
      const started = startedFor(entry, sessions);
      if (started) return { entry, adopt: started };
      Object.assign(entry, { state: "failed", failed_at: store.isoLocal(new Date()), error: "the hand-over runner stopped before the new session started" });
      store.writeJsonAtomic(where, queueFile(where, entry.role), entry);
      if (entry.attempts >= HANDOVER_ATTEMPTS) return null;
    }
    if (entry.state === "failed") {
      // Someone resumed the old session: it is theirs now (#408 D4).
      if (row && row.status) {
        Object.assign(entry, { attempts: HANDOVER_ATTEMPTS, error: `${entry.error}; not retried: the old session is running again` });
        store.writeJsonAtomic(where, queueFile(where, entry.role), entry);
        return null;
      }
      const started = entry.starting_at && startedFor(entry, sessions);
      if (started) return { entry, adopt: started };
    } else if (!finished(row)) {
      return null;
    }
    Object.assign(entry, { state: "starting", runner_pid: process.pid, starting_at: store.isoLocal(new Date()), attempts: (entry.attempts || 0) + 1 });
    store.writeJsonAtomic(where, queueFile(where, entry.role), entry);
    return { entry, row };
  });
}

// One step of the waker (#357 D2): a busy or unfinished old session waits; a
// finished or gone one is retired (stopped) and a new session starts. A claim
// left by a runner that died is settled, and a failed start is tried again
// (#408). `only` limits the step to one role (the waiter's).
function handOver(where, only = null) {
  const { readShiftDeclaration } = require("./config");
  const claude = process.env.KEEL_CLAUDE || "claude";
  const queuedEntries = handOffs(where).filter((entry) => actionable(entry) && (!only || entry.role === only));
  if (!queuedEntries.length) return [];
  const queried = queryAgents(claude);
  const sessions = queried.rows;
  // A listing that failed says nothing about the old session: wait for the next
  // step, and say why on the entry, which status and the patrol show (#408 D2).
  if (!sessions) {
    for (const queuedEntry of queuedEntries) {
      const entry = store.readJsonFile(queueFile(where, queuedEntry.role));
      if (entry && entry.state === "pending" && entry.waiting_on !== queried.why) {
        store.writeJsonAtomic(where, queueFile(where, entry.role), { ...entry, waiting_on: queried.why });
      }
    }
    return [];
  }
  const done = [];
  for (const queued of queuedEntries) {
    const claimed = claim(where, queued, sessions);
    if (!claimed) continue;
    const { entry, row, adopt } = claimed;
    if (adopt) {
      done.push(deliver(claude, where, entry, adopt.id || adopt.sessionId.slice(0, 8), adopt.name, true));
      continue;
    }
    // `stop`, `attach` and `logs` take the 8-character job id, not the full
    // session id (`No job matching`, measured 2026-10-19).
    if (row) retire(claude, entry, row);
    const mode = readShiftDeclaration(entry.worktree).permissionMode;
    const name = sessionName(entry.role);
    const started = spawnSync(claude, ["--bg", "-n", name, "--permission-mode", mode, SHIFT_START_TEXT(entry.role)], {
      cwd: entry.worktree, encoding: "utf8", timeout: hostTimeout(),
    });
    const output = `${started.stdout || ""}`;
    if (!started.error && started.status === 0) {
      const id = (output.match(/backgrounded\s*·\s*(\S+)/) || [])[1] || null;
      done.push(deliver(claude, where, entry, id, name, false));
    } else {
      const reason = started.error ? hostTrouble(started, "claude --bg") : String(started.stderr || output).trim().split(/\r?\n/).pop();
      Object.assign(entry, { state: "failed", failed_at: store.isoLocal(new Date()), error: reason || `exited ${started.status}` });
      delete entry.runner_pid;
      store.writeJsonAtomic(where, queueFile(where, entry.role), entry);
      done.push(entry);
    }
  }
  return done;
}

// `ready --wake` on the CLI leaves this waiter (#388 D1). Its working directory
// is `/`, so `check` never counts it, and its environment has none of the old
// session's `CLAUDE*` variables, which the claude it starts must not inherit.
function armHandOver(where, role) {
  const keel = path.resolve(__dirname, "..", "..", "bin", "keel.js");
  const env = Object.fromEntries(Object.entries(process.env).filter(([key]) => !key.startsWith("CLAUDE")));
  const child = spawn(process.execPath, [keel, "shift", "handover-wait", "--role", role, "--repo", where.worktree],
    { detached: true, stdio: "ignore", cwd: path.parse(where.worktree).root, env });
  child.unref();
  return child.pid;
}

function waitForHandOver(where, role) {
  const poll = envMs("KEEL_SHIFT_HANDOVER_POLL_MS", 3000);
  const deadline = Date.now() + envMs("KEEL_SHIFT_HANDOVER_TIMEOUT_MS", 2 * 60 * 60 * 1000);
  const step = () => {
    const entry = store.readJsonFile(queueFile(where, role));
    if (!entry || entry.state !== "pending" || Date.now() > deadline) return;
    handOver(where, role);
    setTimeout(step, poll);
  };
  // `ready` has just run, so the session is still finishing its turn: look first after one interval.
  setTimeout(step, poll);
}

function describeHandOff(entry) {
  const tail = entry.state === "delivered"
    ? `delivered ${entry.delivered_at} as session ${entry.new_session || "(id not printed)"}${entry.new_name ? ` "${entry.new_name}"` : ""}`
    : entry.state === "failed" ? `failed ${entry.failed_at}: ${entry.error}; ${retryNote(entry)}`
      : entry.state === "starting" ? `starting since ${entry.starting_at} (attempt ${entry.attempts} of ${HANDOVER_ATTEMPTS})`
      : entry.waiting_on ? `pending: cannot ask the host — ${entry.waiting_on}` : "pending: waits for the session to go idle";
  // An entry from before #399 recorded whether the old session's rename showed.
  const renamed = entry.state === "delivered" && "renamed" in entry ? (entry.renamed ? `; old session renamed "${entry.renamed}"` : "; rename not shown") : "";
  const removed = (entry.removed || []).length ? `; older sessions removed from \`claude agents\` (transcripts kept by Keel): ${entry.removed.join(", ")}` : "";
  const notice = entry.notice ? `; ${entry.notice}` : "";
  const own = entry.session.slice(0, 8);
  const reopen = (entry.removed || []).includes(own)
    ? `old session removed, its conversation kept: \`keel shift history ${entry.role} --show ${own}\``
    : `old session kept, reopen it with \`claude attach ${own}\``;
  return `- ${entry.role}: ${tail}${renamed}; requested ${entry.requested_at}; ${reopen}${removed}${notice}`;
}

// What follows a failed start: the tick's next attempt, or, once none is left,
// the existing way to bring the role back (#408 D5).
function retryNote(entry) {
  return Number.isInteger(entry.attempts) && entry.attempts < HANDOVER_ATTEMPTS
    ? `attempt ${entry.attempts} of ${HANDOVER_ATTEMPTS}, the tick tries again`
    : `resume the old session with \`keel chat wake now ${entry.role}\``;
}

// A failed hand-off, or one pending past 15 minutes, is the patrol's risk (#357 D4).
// `covers` limits them to the roles a scoped patrol coordinates (#434 D5).
function handOffRisks(where, now = Date.now(), covers = () => true) {
  return handOffs(where).filter((entry) => covers(entry.role)).filter((entry) => entry.state === "failed"
    || (entry.state === "pending" && now - Date.parse(entry.requested_at) > 15 * 60 * 1000))
    .map((entry) => `${entry.role}'s CLI hand-off ${entry.state}${entry.error ? `: ${entry.error}; ${retryNote(entry)}` : ` since ${entry.requested_at}`}`
      + `${entry.waiting_on ? ` (${entry.waiting_on})` : ""}; see \`keel shift status\``);
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
  return process.env.KEEL_SHIFT_WAKE_OVERDUE_MS && Number.isFinite(value) && value >= 0 ? value : 3 * 60 * 1000;
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
  // A note written on the Claude desktop app names its session: there a
  // session with no running process sees no chat record (#320 D1).
  const desktop = (fs.readFileSync(notePath(where, role), "utf8").match(/^Desktop session: (\S+?)\.$/m) || [])[1] || null;
  return { record: store.post(where, { group, text: body, refs: [REF] }), body, desktop };
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

// Notes cite `<branch> @ <sha>` and bare commit ids, which go stale between
// `ready` and `resume` (#347). Each is marked against the remote-tracking refs
// as they are: Keel fetches nothing, and says when they were last fetched.
const NOTE_PAIR = /([A-Za-z0-9][\w./-]*)\s*@\s*([0-9a-f]{7,40})\b/g;
// The first segment of a UUID — a session id — is not a commit (#445 D1).
const NOTE_SHA = /(?<![\w@/-])([0-9a-f]{7,40})\b(?!-[0-9a-f]{4}-)/g;
const looksLikeSha = (token) => /[a-f]/.test(token) && /\d/.test(token);

function remoteDefault(cwd) {
  const head = git(cwd, ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"]);
  if (head.ok && head.out) return head.out;
  for (const name of ["origin/main", "origin/master"]) {
    if (git(cwd, ["rev-parse", "--verify", "--quiet", `refs/remotes/${name}`]).ok) return name;
  }
  return null;
}

// Session ids Keel records or keeps a transcript of (#445 D2).
function knownSessionIds(where) {
  const ids = new Set();
  const names = (dir) => {
    try {
      return fs.readdirSync(dir);
    } catch {
      return [];
    }
  };
  for (const file of names(path.join(where.root, "sessions"))) ids.add(file.split(".")[0]);
  const kept = path.join(where.root, "shift", "transcripts");
  for (const role of names(kept)) for (const file of names(path.join(kept, role))) ids.add(file.split(".")[0]);
  return [...ids].filter((id) => /^[0-9a-f]{8}-/.test(id));
}

function noteCommits(cwd, text, sessions = []) {
  const seen = new Set();
  const named = [];
  // After `@` the pair already says it is a commit, so an all-digit sha counts
  // (about 2% of short shas are all digits).
  for (const match of String(text).matchAll(NOTE_PAIR)) {
    named.push({ index: match.index, branch: match[1], sha: match[2], token: `${match[1]} @ ${match[2]}` });
    seen.add(match.index + match[0].length - match[2].length);
  }
  for (const match of String(text).matchAll(NOTE_SHA)) {
    if (seen.has(match.index)) continue;
    // A bare token needs a letter and a digit, or, when it is all digits, to
    // resolve to a commit, so a date does not count; one that begins a session
    // id Keel records is that session (#445 D2).
    if (sessions.some((id) => id.startsWith(match[1]))) continue;
    const allDigits = /^\d+$/.test(match[1]);
    if (allDigits ? !git(cwd, ["rev-parse", "--verify", "--quiet", `${match[1]}^{commit}`]).ok : !looksLikeSha(match[1])) continue;
    named.push({ index: match.index, branch: null, sha: match[1], token: match[1] });
  }
  named.sort((a, b) => a.index - b.index);
  const listed = new Set();
  const base = remoteDefault(cwd);
  const commits = [];
  for (const item of named) {
    if (listed.has(item.token)) continue;
    listed.add(item.token);
    const marks = [];
    const full = git(cwd, ["rev-parse", "--verify", "--quiet", `${item.sha}^{commit}`]);
    if (!full.ok) marks.push("not found");
    else if (base && git(cwd, ["merge-base", "--is-ancestor", full.out, base]).ok) marks.push(`already in ${base}`);
    if (item.branch) {
      const tip = git(cwd, ["rev-parse", "--verify", "--quiet", `refs/remotes/origin/${item.branch}`]);
      if (!tip.ok) marks.push("branch gone");
      else if (!full.ok || tip.out !== full.out) marks.push(`branch moved: now ${tip.out.slice(0, 8)}`);
    }
    commits.push({ token: item.token, marks: marks.length ? marks : ["current"] });
  }
  return commits;
}

// A new shift starts on the branch the last one left, which `land` has
// usually merged (#446 D1): named when HEAD is behind the remote default branch
// and contained in it. Nothing is fetched.
function mergedBranch(cwd) {
  const base = remoteDefault(cwd);
  if (!base) return null;
  const head = git(cwd, ["rev-parse", "--verify", "--quiet", "HEAD"]);
  const tip = git(cwd, ["rev-parse", "--verify", "--quiet", `refs/remotes/${base}`]);
  if (!head.ok || !tip.ok || head.out === tip.out) return null;
  if (!git(cwd, ["merge-base", "--is-ancestor", head.out, tip.out]).ok) return null;
  const branch = git(cwd, ["symbolic-ref", "--quiet", "--short", "HEAD"]);
  const behind = Number(git(cwd, ["rev-list", "--count", `${head.out}..${tip.out}`]).out) || 0;
  return { branch: branch.ok ? branch.out : null, base, behind };
}

function lastFetch(cwd) {
  const file = git(cwd, ["rev-parse", "--git-path", "FETCH_HEAD"]);
  if (!file.ok) return null;
  try {
    return store.isoLocal(fs.statSync(path.resolve(cwd, file.out)).mtime);
  } catch {
    return null;
  }
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
  if (!role) return { role: null, note: history, text, told: null, commits: noteCommits(where.worktree, text, knownSessionIds(where)), merged_branch: mergedBranch(where.worktree), fetched: lastFetch(where.worktree) };
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
  return { role, note: history, text, told, waiting: role ? unstarted(where, role) : [], commits: noteCommits(where.worktree, text, knownSessionIds(where)), merged_branch: mergedBranch(where.worktree), fetched: lastFetch(where.worktree) };
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

// The speaker and text of a conversation record: Claude's `{type, message}`,
// or a Codex rollout's `{type: "response_item", payload: {type: "message"}}`
// (#343). Anything else is not conversation.
function conversationLine(record) {
  if (!record) return null;
  if (record.type === "user" || record.type === "assistant") return { speaker: record.type, text: transcriptText(record) };
  const payload = record.type === "response_item" ? record.payload : null;
  if (payload && payload.type === "message" && (payload.role === "user" || payload.role === "assistant")) {
    const parts = Array.isArray(payload.content) ? payload.content : [];
    const text = parts.filter((part) => part && typeof part.text === "string").map((part) => part.text).join("\n");
    return { speaker: payload.role, text };
  }
  return null;
}

// A transcript's text, from the host's file or Keel's gzip copy of it.
function readTranscript(file) {
  const bytes = fs.readFileSync(file);
  return (file.endsWith(".gz") ? zlib.gunzipSync(bytes) : bytes).toString("utf8");
}

function transcriptText(record) {
  const content = record && record.message ? record.message.content : null;
  if (typeof content === "string") return content;
  if (Array.isArray(content)) return content.filter((part) => part && part.type === "text").map((part) => part.text).join("\n");
  return "";
}

function grepTranscript(file, needle, limit = 3) {
  const hits = [];
  const lower = needle.toLowerCase();
  for (const line of readTranscript(file).split("\n")) {
    if (!line.trim()) continue;
    let record;
    try {
      record = JSON.parse(line);
    } catch {
      continue;
    }
    const said = conversationLine(record);
    if (!said) continue;
    const text = said.text;
    const at = text.toLowerCase().indexOf(lower);
    if (at < 0) continue;
    const from = Math.max(0, at - 60);
    const snippet = text.slice(from, at + needle.length + 60).replace(/\s+/g, " ");
    const hit = { timestamp: record.timestamp || null, speaker: said.speaker, snippet: `${from ? "…" : ""}${snippet}…` };
    // A transcript can hold the same message twice; report it once.
    if (hits.some((seen) => seen.timestamp === hit.timestamp && seen.snippet === hit.snippet)) continue;
    hits.push(hit);
    if (hits.length >= limit) break;
  }
  return hits;
}

// Transcripts Claude already keeps for a worktree (#304 D6, F5): its project
// directory is the cwd with every non-alphanumeric character turned into `-`.
// `wanted` is asked before a file is read, so a caller can skip the parse.
function claudeTranscripts(worktree, wanted = () => true) {
  const config = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), ".claude");
  const found = [];
  for (const cwd of new Set([worktree, realpath(worktree)])) {
    const dir = path.join(config, "projects", cwd.replace(/[^A-Za-z0-9]/g, "-"));
    for (const name of safeList(dir)) {
      if (!name.endsWith(".jsonl")) continue;
      const file = path.join(dir, name);
      if (!wanted(file)) continue;
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

// The Claude transcripts of every worktree bound to `role`, scheduled runs left out.
function foundTranscripts(where, role, wanted) {
  const bound = Object.entries(store.readJsonFile(path.join(where.root, "roles.json")))
    .filter(([, name]) => name === role).map(([worktree]) => worktree);
  return bound.flatMap((worktree) => claudeTranscripts(worktree, wanted));
}

function history(where, named, grep) {
  const role = named || store.currentRole(where);
  if (!role) throw new ShiftError("keel shift history needs a role: name it, or run it in a worktree bound to one.");
  store.checkName(role, "Role");
  const file = path.join(shiftDir(where), "segments", `${role}.json`);
  const stored = fs.existsSync(file) ? store.readJsonFile(file).segments : [];
  const recorded = Array.isArray(stored) ? stored : [];
  const known = new Set(recorded.map((segment) => segment.transcript));
  const earlier = foundTranscripts(where, role).filter((segment) => !known.has(segment.transcript));
  const { keptFile } = require("./chat/notice");
  // A found segment has no record to name its copy, so the kept path is looked at directly (#361).
  const keptCopy = (segment) => [segment.kept, keptFile(where, role, segment.transcript)]
    .find((file) => file && fs.existsSync(file)) || null;
  const seen = new Set();
  // Newest first; the sort is stable, so segments recorded in the same second keep their order.
  const segments = [...recorded.slice().reverse(), ...earlier]
    .filter((segment) => !seen.has(segment.transcript) && seen.add(segment.transcript))
    .sort((a, b) => Date.parse(b.started) - Date.parse(a.started))
    .map((segment) => ({
      ...segment,
      exists: fs.existsSync(segment.transcript),
      kept: keptCopy(segment),
    }));
  const notes = safeList(path.join(shiftDir(where), "history"))
    .filter((name) => name.startsWith(`${role}-`) && name.endsWith(".md"))
    .sort().reverse().map((name) => path.join(shiftDir(where), "history", name));
  if (grep) {
    for (const segment of segments) {
      const source = segment.exists ? segment.transcript : segment.kept;
      segment.matches = source ? grepTranscript(source, grep) : [];
    }
  }
  return { role, segments, notes };
}

// One past shift in full (#397 D3): the segment whose transcript name starts
// with `id`, read from the host's file or Keel's kept copy, every conversation
// record in file order with tool calls and results, nothing cut.
function showSegment(where, named, id) {
  const wanted = String(id || "").trim();
  if (!wanted) throw new ShiftError("keel shift history --show needs a session id or its first 8 characters.");
  const { role, segments } = history(where, named, null);
  const matches = segments.filter((segment) => path.basename(segment.transcript).startsWith(wanted));
  if (!matches.length) throw new ShiftError(`no segment of ${role} matches ${JSON.stringify(wanted)}; \`keel shift history ${role}\` lists them.`);
  if (matches.length > 1) {
    throw new ShiftError(`${matches.length} segments of ${role} match ${JSON.stringify(wanted)}: ${matches.map((segment) => path.basename(segment.transcript)).join(", ")}.`);
  }
  const segment = matches[0];
  const source = segment.exists ? segment.transcript : segment.kept;
  if (!source) throw new ShiftError(`${segment.transcript} is gone and Keel kept no copy of it.`);
  const entries = [];
  for (const line of readTranscript(source).split("\n")) {
    if (!line.trim()) continue;
    let record;
    try {
      record = JSON.parse(line);
    } catch {
      continue;
    }
    entries.push(...shownEntries(record));
  }
  return { role, transcript: segment.transcript, source, started: segment.started, ended: segment.ended || null, entries };
}

function shownEntries(record) {
  const at = record.timestamp || null;
  const content = record.message ? record.message.content : null;
  if ((record.type === "user" || record.type === "assistant") && Array.isArray(content)) {
    const shown = [];
    for (const part of content) {
      if (!part) continue;
      if (part.type === "text" && part.text) shown.push({ at, speaker: record.type, text: part.text });
      else if (part.type === "tool_use") shown.push({ at, speaker: `tool ${part.name}`, text: JSON.stringify(part.input) });
      else if (part.type === "tool_result") {
        const text = typeof part.content === "string" ? part.content
          : Array.isArray(part.content) ? part.content.filter((item) => item && item.type === "text").map((item) => item.text).join("\n") : "";
        shown.push({ at, speaker: "result", text });
      }
    }
    return shown;
  }
  const said = conversationLine(record);
  return said && said.text ? [{ at, speaker: said.speaker, text: said.text }] : [];
}

function renderShown(shown) {
  const head = `${shown.started} → ${shown.ended || "now"}  ${shown.transcript}${shown.source === shown.transcript ? "" : ` (kept: ${shown.source})`}`;
  return [head, ...shown.entries.map((entry) => `\n[${entry.at || "?"}] ${entry.speaker}:\n${entry.text}`)].join("\n");
}

function renderHistory(result, grep) {
  const lines = [];
  for (const segment of result.segments) {
    if (grep && !segment.matches.length) continue;
    lines.push(`${segment.started} → ${segment.ended || "now"}  ${segment.transcript}${segment.found ? " (found)" : ""}${segment.exists ? "" : segment.kept ? " (kept)" : " (missing)"}`);
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
  if (result.queued) {
    const own = result.cli.session.slice(0, 8);
    // Nothing kept by default (#418): the old shift is removed once Keel holds its transcript.
    const kept = require("./config").readShiftDeclaration(result.worktree).keepOldSessions > 0
      ? `its conversation is kept, \`claude attach ${own}\` reopens it`
      : `then removes it from the session list once Keel's store holds its transcript, which \`keel shift history ${result.role} --show ${own}\` prints`;
    return "This is a Claude Code CLI session, which cannot clear itself (#357). End your turn now: once this session has finished, "
      + `a waiter stops it — ${kept} — and starts a new session `
      + `named for its start, \`${result.role} · <MM-DD HH:MM>\`, in ${result.worktree} that runs \`keel shift resume\`; \`keel tick\` does the same if the waiter is gone. \`keel shift status\` shows the hand-off.`;
  }
  let last;
  if (!result.role) last = `Without a chat role nothing wakes the new session; ${result.startedBy} — tell it to run \`keel shift resume\`.`;
  else if (result.waiter && result.desktop) {
    // Nothing starts a cleared desktop session but a prompt (#319 D3). The app
    // dispatches scheduled tasks once a minute, and a wake that lands before
    // the clear gets it refused, so the wake starts at once and waits for the
    // session's process to exit — the clear — before it sends (D3 of
    // shift-desktop-wake-in-a-minute). Remote Control stays on (#324); the app's
    // auto-archive can still take the cleared session, so the wake unarchives
    // first (#326), and a send that does not deliver reaches the owner.
    const task = `keel-shift-wake-${result.role}`;
    const resumeText = `${result.role}: your new shift starts now. `
      + "Run `keel context` and `keel shift resume`, then restore Remote Control and this session's title as `keel shift resume` says.";
    last = [
      "On the Claude desktop app a clear starts no session until a prompt arrives, so the waiter alone wakes nothing (#319). "
        + "Leave Remote Control on: the clear is accepted with it on, and the app reconnects it after the clear under a new address, which a remote viewer has to open (#324). "
        + "The whole shift takes well under a minute. Do these in order, without pausing between them:",
      result.pid
        ? `1. Create the ad-hoc task \`${task}\` with the host's \`create_scheduled_task\` (or \`update_scheduled_task\` when it exists), with no \`cronExpression\` and no fire time, and \`notifyOnCompletion: false\`. Its prompt: `
          + `"Run \`keel shift await-clear --pid ${result.pid}\` with Bash. If it exits 1, the session was not cleared: send nothing, call \`PushNotification\` naming session ${result.desktop}, and start your reply with \`WAKE FAILED\`. `
          + `If it exits 0, call \`get_session\` on session \`${result.desktop}\` and, when it reports the session archived, call \`unarchive_session\` on it; `
          + `then call \`send_message\` to it with: '${resumeText}' `
          + "If that send is refused because the session is archived, unarchive it and send once more, and say which path you took. "
          + "A send result of `delivered` or `queued` is a delivered wake; any other result after that retry is a failed wake: call `PushNotification` naming the session and the result, and start your reply with `WAKE FAILED`.\" "
          + "The app's auto-archive can archive the cleared session before the wake (#326); unarchiving brings back its worktree."
        : "1. Keel found no `claude` process above this one, so nothing can wait for the clear: after the clear, type into the new session.",
      result.pid
        ? `2. Start it at once with \`run_scheduled_task\` on \`${task}\`. The run waits for this session's clear itself, so starting it first is safe.`
        : "2. There is no task to start.",
      `3. Rename this session with \`set_session_title\` (for example "${result.role} · shifted ${store.isoLocal(new Date()).slice(0, 16)}"), so it reads as between shifts until the woken session renames it back.`,
      '4. Call clear_session("self").',
      "Keel creates no task. Running unattended needs `mcp__ccd_session_mgmt__set_remote_control`, `mcp__ccd_session_mgmt__get_session`, "
        + "`mcp__ccd_session_mgmt__unarchive_session` and `mcp__scheduled-tasks__run_scheduled_task` in `permissions.allow`, "
        + "and `shift-restore` under `authorize:` in keel/config.yaml so the woken session does not stop to ask.",
      // The outgoing side's confirmation is the repository's to waive (#319).
      require("./config").readStandingAuthorization(result.worktree).scopes.has("self-shift")
        ? "Standing-authorized by `self-shift` in keel/config.yaml: take these four steps now, without asking."
        : "Declaring `self-shift` under authorize: in keel/config.yaml lets a session take these four steps without asking.",
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
    else if (arg === "--pid") options.pid = Number(argv[++index]);
    else if (arg === "--timeout-ms") options.timeoutMs = Number(argv[++index]);
    else if (arg === "--grep") options.grep = argv[++index] || "";
    else if (arg === "--show") options.show = argv[++index] || "";
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
      case "handover-wait": {
        // Internal: the detached waiter `ready --wake` spawns in a CLI session.
        if (!options.role) throw new ShiftError("keel shift handover-wait needs --role.");
        store.checkName(options.role, "Role");
        waitForHandOver(where, options.role);
        return 0;
      }
      case "start": {
        if (!rest[0]) throw new ShiftError("keel shift start needs the role.");
        const { record, body, desktop } = start(where, rest[0], rest.slice(1).join(" "));
        const posted = `(${record.id} in ${record.group})`;
        out(
          { id: record.id, group: record.group, role: rest[0], desktop },
          desktop
            ? [
              `Posted the start for ${rest[0]} ${posted}. Its note was written on the Claude desktop app, where a session with no running process sees no chat record (#320), so this alone wakes nothing.`,
              `Wake it: call \`get_session\` on \`${desktop}\`; when it reports the session archived, call \`unarchive_session\` on it; then call \`send_message\` to \`${desktop}\` with: '${body.replace(/\n/g, " ")}'`,
            ].join("\n")
            : `Woke ${rest[0]} to start its new shift ${posted}.`,
        );
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
        const patrol = readPatrolDeclaration(where.worktree, { role: result.role || null });
        const remind = Boolean(patrol.role);
        if (remind) result.patrol = { role: patrol.role, every: patrol.every, ...(patrol.hostTask ? { hostTask: patrol.hostTask } : {}), ...(patrol.runner ? { runner: patrol.runner } : {}) };
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
        const commits = (result.commits || []).length
          ? `\n\nCommits the note names, against the remote-tracking refs (not fetched; last fetch ${result.fetched || "never"}):\n`
            + result.commits.map((c) => `- ${c.token}: ${c.marks.join("; ")}`).join("\n")
          : "";
        const merged = result.merged_branch;
        const stale = merged
          ? `\n\nThis worktree is on ${merged.branch ? `\`${merged.branch}\`` : "a detached HEAD"}, already in ${merged.base} and `
            + `${merged.behind} commit${merged.behind === 1 ? "" : "s"} behind it: start new work from ${merged.base}.`
          : "";
        out(result, `${result.text.replace(/\s+$/, "")}${commits}${stale}\n\n(The note moved to ${result.note}.)${still}${remind ? `\n\n${patrolReminder(patrol)}` : ""}${remote}`);
        return 0;
      }
      case "history": {
        if (options.show !== undefined) {
          const shown = showSegment(where, rest[0] || null, options.show);
          out(shown, renderShown(shown));
          return 0;
        }
        const result = history(where, rest[0] || null, options.grep);
        out(result, renderHistory(result, options.grep));
        return options.grep && !result.segments.some((segment) => segment.matches.length) ? 1 : 0;
      }
      case "await-clear": {
        if (!Number.isInteger(options.pid) || options.pid <= 1) throw new ShiftError("keel shift await-clear needs --pid <the desktop session's process id>.");
        const limit = Number.isFinite(options.timeoutMs) && options.timeoutMs >= 0 ? options.timeoutMs : 120000;
        const cleared = awaitClear(options.pid, limit);
        out({ pid: options.pid, cleared }, cleared
          ? `cleared: process ${options.pid} has exited.`
          : `not cleared: process ${options.pid} still runs after ${limit} ms.`);
        return cleared ? 0 : 1;
      }
      case "status": {
        const rows = status(where);
        const queue = handOffs(where);
        const text = [rows.length ? rows.map(describe).join("\n") : "No shift change recorded.",
          ...(queue.length ? ["", "Hand-offs (CLI, run by `keel tick`):", ...queue.map(describeHandOff)] : [])].join("\n");
        out({ roles: rows, handOffs: queue }, text);
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

module.exports = {
  desktopProcess, foundTranscripts, handOver, handOffRisks, check, describe, runShift, shiftStatus: status, waitingFor };
