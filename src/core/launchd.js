"use strict";

// What the LaunchAgents Keel prints or writes (`keel tick task`, `keel chat
// wake add`, the chat bridge) name, so that they outlive a package upgrade
// (#387). A launchd job runs long after the shell that rendered it.
const fs = require("fs");
const os = require("os");
const path = require("path");

// `process.execPath` is the binary's real location, which `brew upgrade` moves
// (`/opt/homebrew/Cellar/node/<version>/bin/node`). The `node` a person types is
// the symlink the manager keeps current, so a name on PATH that resolves to this
// same binary is the one to write; when none does, the real path is all there is.
function stableNode(env = process.env) {
  const exec = process.execPath;
  let real;
  try {
    real = fs.realpathSync(exec);
  } catch {
    return exec;
  }
  for (const dir of String(env.PATH || "").split(path.delimiter)) {
    if (!dir) continue;
    const candidate = path.join(dir, "node");
    try {
      if (fs.realpathSync(candidate) === real) return candidate;
    } catch {
      // not on this directory
    }
  }
  return exec;
}

// A Claude plugin cache directory belongs to one release (`…/keel/5.149.0/bin`)
// and is stale after the next update. The jobs call node and keel.js by
// absolute path, so nothing in it is needed.
const PLUGIN_CACHE = /[\\/]\.claude[\\/]plugins[\\/]cache[\\/]/;

function launchdPath(value) {
  const text = value || "/usr/bin:/bin:/usr/sbin:/sbin";
  return text.split(path.delimiter).filter((dir) => dir && !PLUGIN_CACHE.test(`${dir}${path.sep}`)).join(path.delimiter);
}

function agentsDir() {
  return process.env.KEEL_CHAT_LAUNCH_AGENTS_DIR || path.join(os.homedir(), "Library", "LaunchAgents");
}

const RECREATE = [
  [/^dev\.keel\.tick\./, "keel tick task"],
  [/^dev\.keel\.chat-wake\./, "keel chat wake add"],
  [/^dev\.keel\.chat-bridge/, "keel chat bridge install"],
];

// Each `dev.keel.*` LaunchAgent with the program it runs and whether that exists.
function inspectJobs() {
  let names = [];
  try {
    names = fs.readdirSync(agentsDir()).filter((name) => /^dev\.keel\..*\.plist$/.test(name)).sort();
  } catch {
    return [];
  }
  return names.map((name) => {
    let text = "";
    try {
      text = fs.readFileSync(path.join(agentsDir(), name), "utf8");
    } catch {
      // unreadable: reported as no program below
    }
    const match = text.match(/<key>ProgramArguments<\/key>\s*<array>\s*<string>([^<]*)<\/string>/);
    const program = match ? match[1].replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&") : null;
    const recreate = (RECREATE.find(([pattern]) => pattern.test(name)) || [null, "the command that wrote it"])[1];
    return { name, program, exists: Boolean(program) && fs.existsSync(program), recreate };
  });
}

module.exports = { stableNode, launchdPath, inspectJobs };
