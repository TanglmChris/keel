"use strict";

// How the Slack bridge lives on a machine (issue #187, design D17, D18):
// where its tokens come from, the user LaunchAgent that keeps it running, and
// the controls that pause, stop, start, or remove it.
//
// The owner runs `install`, `start`, `stop`, and `uninstall`: they change the
// machine's login items, which is system configuration, not project state.
// Tests replace the system boundary with doubles through KEEL_CHAT_LAUNCHCTL,
// KEEL_CHAT_SECURITY, and KEEL_CHAT_LAUNCH_AGENTS_DIR.

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");
const { ChatError } = require("./store");

const LABEL = "dev.keel.chat-bridge";
const KEYCHAIN_SERVICE = "keel-chat-slack";

function keelHome() {
  return process.env.KEEL_HOME || path.join(os.homedir(), ".keel");
}

function bridgeDir() {
  return path.join(keelHome(), "chat", "bridge");
}

// --- tokens -----------------------------------------------------------------------

function keychainToken(account) {
  const security = process.env.KEEL_CHAT_SECURITY || (process.platform === "darwin" ? "security" : null);
  if (!security) return null;
  const result = spawnSync(security, ["find-generic-password", "-s", KEYCHAIN_SERVICE, "-a", account, "-w"], {
    encoding: "utf8",
    timeout: 10000,
  });
  if (result.status !== 0) return null;
  const token = String(result.stdout || "").trim();
  return token || null;
}

// The environment first, then the macOS Keychain. Tokens are held in memory
// only: never written to a file, a record, the status, or a log.
function tokens() {
  const app = (process.env.KEEL_SLACK_APP_TOKEN || "").trim() || keychainToken("app");
  const bot = (process.env.KEEL_SLACK_BOT_TOKEN || "").trim() || keychainToken("bot");
  return { app: app || null, bot: bot || null };
}

// A registered bot's tokens (chat-shared-bots D1): Keychain only, by the
// bot's name, because an environment variable would have to encode that name
// in its own.
function botTokens(name) {
  return { bot: keychainToken(`bot:${name}`), app: keychainToken(`app:${name}`) };
}

function missingTokens(which) {
  return new ChatError(
    `No Slack ${which}: set KEEL_SLACK_APP_TOKEN and KEEL_SLACK_BOT_TOKEN, or store them in the macOS Keychain `
      + `as generic passwords of service ${KEYCHAIN_SERVICE}, accounts app and bot `
      + `(\`security add-generic-password -s ${KEYCHAIN_SERVICE} -a app -w\`).`
  );
}

// --- pause ------------------------------------------------------------------------

function controlFile() {
  return path.join(bridgeDir(), "control.json");
}

function readControl() {
  try {
    return JSON.parse(fs.readFileSync(controlFile(), "utf8")) || {};
  } catch {
    return {};
  }
}

function pausedUntil(now = Date.now()) {
  const until = Date.parse(readControl().paused_until || "");
  return !Number.isNaN(until) && until > now ? until : null;
}

function parseDuration(value) {
  const match = String(value || "").trim().match(/^(\d+)([smhd])$/);
  if (!match) return null;
  return Number(match[1]) * { s: 1e3, m: 60e3, h: 3600e3, d: 86400e3 }[match[2]];
}

function pause(duration) {
  const ms = parseDuration(duration);
  if (!ms) throw new ChatError(`keel chat bridge pause needs a duration such as 30m, 2h, or 1d, not ${JSON.stringify(duration)}.`);
  const until = new Date(Date.now() + ms);
  fs.mkdirSync(bridgeDir(), { recursive: true });
  fs.writeFileSync(controlFile(), `${JSON.stringify({ paused_until: until.toISOString() }, null, 2)}\n`);
  return until;
}

function resume() {
  try {
    fs.rmSync(controlFile());
  } catch {
    // Not paused.
  }
}

// --- the LaunchAgent ----------------------------------------------------------------

function agentsDir() {
  return process.env.KEEL_CHAT_LAUNCH_AGENTS_DIR || path.join(os.homedir(), "Library", "LaunchAgents");
}

function plistPath() {
  return path.join(agentsDir(), `${LABEL}.plist`);
}

function installed() {
  return fs.existsSync(plistPath());
}

function xml(text) {
  return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function plistText() {
  const cli = path.resolve(__dirname, "..", "..", "..", "bin", "keel.js");
  const args = [process.execPath, cli, "chat", "bridge", "run"];
  const environment = { PATH: process.env.PATH || "/usr/bin:/bin:/usr/sbin:/sbin" };
  if (process.env.KEEL_HOME) environment.KEEL_HOME = process.env.KEEL_HOME;
  if (process.env.KEEL_CHAT_MACHINE) environment.KEEL_CHAT_MACHINE = process.env.KEEL_CHAT_MACHINE;
  const log = path.join(bridgeDir(), "bridge.log");
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
    '<plist version="1.0">',
    "<dict>",
    `  <key>Label</key><string>${LABEL}</string>`,
    "  <key>ProgramArguments</key>",
    "  <array>",
    ...args.map((arg) => `    <string>${xml(arg)}</string>`),
    "  </array>",
    "  <key>EnvironmentVariables</key>",
    "  <dict>",
    ...Object.entries(environment).map(([key, value]) => `    <key>${xml(key)}</key><string>${xml(value)}</string>`),
    "  </dict>",
    "  <key>RunAtLoad</key><true/>",
    "  <key>KeepAlive</key><true/>",
    "  <key>ProcessType</key><string>Background</string>",
    `  <key>StandardOutPath</key><string>${xml(log)}</string>`,
    `  <key>StandardErrorPath</key><string>${xml(log)}</string>`,
    "</dict>",
    "</plist>",
    "",
  ].join("\n");
}

function launchctl(args) {
  const command = process.env.KEEL_CHAT_LAUNCHCTL || "launchctl";
  const result = spawnSync(command, args, { encoding: "utf8", timeout: 20000 });
  return { ok: result.status === 0, output: `${result.stdout || ""}${result.stderr || ""}`.trim() };
}

function domain() {
  return `gui/${typeof process.getuid === "function" ? process.getuid() : 0}`;
}

// launchd's view of the agent (bridge-start-race D1): loaded with its state
// and pid, unloaded, or null when launchctl gives no answer to read — a
// system without it, or a test double that prints nothing.
function loadedState() {
  const result = launchctl(["print", `${domain()}/${LABEL}`]);
  const state = result.output.match(/^\s*state = (\S+)/m);
  if (result.ok && state) {
    const pid = result.output.match(/^\s*pid = (\d+)/m);
    return { loaded: true, state: state[1], pid: pid ? Number(pid[1]) : null };
  }
  if (!result.ok && /could not find service/i.test(result.output)) return { loaded: false };
  return null;
}

function waitLimit() {
  const ms = Number(process.env.KEEL_CHAT_LAUNCHCTL_WAIT_MS);
  return Number.isFinite(ms) && ms >= 0 ? ms : 10000;
}

function sleep(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
}

// `bootout` returns before launchd has removed the service (F1); waits,
// bounded, until it reports the service gone or gives no answer.
function bootout() {
  launchctl(["bootout", `${domain()}/${LABEL}`]);
  const deadline = Date.now() + waitLimit();
  for (;;) {
    const state = loadedState();
    if (!state || !state.loaded || Date.now() >= deadline) return;
    sleep(250);
  }
}

// Loads the agent, retrying while a previous unload is still in progress
// (D2); any other failure, or one that outlasts the wait, is reported with
// launchctl's own words.
function bootstrap(what) {
  const deadline = Date.now() + waitLimit();
  for (;;) {
    const loaded = launchctl(["bootstrap", domain(), plistPath()]);
    if (loaded.ok) return;
    const busy = /already|in progress|5:/i.test(loaded.output);
    if (!busy || Date.now() >= deadline) {
      throw new ChatError(`launchctl could not ${what}: ${loaded.output}`);
    }
    sleep(500);
  }
}

function install() {
  if (process.platform !== "darwin" && !process.env.KEEL_CHAT_LAUNCHCTL) {
    throw new ChatError("keel chat bridge install sets up a macOS LaunchAgent; on this system run `keel chat bridge run` under your own service manager.");
  }
  fs.mkdirSync(agentsDir(), { recursive: true });
  fs.mkdirSync(bridgeDir(), { recursive: true });
  fs.writeFileSync(plistPath(), plistText());
  bootout();
  bootstrap(`load ${plistPath()}`);
  return plistPath();
}

function uninstall() {
  bootout();
  try {
    fs.rmSync(plistPath());
  } catch {
    // Already gone.
  }
  return plistPath();
}

// Returns false when launchd already has the agent loaded, and so keeps it
// running, and nothing was done.
function start() {
  if (!installed()) throw new ChatError("The bridge is not installed: run `keel chat bridge install` first.");
  resume();
  const state = loadedState();
  if (state && state.loaded) return false;
  bootstrap("start the bridge");
  return true;
}

// Unloads the agent: it stays stopped until `start`, or until the next login
// loads it again.
function stop() {
  bootout();
}

module.exports = {
  botTokens,
  KEYCHAIN_SERVICE,
  LABEL,
  bridgeDir,
  install,
  installed,
  loadedState,
  missingTokens,
  pause,
  pausedUntil,
  plistPath,
  resume,
  start,
  stop,
  tokens,
  uninstall,
};
