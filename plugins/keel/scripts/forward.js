"use strict";

// Hand-off to an installed update (issue #204), Claude Code only.
//
// Claude binds a session's hooks to the version directory it loaded,
// <plugins>/cache/<marketplace>/<plugin>/<version>, and keeps that directory
// after an update, so a running session would go on executing these scripts
// until `/reload-plugins`. The host records what it installed in
// <plugins>/installed_plugins.json (#172). When that record names another
// install of this same plugin — a newer version with the same major, holding
// the same script — the loaded script runs that copy with the same arguments
// and input and relays what it printed and how it exited.
//
// Codex resolves the plugin root again at every hook call, so its sessions
// already run the installed version; its cache has no record beside the
// package root and no hand-off happens there.
//
// Anything unexpected is no hand-off: the loaded script then runs exactly as
// it would without this file. Local and offline; nothing is installed,
// fetched, or written.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const MARKER = "KEEL_HOOK_FORWARDED";

function pluginVersion(pluginDir) {
  try {
    const manifest = path.join(pluginDir, ".claude-plugin", "plugin.json");
    const value = JSON.parse(fs.readFileSync(manifest, "utf8")).version;
    return typeof value === "string" && value.trim() ? value.trim() : null;
  } catch {
    return null;
  }
}

function parts(version) {
  const match = /^(\d+)\.(\d+)\.(\d+)/.exec(version || "");
  return match ? match.slice(1, 4).map(Number) : null;
}

// Only a newer release in the same major. A different major is allowed to
// change what a hook receives or returns, which a loaded script must not
// relay on the new copy's behalf.
function compatibleNewer(running, candidate) {
  const a = parts(running);
  const b = parts(candidate);
  if (!a || !b || a[0] !== b[0]) return false;
  for (let i = 1; i < 3; i += 1) {
    if (b[i] !== a[i]) return b[i] > a[i];
  }
  return false;
}

// The one other install of this plugin the host recorded, compared through
// real paths the way session-start.js's pendingInstall does.
function recordedInstall(root) {
  const record = path.join(root, "..", "..", "..", "..", "installed_plugins.json");
  const plugins = JSON.parse(fs.readFileSync(record, "utf8")).plugins;
  const found = new Set();
  for (const entries of Object.values(plugins || {})) {
    for (const entry of Array.isArray(entries) ? entries : []) {
      if (!entry || typeof entry.installPath !== "string") continue;
      let installPath;
      try {
        installPath = fs.realpathSync(path.resolve(entry.installPath));
      } catch {
        continue;
      }
      if (path.dirname(installPath) !== path.dirname(root)) continue;
      if (installPath === root) continue;
      found.add(installPath);
    }
  }
  return found.size === 1 ? [...found][0] : null;
}

// Where this script's newer copy is, or null for no hand-off.
function handOffTarget(scriptFile) {
  if (process.env[MARKER]) return null;
  try {
    const scriptDir = path.dirname(fs.realpathSync(scriptFile));
    const pluginDir = path.dirname(scriptDir);
    const root = path.dirname(path.dirname(pluginDir));
    // A Claude install is the tagged repository: its root carries the Claude
    // manifest and the plugin under plugins/keel. A Codex install is the
    // plugin directory itself and has neither.
    if (!fs.existsSync(path.join(root, ".claude-plugin", "plugin.json"))) return null;
    const running = pluginVersion(pluginDir);
    if (!running) return null;
    const other = recordedInstall(root);
    if (!other) return null;
    const relative = path.relative(root, path.join(scriptDir, path.basename(scriptFile)));
    const script = path.join(other, relative);
    const otherPlugin = path.join(other, path.relative(root, pluginDir));
    const version = pluginVersion(otherPlugin);
    if (!compatibleNewer(running, version) || !fs.existsSync(script)) return null;
    return { script, root: other, running, version };
  } catch {
    return null;
  }
}

// Runs the newer copy of `scriptFile` with `input` on stdin when there is one.
// Returns its exit status after relaying its output, or null when there was no
// hand-off or the copy could not run to completion — a spawn error, a timeout,
// or a signal — in which case nothing has been written and the caller runs its
// own logic.
function handOff(scriptFile, input, timeoutMs) {
  const target = handOffTarget(scriptFile);
  if (!target) return null;
  const budget = Number(process.env.KEEL_HOOK_FORWARD_TIMEOUT_MS || timeoutMs) || timeoutMs;
  const result = spawnSync(process.execPath, [target.script, ...process.argv.slice(2)], {
    input,
    encoding: "utf8",
    timeout: budget,
    env: { ...process.env, [MARKER]: target.running, CLAUDE_PLUGIN_ROOT: target.root },
  });
  if (result.error || result.signal || typeof result.status !== "number") return null;
  if (result.stdout) process.stdout.write(result.stdout);
  if (result.stderr) process.stderr.write(result.stderr);
  return result.status;
}

module.exports = { handOff, handOffTarget, MARKER };
