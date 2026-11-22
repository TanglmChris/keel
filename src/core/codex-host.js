'use strict';
const http = require('node:http');
const crypto = require('node:crypto');
const path = require('node:path');
const os = require('node:os');
const MAX_MESSAGE = 16 * 1024 * 1024;

// The managed daemon speaks WebSocket over a Unix socket, not JSON lines.
function connect(socketPath, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const key = crypto.randomBytes(16).toString('base64');
    const pending = new Map();
    let socket, opened = false, closed = false, sequence = 0;
    let buffer = Buffer.alloc(0), fragments = [], fragmentSize = 0;
    const request = http.request({socketPath, path: '/', headers: {
      Host: 'localhost', Upgrade: 'websocket', Connection: 'Upgrade',
      'Sec-WebSocket-Key': key, 'Sec-WebSocket-Version': '13',
    }});
    const deadline = setTimeout(() => fail(Error('Codex host connection timeout')), timeout);
    function fail(error) {
      if (closed) return;
      closed = true;
      clearTimeout(deadline);
      for (const entry of pending.values()) {
        clearTimeout(entry.timer);
        entry.reject(error);
      }
      pending.clear();
      if (!opened) reject(error);
      request.destroy();
      if (socket) socket.destroy();
    }
    function send(opcode, body) {
      if (closed) throw Error('Codex host disconnected');
      if (body.length > MAX_MESSAGE) throw Error('Codex request too large');
      const mask = crypto.randomBytes(4);
      const header = Buffer.alloc(body.length < 126 ? 2 : body.length <= 65535 ? 4 : 10);
      header[0] = 128 | opcode;
      if (header.length === 2) header[1] = 128 | body.length;
      else if (header.length === 4) {header[1] = 254; header.writeUInt16BE(body.length, 2);}
      else {header[1] = 255; header.writeBigUInt64BE(BigInt(body.length), 2);}
      const payload = Buffer.from(body);
      for (let i = 0; i < payload.length; i++) payload[i] ^= mask[i % 4];
      socket.write(Buffer.concat([header, mask, payload]));
    }
    function message(body) {
      const value = JSON.parse(body.toString('utf8'));
      if (typeof value.method === 'string') return;
      const entry = pending.get(value.id);
      if (!entry) return; // Notifications are not acknowledgements of pending RPCs.
      pending.delete(value.id);
      clearTimeout(entry.timer);
      if (value.error) entry.reject(Error(value.error.message));
      else entry.resolve(value.result);
    }
    function receive(chunk) {
      buffer = Buffer.concat([buffer, chunk]);
      try {
        while (buffer.length >= 2) {
          const fin = Boolean(buffer[0] & 128), opcode = buffer[0] & 15;
          if ((buffer[0] & 112) || (buffer[1] & 128)) throw Error('Invalid Codex WebSocket frame');
          let length = buffer[1] & 127, offset = 2;
          if (length === 126) {
            if (buffer.length < 4) return;
            length = buffer.readUInt16BE(2); offset = 4;
          } else if (length === 127) {
            if (buffer.length < 10) return;
            const large = buffer.readBigUInt64BE(2);
            if (large > BigInt(MAX_MESSAGE)) throw Error('Codex response too large');
            length = Number(large); offset = 10;
          }
          if (length > MAX_MESSAGE || fragmentSize + length > MAX_MESSAGE) throw Error('Codex response too large');
          if (opcode >= 8 && (!fin || length > 125)) throw Error('Invalid Codex control frame');
          if (buffer.length < offset + length) return;
          const body = buffer.subarray(offset, offset + length);
          buffer = buffer.subarray(offset + length);
          if (opcode === 8) throw Error('Codex host closed connection');
          if (opcode === 9) {send(10, body); continue;}
          if (opcode === 10) continue;
          if (opcode === 1 && !fragments.length) {
            if (fin) message(body);
            else {fragments = [body]; fragmentSize = length;}
          } else if (opcode === 0 && fragments.length) {
            fragments.push(body); fragmentSize += length;
            if (fin) {message(Buffer.concat(fragments)); fragments = []; fragmentSize = 0;}
          } else throw Error('Unsupported Codex WebSocket frame');
        }
      } catch (error) {fail(error);}
    }
    request.on('error', fail);
    request.on('response', response => {response.resume(); fail(Error(`WebSocket upgrade refused: ${response.statusCode}`));});
    request.on('upgrade', (response, peer, head) => {
      socket = peer;
      const expected = crypto.createHash('sha1').update(key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').digest('base64');
      if (response.headers['sec-websocket-accept'] !== expected) return fail(Error('Invalid WebSocket handshake'));
      clearTimeout(deadline);
      socket.on('data', receive);
      socket.on('error', fail);
      socket.on('close', () => fail(Error('Codex host disconnected')));
      opened = true;
      resolve({
        call(method, params, callTimeout = timeout) {
          return new Promise((resolveCall, rejectCall) => {
            if (closed) return rejectCall(Error('Codex host disconnected'));
            const id = ++sequence;
            const timer = setTimeout(() => fail(Error(`Codex ${method} timeout`)), callTimeout);
            pending.set(id, {resolve: resolveCall, reject: rejectCall, timer});
            try {send(1, Buffer.from(JSON.stringify({id, method, params})));}
            catch (error) {fail(error);}
          });
        },
        notify(method, params = {}) {send(1, Buffer.from(JSON.stringify({method, params})));},
        close() {fail(Error('Codex host disconnected'));},
      });
      if (head.length) receive(head);
    });
    request.end();
  });
}

async function run(args) {
  const onboarding = require("./codex-onboarding");
  if (onboarding.actions.includes(args[0])) return onboarding.run(args, {connect});
  let client;
  let reservation;
  let roleLock;
  let registrationLock;
  try {
    const action = args.shift();
    if (!["status", "start", "deliver", "handover", "drain", "recover"].includes(action)) throw Error("Usage: keel codex status|start|deliver|handover|drain|recover [--socket path] [--role name] [--repo path] [--thread id] [--timeout ms] [--json]");
    const options = {socket: path.join(process.env.CODEX_HOME || path.join(os.homedir(), ".codex"), "app-server-control/app-server-control.sock"), timeout: 5000, repo: process.cwd()};
    let explicitSocket = false;
    let explicitTimeout = false;
    while (args.length) {
      const flag = args.shift();
      if (flag === "--json") options.json = true;
      else if (["--socket", "--thread", "--timeout", "--role", "--repo", "--record", "--text", "--note", "--approvals-reviewer"].includes(flag)) {
        const value = args.shift();
        if (!value || value.startsWith("--")) throw Error(`${flag} needs a value`);
        options[flag.slice(2)] = value;
        if (flag === "--socket") explicitSocket = true;
        if (flag === "--timeout") explicitTimeout = true;
      } else throw Error(`Unknown argument ${flag}`);
    }
    const requestedReviewer = options["approvals-reviewer"];
    if (requestedReviewer && !["user", "auto_review"].includes(requestedReviewer)) throw Error("approvals-reviewer must be user or auto_review");
    if (requestedReviewer && action !== "start") throw Error("--approvals-reviewer is only accepted by start");
    const ms = Number(options.timeout);
    if (!Number.isInteger(ms) || ms < 50 || ms > 60000) throw Error("timeout must be 50–60000 milliseconds");
    const fs = require("node:fs");
    const store = require("./chat/store");
    if (action === "drain") {
      const deliveries = wakeManaged(store.requireLocation(path.resolve(options.repo)), options.role);
      process.stdout.write(JSON.stringify({deliveries}) + "\n");
      return deliveries.some(entry => entry.error) ? 1 : 0;
    }
    let where, file, recorded;
    if (options.role) {
      store.checkName(options.role, "Role");
      where = store.requireLocation(path.resolve(options.repo));
      if (action === "start" && options.role === "keel") throw Error("Role name keel is reserved");
      if (action === "start" && store.canonicalRole(where.root, options.role) !== options.role) throw Error("Role was renamed; bind its current name before starting a managed thread");
      file = path.join(where.root, "codex-roles", `${options.role}.json`);
      if (fs.existsSync(file)) recorded = JSON.parse(fs.readFileSync(file, "utf8"));
      if (action === "start" && store.currentRole(where) && store.currentRole(where) !== options.role) throw Error("worktree already belongs to a different role");
      if (action === "start" && recorded) throw Error(`managed role ${options.role} already exists; no new thread started`);
      if (action !== "start") {
        if (!recorded || recorded.state !== "managed") throw Error("managed role not found or creation outcome unknown");
        if (recorded.worktree !== where.worktree) throw Error("managed role worktree mismatch");
        if (explicitSocket && options.socket !== recorded.socket) throw Error("managed role endpoint mismatch");
        options.socket = recorded.socket;
        options.thread = recorded.thread;
      }
    }
    if (action === "start" && !options.role) throw Error("start needs --role");
    if (["deliver", "handover", "recover"].includes(action)) {
      if (!recorded) throw Error("operation needs a managed --role");
      const candidateLock = `${file}.lock`;
      const fd = fs.openSync(candidateLock, "wx"); fs.closeSync(fd);
      roleLock = candidateLock;
      // A contender may have read before another process finished its claim.
      // The durable decision must be read under the lock this call now owns.
      recorded = JSON.parse(fs.readFileSync(file, "utf8"));
      if (recorded.state !== "managed" || recorded.role !== options.role || recorded.worktree !== where.worktree || recorded.socket !== options.socket) throw Error("managed role identity changed before operation lock");
      if (action === "deliver" && (!options.record || !options.text)) throw Error("deliver needs --record and --text");
      if (action === "handover" && !options.note) throw Error("handover needs --note");
    }
    if (action === "start") {
      const directory = path.dirname(file); fs.mkdirSync(directory, {recursive: true});
      const candidate = path.join(directory, ".registration.lock");
      const fd = fs.openSync(candidate, "wx"); fs.closeSync(fd); registrationLock = candidate;
      if (fs.existsSync(file)) throw Error("managed role already exists or creation outcome unknown");
    }
    if (action === "handover" && recorded?.registration) throw Error("registered frontend handover requires separate successor authorization; no replacement started");
    const savedPolicy = onboarding.policyFor(recorded);
    // Recovery can restore runtimeWorkspaceRoots even for legacy role records.
    const needsExperimentalApi = action === "recover" || requestedReviewer || recorded?.approvalsReviewer || savedPolicy;
    client = await connect(options.socket, ms);
    const host = await client.call("initialize", {clientInfo: {name: "keel", version: "1"}, ...(needsExperimentalApi ? {capabilities: {experimentalApi: true}} : {})});
    if (!host || typeof host.userAgent !== "string" || !host.userAgent) throw Error("Codex host returned no initialization identity");
    client.notify("initialized");
    const result = {socket: options.socket, host};
    function verifyReviewerPolicy(reply, reviewer) {
      if (!reviewer) return;
      if (reply.approvalsReviewer !== reviewer) throw Error("Codex thread reviewer mismatch; original identity retained");
      if (reply.approvalPolicy !== "on-request") throw Error("Codex thread approval policy mismatch; original identity retained");
      if (reply.sandbox?.type !== "workspaceWrite") throw Error("Codex thread sandbox mismatch; original identity retained");
    }
    async function initializeThread(thread, reviewer) {
      // Native metadata writes materialize fresh persistent threads without a
      // model turn. Blank thread/start alone has no durable rollout yet.
      await client.call("thread/name/set", {threadId: thread.id, name: options.role});
      if (reviewer) await client.call("thread/settings/update", {threadId: thread.id, approvalsReviewer: reviewer, approvalPolicy: "on-request"});
      const verified = (await client.call("thread/read", {threadId: thread.id, includeTurns: false})).thread;
      if (!verified || verified.id !== thread.id || verified.cwd !== where.worktree) {
        throw Error("initialized managed role identity mismatch");
      }
    }
    if (action === "start") {
      const reviewerPolicy = requestedReviewer ? {approvalsReviewer: requestedReviewer} : {};
      fs.mkdirSync(path.dirname(file), {recursive: true});
      const fd = fs.openSync(file, "wx");
      fs.writeFileSync(fd, JSON.stringify({state: "creation-pending", role: options.role, worktree: where.worktree, socket: options.socket, ...reviewerPolicy}));
      fs.closeSync(fd);
      reservation = file;
      const started = await client.call("thread/start", {cwd: where.worktree, sandbox: "workspace-write", approvalPolicy: "on-request", serviceName: "keel", ...reviewerPolicy});
      const thread = started.thread;
      if (!thread || !thread.id || thread.cwd !== where.worktree) throw Error("Codex created thread with unexpected identity");
      store.writeJsonAtomic(where, file, {state: "creation-pending", role: options.role, thread: thread.id, worktree: where.worktree, socket: options.socket, ...reviewerPolicy});
      verifyReviewerPolicy(started, requestedReviewer);
      await initializeThread(thread, requestedReviewer);
      const entry = {state: "managed", role: options.role, thread: thread.id, worktree: where.worktree, socket: options.socket, ...reviewerPolicy};
      store.writeJsonAtomic(where, file, entry);
      store.setRole(where, options.role);
      Object.assign(result, entry);
    } else if (action === "recover") {
      const original = (await client.call("thread/read", {threadId: recorded.thread, includeTurns: false})).thread;
      if (!original || original.id !== recorded.thread) throw Error("managed role identity mismatch; no recovery attempted");
      if (!original.status || !["idle", "active", "notLoaded"].includes(original.status.type)) throw Error("managed role state is not verified; no recovery attempted");
      if (original.status.type === "active") {
        Object.assign(result, {state: "waiting", thread: recorded.thread});
      } else {
        // Native writer ownership decides whether the original id can resume.
        // Restore only the recorded execution cwd; never rewrite role claims.
        const resumed = await client.call("thread/resume", {threadId: recorded.thread, cwd: recorded.worktree, ...(savedPolicy ? (savedPolicy.runtimeWorkspaceRoots !== undefined ? {runtimeWorkspaceRoots: savedPolicy.runtimeWorkspaceRoots} : {}) : {runtimeWorkspaceRoots: [recorded.worktree]}), serviceName: "keel", ...(!savedPolicy && recorded.approvalsReviewer ? {approvalsReviewer: recorded.approvalsReviewer} : {})}, explicitTimeout ? ms : Math.max(ms, 15000));
        if (!resumed.thread || resumed.thread.id !== recorded.thread || resumed.thread.cwd !== recorded.worktree) throw Error("recovered managed role identity mismatch; original registry retained");
        if (savedPolicy) onboarding.verifyPolicy(resumed, savedPolicy);
        else if (resumed.approvalPolicy !== "on-request") throw Error("recovered thread approval policy mismatch; original registry retained");
        if (!savedPolicy && resumed.sandbox?.type !== "workspaceWrite") throw Error("recovered thread sandbox mismatch; original registry retained");
        if (recorded.approvalsReviewer && resumed.approvalsReviewer !== recorded.approvalsReviewer) throw Error("recovered thread reviewer mismatch; original registry retained");
        if (resumed.thread.status?.type !== "idle") throw Error("recovered thread is not verified idle; original registry retained");
        Object.assign(result, {state: "recovered", thread: recorded.thread, worktree: recorded.worktree});
      }
    } else if (["deliver", "handover"].includes(action)) {
      let thread = (await client.call("thread/read", {threadId: recorded.thread, includeTurns: false})).thread;
      const owned = value => value && value.id === recorded.thread && value.cwd === recorded.worktree;
      if (!owned(thread)) throw Error("managed role identity mismatch");
      const claims = recorded.deliveries || {};
      const key = options.record ? crypto.createHash("sha256").update(options.record).digest("hex") : null;
      if (action === "deliver" && claims[key]) {
        // Deduplication is a recorded outcome, not a reason to load a thread.
        if (claims[key].state !== "delivered" || typeof claims[key].turn !== "string" || !claims[key].turn) {
          throw Error("delivery outcome unknown; claim retained, no retry started");
        }
        Object.assign(result, {state: "already-delivered", turn: claims[key].turn});
      } else {
        if (action === "deliver" && thread.status && (thread.status.type === "notLoaded" || ((recorded.approvalsReviewer || savedPolicy) && thread.status.type === "idle"))) {
          // Only this recorded owned identity may be loaded. Keep this same
          // connection alive through the subsequent turn/start and preserve
          // saved sandbox/approval settings. An explicitly chosen reviewer
          // belongs to the managed role and follows its later deliveries.
          const resumed = await client.call("thread/resume", {threadId: recorded.thread, ...(!savedPolicy ? {serviceName: "keel", ...(recorded.approvalsReviewer ? {approvalsReviewer: recorded.approvalsReviewer} : {})} : {})}, explicitTimeout ? ms : Math.max(ms, 15000));
          thread = resumed.thread;
          if (!owned(thread)) throw Error("resumed managed role identity mismatch");
          if (thread.status?.type === "idle") {
            if (savedPolicy) onboarding.verifyPolicy(resumed, savedPolicy);
            else verifyReviewerPolicy(resumed, recorded.approvalsReviewer);
          }
        }
        if (!thread.status || !["idle", "active"].includes(thread.status.type)) {
          throw Error("managed role state is not verified idle or active; no work started");
        }
        if (thread.status.type === "active") {
          Object.assign(result, {state: "waiting", thread: recorded.thread});
        } else if (action === "deliver") {
          claims[key] = {record: options.record, state: "pending"};
          recorded.deliveries = claims;
          store.writeJsonAtomic(where, file, recorded);
          const turn = (await client.call("turn/start", {threadId: recorded.thread, ...(!savedPolicy && recorded.approvalsReviewer ? {approvalsReviewer: recorded.approvalsReviewer} : {}), input: [{type: "text", text: (recorded.note ? `Handover note (context only):\n${recorded.note}\n\n` : "") + options.text}]})).turn;
          if (!turn || !turn.id) throw Error("Codex returned no turn identity; claim retained");
          claims[key] = {record: options.record, state: "delivered", turn: turn.id};
          store.writeJsonAtomic(where, file, recorded);
          Object.assign(result, {state: "delivered", turn: turn.id});
        } else {
          if (recorded.handover) throw Error("handover outcome unknown; no successor started");
          recorded.handover = {state: "pending", note: options.note};
          store.writeJsonAtomic(where, file, recorded);
          const successor = await client.call("thread/start", {cwd: recorded.worktree, sandbox: "workspace-write", approvalPolicy: "on-request", serviceName: "keel", ...(recorded.approvalsReviewer ? {approvalsReviewer: recorded.approvalsReviewer} : {})});
          const next = successor.thread;
          if (!next || !next.id || next.cwd !== recorded.worktree) throw Error("successor identity mismatch; handover retained");
          recorded.handover.thread = next.id;
          store.writeJsonAtomic(where, file, recorded);
          verifyReviewerPolicy(successor, recorded.approvalsReviewer);
          await initializeThread(next, recorded.approvalsReviewer);
          const history = [...(recorded.history || []), {thread: recorded.thread, note: options.note}];
          delete recorded.handover;
          Object.assign(recorded, {thread: next.id, history, note: options.note});
          store.writeJsonAtomic(where, file, recorded);
          Object.assign(result, {state: "handed-over", thread: next.id, note: options.note});
        }
      }
    } else if (options.thread) {
      result.thread = (await client.call("thread/read", {threadId: options.thread, includeTurns: false})).thread;
      if (recorded && (result.thread.id !== recorded.thread || result.thread.cwd !== recorded.worktree)) throw Error("managed role identity mismatch");
    }
    process.stdout.write((options.json ? JSON.stringify(result) : `Codex host connected: ${host.userAgent}${result.role ? `; role ${result.role}: ${result.thread}` : ""}`) + "\n");
    return 0;
  } catch (error) {
    process.stderr.write(`keel codex: ${error.message}${reservation ? "; creation record retained to prevent duplicate start" : ""}\n`);
    return 1;
  } finally {
    if (client) client.close();
    if (roleLock) require("node:fs").rmSync(roleLock, {force: true});
    if (registrationLock) require("node:fs").rmSync(registrationLock, {force: true});
  }
}
// Use the existing mailbox addressing rules and parking decisions. Calling the
// public CLI in a child keeps synchronous tick callers and Claude behavior intact.
function wakeManaged(where, onlyRole = null) {
  const fs = require('node:fs');
  const store = require('./chat/store');
  const directory = path.join(where.root, 'codex-roles');
  if (!fs.existsSync(directory)) return [];
  const results = [];
  for (const name of fs.readdirSync(directory).filter(name => name.endsWith('.json')).sort()) {
    let entry;
    try {entry = JSON.parse(fs.readFileSync(path.join(directory, name), 'utf8'));}
    catch (error) {results.push({role: name, error: error.message}); continue;}
    const role = name.slice(0, -5);
    if (onlyRole && onlyRole !== role) continue;
    if (entry.state !== 'managed' || entry.role !== role) {
      results.push({role, error: 'managed role identity or creation outcome unverified'}); continue;
    }
    if (require('./chat/notice').parkOf(where, role)) continue;
    const bound = store.readJsonFile(path.join(where.root, 'roles.json'));
    if (bound[entry.worktree] !== role) {
      results.push({role, error: 'managed worktree role binding mismatch'}); continue;
    }
    for (const record of store.unread(where, role).filter(record => store.wakes(record, role))) {
      const prompt = `${store.DATA_NOTICE}\nRun keel context before acting.\nAddressed record ${record.id} from ${record.from}:\n${record.text || record.body || ''}`;
      const child = require('node:child_process').spawnSync(process.execPath, [
        path.resolve(__dirname, '../../bin/keel.js'), 'codex', 'deliver',
        '--repo', entry.worktree, '--role', role, '--record', record.id, '--text', prompt, '--json',
      ], {encoding: 'utf8', timeout: 40000});
      let result;
      try {result = JSON.parse(child.stdout);} catch {result = {};}
      if (child.error || child.status !== 0) result.error = child.error ? child.error.message : child.stderr.trim();
      results.push({role, record: record.id, ...result});
      if (result.error || result.state === 'waiting' || result.state === 'delivered') break;
    }
  }
  return results;
}
module.exports = {connect, run, wakeManaged};
