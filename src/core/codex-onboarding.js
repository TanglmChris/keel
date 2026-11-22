'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const store = require('./chat/store');
const actions = ['inspect-registration', 'register', 'inspect-migration', 'migrate', 'migration-status'];
const canonical = value => Array.isArray(value) ? value.map(canonical) : value && typeof value === 'object' ? Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])])) : value;
const digest = value => crypto.createHash('sha256').update(typeof value === 'string' || Buffer.isBuffer(value) ? value : JSON.stringify(canonical(value))).digest('hex');
const same = (a, b) => digest(a) === digest(b);
function policyOf(reply) {
  if (!reply.sandbox?.type || !reply.approvalPolicy || !['user', 'auto_review'].includes(reply.approvalsReviewer)) throw Error('native effective policy unavailable');
  const result = {};
  for (const key of ['approvalPolicy', 'approvalsReviewer', 'sandbox', 'runtimeWorkspaceRoots', 'activePermissionProfile']) {
    if (key === 'activePermissionProfile') {
      const profile = reply[key];
      const builtin = {readOnly: ':read-only', workspaceWrite: ':workspace-write'}[reply.sandbox.type];
      // Native cold resume may attach built-in provenance to an unchanged
      // legacy policy. Custom profiles and every effective field stay exact.
      if (profile == null || (builtin && profile.id === builtin && profile.extends == null)) continue;
    }
    if (reply[key] !== undefined) result[key] = reply[key];
  }
  return result;
}
function policyFor(record) { return record?.nativePolicy || record?.endpointMigrations?.at(-1)?.nativePolicy; }
function verifyPolicy(reply, expected) {
  if (!same(policyOf(reply), expected)) throw Error('native effective policy mismatch; no policy override attempted');
}
function verifyThread(thread, plan) {
  if (!thread || thread.id !== plan.thread || thread.cwd !== plan.worktree) throw Error('original thread identity or worktree mismatch');
  if (!['idle', 'active', 'notLoaded'].includes(thread.status?.type)) throw Error('original native thread state is unverified');
}
function acquire(file, locks) {
  fs.mkdirSync(path.dirname(file), {recursive: true});
  const fd = fs.openSync(file, 'wx'); fs.closeSync(fd); locks.push(file);
}
function binding(where, role) {
  store.checkName(role, 'Role');
  if (role === 'keel') throw Error('Role name keel is reserved');
  if (store.canonicalRole(where.root, role) !== role) throw Error('Role was renamed; use its current canonical name');
  const roles = JSON.parse(fs.readFileSync(path.join(where.root, 'roles.json'), 'utf8'));
  if (roles[where.worktree] !== role) throw Error('worktree must already be bound to this exact role');
  if (Object.entries(roles).some(([worktree, name]) => name === role && worktree !== where.worktree)) throw Error('role is bound to another worktree');
}
function unique(where, role, thread, registering) {
  const directory = path.join(where.root, 'codex-roles');
  if (!fs.existsSync(directory)) return;
  for (const name of fs.readdirSync(directory).filter(name => name.endsWith('.json'))) {
    const value = JSON.parse(fs.readFileSync(path.join(directory, name), 'utf8'));
    if (name === role + '.json') {
      if (registering) throw Error('managed role already exists or creation outcome unknown');
      continue;
    }
    if (value.thread === thread || value.handover?.thread === thread || value.history?.some(item => item.thread === thread)) throw Error('original thread already belongs to another managed role');
  }
}
function loadPlan(file) {
  const plan = JSON.parse(fs.readFileSync(file, 'utf8'));
  const {id, ...body} = plan;
  if (plan.schema !== 'keel-codex-onboarding/v1' || !id || digest(body) !== id) throw Error('invalid or tampered onboarding plan');
  return plan;
}
function savePlan(body) { return {...body, id: digest(body)}; }
async function history(client, thread) {
  const turns = [], seen = new Set(); let cursor;
  do {
    const reply = await client.call('thread/turns/list', {threadId: thread, sortDirection: 'asc', itemsView: 'full', limit: 50, ...(cursor ? {cursor} : {})});
    if (!Array.isArray(reply.data)) throw Error('native full history unavailable');
    turns.push(...reply.data);
    cursor = reply.nextCursor;
    if (cursor && (typeof cursor !== 'string' || seen.has(cursor))) throw Error('native history cursor did not advance');
    if (cursor) seen.add(cursor);
  } while (cursor);
  return turns;
}
async function run(args, {connect}) {
  const clients = [], locks = [];
  try {
    const action = args.shift(), options = {timeout: 15000};
    while (args.length) {
      const flag = args.shift();
      if (flag === '--json') continue;
      if (flag === '--reconcile') {options.reconcile = true; continue;}
      if (!['--repo', '--role', '--thread', '--socket', '--authority', '--plan', '--timeout', '--to-socket'].includes(flag)) throw Error(`Unknown argument ${flag}`);
      const value = args.shift();
      if (!value || value.startsWith('--')) throw Error(`${flag} needs a value`);
      if (options[flag.slice(2)] !== undefined && flag !== '--timeout') throw Error(`duplicate ${flag}`);
      options[flag.slice(2)] = value;
    }
    const timeout = Number(options.timeout);
    if (!Number.isInteger(timeout) || timeout < 50 || timeout > 60000) throw Error('timeout must be 50–60000 milliseconds');
    if (['inspect-migration', 'migrate', 'migration-status'].includes(action)) return await migration(action, options, {connect, timeout, clients, locks});
    if (options.reconcile || options['to-socket']) throw Error('migration-only option used for registration');
    let plan, where;
    const applying = action === 'register';
    if (applying) {
      if (!options.plan) throw Error('register needs --plan');
      if (['repo','role','thread','socket','authority'].some(key => options[key])) throw Error('apply takes the exact plan; tuple overrides are not accepted');
      plan = loadPlan(options.plan);
      if (plan.action !== 'registration') throw Error('plan action mismatch');
      where = store.requireLocation(plan.worktree);
      if (where.root !== plan.root || where.worktree !== plan.worktree) throw Error('plan repository identity mismatch');
    } else {
      if (options.plan || ['repo','role','thread','socket','authority'].some(key => !options[key])) throw Error('inspect-registration needs explicit --repo --role --thread --socket --authority');
      if (!path.isAbsolute(options.socket)) throw Error('native socket must be an absolute path');
      where = store.requireLocation(path.resolve(options.repo));
      plan = {schema: 'keel-codex-onboarding/v1', action: 'registration', root: where.root, worktree: where.worktree, role: options.role, thread: options.thread, socket: options.socket, authority: options.authority};
    }
    acquire(path.join(where.root, 'codex-roles', '.registration.lock'), locks);
    binding(where, plan.role);
    unique(where, plan.role, plan.thread, true);
    const file = path.join(where.root, 'codex-roles', plan.role + '.json');
    acquire(file + '.lock', locks);
    const client = await connect(plan.socket, timeout); clients.push(client);
    const host = await client.call('initialize', {clientInfo: {name: 'keel-onboarding', version: '1'}, capabilities: {experimentalApi: true}});
    if (!host?.userAgent) throw Error('Codex host returned no initialization identity');
    client.notify('initialized');
    const before = (await client.call('thread/read', {threadId: plan.thread, includeTurns: false})).thread;
    verifyThread(before, plan);
    // Rejoin the exact native context. No settings, cwd or permission overrides.
    const native = await client.call('thread/resume', {threadId: plan.thread});
    verifyThread(native.thread, plan);
    if (!['idle', 'active'].includes(native.thread.status.type)) throw Error('original thread is not loaded after native rejoin');
    const policy = policyOf(native);
    if (applying) verifyPolicy(native, plan.nativePolicy);
    const turns = await history(client, plan.thread);
    if (!applying) {
      const prepared = savePlan({...plan, nativePolicy: policy, historyDigest: digest(turns), historyCount: turns.length});
      process.stdout.write(JSON.stringify(prepared) + '\n');
    } else {
      binding(where, plan.role); unique(where, plan.role, plan.thread, true);
      const entry = {state: 'managed', role: plan.role, thread: plan.thread, worktree: plan.worktree, socket: plan.socket, nativePolicy: policy, registration: {plan: plan.id, authority: plan.authority, historyDigest: plan.historyDigest, historyCount: plan.historyCount}};
      // Hard link is atomic no-overwrite; a failed/competing write cannot turn
      // a partial file into a managed record. Existing worktree binding stays.
      const temporary = file + '.' + crypto.randomBytes(8).toString('hex') + '.tmp';
      try {fs.writeFileSync(temporary, JSON.stringify(entry, null, 2) + '\n', {flag: 'wx', mode: 0o600}); fs.linkSync(temporary, file);}
      finally {fs.rmSync(temporary, {force: true});}
      process.stdout.write(JSON.stringify({state: 'registered', role: plan.role, thread: plan.thread, socket: plan.socket, plan: plan.id}) + '\n');
    }
    return 0;
  } catch (error) {process.stderr.write(`keel codex: ${error.message}\n`); return 1;}
  finally {clients.forEach(client => client.close()); locks.reverse().forEach(file => fs.rmSync(file, {force: true}));}
}

async function openHost(socket, {connect, timeout, clients}) {
  const client = await connect(socket, timeout); clients.push(client);
  const host = await client.call('initialize', {clientInfo: {name: 'keel-onboarding', version: '1'}, capabilities: {experimentalApi: true}});
  if (!host?.userAgent) throw Error('Codex host returned no initialization identity');
  client.notify('initialized'); return client;
}
async function quiescent(client, plan, thread, turns) {
  if (thread.status.type !== 'idle' || turns.some(turn => turn.status === 'inProgress')) throw Error('source has active work; no handoff attempted');
  const [queue, goal, terminals] = await Promise.all([
    client.call('thread/queue/list', {threadId: plan.thread}),
    client.call('thread/goal/get', {threadId: plan.thread}),
    client.call('thread/backgroundTerminals/list', {threadId: plan.thread}),
  ]);
  if (!Array.isArray(queue.data) || queue.data.length || queue.nextCursor) throw Error('source queue is not verified empty; input retained');
  if (!Object.hasOwn(goal, 'goal') || goal.goal !== null) throw Error('source Goal is not verified absent; Goal retained');
  if (!Array.isArray(terminals.data) || terminals.data.length || terminals.nextCursor) throw Error('source background tools are not verified absent; tools retained');
}
async function inspectSource(client, plan, recorded) {
  const before = (await client.call('thread/read', {threadId: plan.thread, includeTurns: false})).thread;
  verifyThread(before, plan);
  if (before.status.type === 'active') throw Error('source has active work; no handoff attempted');
  const native = await client.call('thread/resume', {threadId: plan.thread});
  verifyThread(native.thread, plan);
  const nativePolicy = policyOf(native);
  if (policyFor(recorded)) verifyPolicy(native, policyFor(recorded));
  else {
    if (nativePolicy.approvalPolicy !== 'on-request' || nativePolicy.sandbox.type !== 'workspaceWrite') throw Error('legacy managed role policy mismatch; no handoff attempted');
    if (recorded.approvalsReviewer && nativePolicy.approvalsReviewer !== recorded.approvalsReviewer) throw Error('legacy managed role reviewer mismatch; no handoff attempted');
  }
  const turns = await history(client, plan.thread);
  await quiescent(client, plan, native.thread, turns);
  return {nativePolicy, historyDigest: digest(turns), historyCount: turns.length};
}
async function migration(action, options, context) {
  const {clients, locks} = context;
  const applying = action !== 'inspect-migration';
  let where, plan;
  if (applying) {
    if (!options.plan) throw Error(`${action} needs --plan`);
    if (['repo', 'role', 'thread', 'socket', 'authority', 'to-socket'].some(key => options[key])) throw Error('apply takes the exact plan; tuple overrides are not accepted');
    if (options.reconcile && action !== 'migrate') throw Error('--reconcile is only accepted by migrate');
    plan = loadPlan(options.plan);
    if (plan.action !== 'migration') throw Error('plan action mismatch');
    where = store.requireLocation(plan.worktree);
    if (where.root !== plan.root || where.worktree !== plan.worktree) throw Error('plan repository identity mismatch');
  } else {
    if (options.plan || options.reconcile || options.thread || options.socket || ['repo', 'role', 'to-socket', 'authority'].some(key => !options[key])) throw Error('inspect-migration needs explicit --repo --role --to-socket --authority');
    if (!path.isAbsolute(options['to-socket'])) throw Error('native target socket must be an absolute path');
    where = store.requireLocation(path.resolve(options.repo));
    plan = {schema: 'keel-codex-onboarding/v1', action: 'migration', root: where.root, worktree: where.worktree, role: options.role, toSocket: options['to-socket'], authority: options.authority};
  }
  binding(where, plan.role);
  const file = path.join(where.root, 'codex-roles', plan.role + '.json');
  const journalFile = applying ? path.join(where.root, 'codex-transitions', plan.id + '.json') : null;
  if (action === 'migration-status') {
    const journal = fs.existsSync(journalFile) ? JSON.parse(fs.readFileSync(journalFile, 'utf8')) : null;
    const registry = JSON.parse(fs.readFileSync(file, 'utf8'));
    const observed = {};
    for (const [name, socket] of [['source', plan.fromSocket], ['target', plan.toSocket]]) {
      try {
        const client = await openHost(socket, context);
        const thread = (await client.call('thread/read', {threadId: plan.thread, includeTurns: false})).thread;
        verifyThread(thread, plan); observed[name] = {state: thread.status.type};
      } catch (error) {observed[name] = {error: error.message};}
    }
    process.stdout.write(JSON.stringify({state: journal?.state || 'not-started', phase: journal?.phase || null, registrySocket: registry.socket, registryMatchesSourceSnapshot: digest(fs.readFileSync(file)) === plan.registryDigest, observed}) + '\n');
    return 0;
  }
  acquire(path.join(where.root, 'codex-roles', '.registration.lock'), locks);
  acquire(file + '.lock', locks);
  binding(where, plan.role);
  const bytes = fs.readFileSync(file), recorded = JSON.parse(bytes);
  if (recorded.state !== 'managed' || recorded.role !== plan.role || recorded.worktree !== where.worktree || !recorded.thread || !recorded.socket) throw Error('managed role identity or creation outcome unverified');
  if (!applying) {
    plan.thread = recorded.thread; plan.fromSocket = recorded.socket; plan.registryDigest = digest(bytes);
    if (plan.toSocket === plan.fromSocket) throw Error('migration target is already the recorded endpoint');
  }
  unique(where, plan.role, plan.thread, false);
  let journal = applying && fs.existsSync(journalFile) ? JSON.parse(fs.readFileSync(journalFile, 'utf8')) : null;
  if (journal?.state === 'committed') {
    if (recorded.socket !== plan.toSocket || recorded.thread !== plan.thread || !recorded.endpointMigrations?.some(entry => entry.plan === plan.id)) throw Error('committed migration no longer matches registry');
    process.stdout.write(JSON.stringify({state: 'already-migrated', thread: plan.thread, plan: plan.id}) + '\n'); return 0;
  }
  const audit = {plan: plan.id, authority: plan.authority, fromSocket: plan.fromSocket, toSocket: plan.toSocket, nativePolicy: plan.nativePolicy, historyDigest: plan.historyDigest, historyCount: plan.historyCount};
  const nextRegistry = original => ({...original, socket: plan.toSocket, endpointMigrations: [...(original.endpointMigrations || []), audit]});
  const registryAlreadyApplied = Boolean(options.reconcile && journal?.originalRegistry && digest(journal.originalRegistry) === plan.registryDigest && same(recorded, nextRegistry(JSON.parse(journal.originalRegistry))));
  const expectedDigest = registryAlreadyApplied ? digest(bytes) : plan.registryDigest;
  const unchanged = () => {
    binding(where, plan.role);
    if (digest(fs.readFileSync(file)) !== expectedDigest) throw Error('managed role registry changed since inspection; original snapshot not overwritten');
  };
  unchanged();
  if ((!registryAlreadyApplied && recorded.socket !== plan.fromSocket) || recorded.thread !== plan.thread) throw Error('migration source identity mismatch');
  if (journal && !options.reconcile) throw Error('migration outcome unknown; inspect migration-status and explicitly reconcile, no automatic retry');
  if (options.reconcile && !journal) throw Error('no transition exists to reconcile');
  const source = await openHost(plan.fromSocket, context);
  if (!options.reconcile) {
    const snapshot = await inspectSource(source, plan, recorded);
    if (!applying) {
      process.stdout.write(JSON.stringify(savePlan({...plan, ...snapshot})) + '\n'); return 0;
    }
    if (!same(snapshot.nativePolicy, plan.nativePolicy) || snapshot.historyDigest !== plan.historyDigest || snapshot.historyCount !== plan.historyCount) throw Error('native source policy or history changed since inspection');
    unchanged();
    journal = {schema: 'keel-codex-migration/v1', state: 'pending', phase: 'intent', plan, originalRegistry: bytes.toString('utf8')};
    store.writeJsonAtomic(where, journalFile, journal);
  }
  try {
    if (!options.reconcile) {
      // Only release our own source subscription, never cancel a tool/turn or
      // remove another frontend's subscription. Native writer refusal rules.
      const current = (await source.call('thread/read', {threadId: plan.thread, includeTurns: false})).thread;
      verifyThread(current, plan);
      await quiescent(source, plan, current, await history(source, plan.thread));
      journal.phase = 'releasing'; store.writeJsonAtomic(where, journalFile, journal);
      const released = await source.call('thread/unsubscribe', {threadId: plan.thread});
      if (released.status !== 'unsubscribed') throw Error('source subscription release not verified');
    }
    const target = await openHost(plan.toSocket, context);
    const targetThread = (await target.call('thread/read', {threadId: plan.thread, includeTurns: false})).thread;
    verifyThread(targetThread, plan);
    if (options.reconcile) {
      const sourceThread = (await source.call('thread/read', {threadId: plan.thread, includeTurns: false})).thread;
      verifyThread(sourceThread, plan);
      if (sourceThread.status.type !== 'notLoaded') throw Error('source release not verified during reconciliation');
      if (!['idle', 'active'].includes(targetThread.status.type)) throw Error('target is not already loaded; reconciliation will not retry native acquisition');
    }
    const prior = await history(target, plan.thread);
    if (prior.length < plan.historyCount || digest(prior.slice(0, plan.historyCount)) !== plan.historyDigest || (!options.reconcile && prior.length !== plan.historyCount)) throw Error('target original persistent history mismatch');
    journal.phase = options.reconcile ? 'reconciling' : 'acquiring'; store.writeJsonAtomic(where, journalFile, journal);
    const native = await target.call('thread/resume', {threadId: plan.thread});
    verifyThread(native.thread, plan); verifyPolicy(native, plan.nativePolicy);
    if (!['idle', ...(options.reconcile ? ['active'] : [])].includes(native.thread.status.type)) throw Error('target native state changed; registration retained');
    const after = await history(target, plan.thread);
    if (after.length < plan.historyCount || digest(after.slice(0, plan.historyCount)) !== plan.historyDigest || (!options.reconcile && after.length !== plan.historyCount)) throw Error('resumed target original persistent history mismatch');
    journal.phase = 'verified'; store.writeJsonAtomic(where, journalFile, journal);
    unchanged();
    if (!registryAlreadyApplied) store.writeJsonAtomic(where, file, nextRegistry(recorded));
    journal.state = 'committed'; journal.phase = 'committed'; delete journal.error;
    store.writeJsonAtomic(where, journalFile, journal);
    process.stdout.write(JSON.stringify({state: 'migrated', role: plan.role, thread: plan.thread, socket: plan.toSocket, plan: plan.id}) + '\n'); return 0;
  } catch (error) {
    journal.state = 'unknown'; journal.error = error.message;
    try {store.writeJsonAtomic(where, journalFile, journal);} catch { /* Preserve last durable phase if journaling itself fails. */ }
    throw Error(`${error.message}; migration outcome unknown, journal retained; no native rollback claimed`);
  }
}
module.exports = {actions, run, policyOf, policyFor, verifyPolicy};
