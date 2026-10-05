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

// A role's own app (chat-role-apps D2): Keychain only, on the machine where
// the role runs, because an environment variable would have to encode a role
// name in its own name.
function roleTokens(role) {
  return { bot: keychainToken(`bot:${role}`), app: keychainToken(`app:${role}`) };
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

function install() {
  if (process.platform !== "darwin" && !process.env.KEEL_CHAT_LAUNCHCTL) {
    throw new ChatError("keel chat bridge install sets up a macOS LaunchAgent; on this system run `keel chat bridge run` under your own service manager.");
  }
  fs.mkdirSync(agentsDir(), { recursive: true });
  fs.mkdirSync(bridgeDir(), { recursive: true });
  fs.writeFileSync(plistPath(), plistText());
  launchctl(["bootout", `${domain()}/${LABEL}`]);
  const loaded = launchctl(["bootstrap", domain(), plistPath()]);
  if (!loaded.ok) throw new ChatError(`launchctl could not load ${plistPath()}: ${loaded.output}`);
  return plistPath();
}

function uninstall() {
  launchctl(["bootout", `${domain()}/${LABEL}`]);
  try {
    fs.rmSync(plistPath());
  } catch {
    // Already gone.
  }
  return plistPath();
}

function start() {
  if (!installed()) throw new ChatError("The bridge is not installed: run `keel chat bridge install` first.");
  resume();
  const loaded = launchctl(["bootstrap", domain(), plistPath()]);
  if (!loaded.ok && !/already|in progress|5:/i.test(loaded.output)) {
    throw new ChatError(`launchctl could not start the bridge: ${loaded.output}`);
  }
}

// Unloads the agent: it stays stopped until `start`, or until the next login
// loads it again.
function stop() {
  launchctl(["bootout", `${domain()}/${LABEL}`]);
}

module.exports = {
  roleTokens,
  KEYCHAIN_SERVICE,
  LABEL,
  bridgeDir,
  install,
  installed,
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
