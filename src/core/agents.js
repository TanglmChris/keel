"use strict";

// External model CLIs as delegates (#219).
//
// Keel describes an external agent and compiles the brief it is handed; it never
// launches one. The session's own shell runs the command, which keeps Keel the
// tool that starts no process and sends nothing, as everywhere else in it.
//
// The catalog records facts a reader can check — the command template, the
// sandbox offered per mode, where data goes, and pitfalls each stamped with a
// date and a source. It carries no field saying what an agent is good at: a
// judgement resident in the session steers the agent that reads it, and goes
// stale with the next model version (owner, 2026-10-04). Which work suits an
// external agent is the project's to write, the way lenses are.

const fs = require("fs");
const os = require("os");
const path = require("path");

const { readExternalAgents } = require("./config");

const FIELDS = ["executable", "command", "sandbox", "sendsTo", "pitfalls"];
const MODES = ["helper", "implementation"];

const RTL_TOOLCHAIN = "rtl_ppa_prj docs/toolchain.md (main 632ad85)";

const BUNDLED = {
  codex: {
    executable: "codex",
    command: "{executable} exec -s {sandbox} -C {dir} -o {out} - < {prompt}",
    sandbox: { helper: "read-only", implementation: "workspace-write" },
    sendsTo: "OpenAI, under the account codex is signed in with",
    pitfalls: [
      {
        date: "2026-10-04",
        source: RTL_TOOLCHAIN,
        text: "Given a prompt argument and no stdin, it waits on stdin forever. Pass the prompt on stdin with `-`, or redirect `< /dev/null`.",
      },
      {
        date: "2026-10-01",
        source: RTL_TOOLCHAIN,
        text: "`codex exec resume` against a Codex Desktop thread breaks on version, write lock, and session format. Start a fresh `codex exec` and put the context in the prompt file.",
      },
      {
        date: "2026-10-04",
        source: RTL_TOOLCHAIN,
        text: "It has a usage quota. When the quota is hit it names the time it can retry.",
      },
      {
        date: "2026-10-02",
        source: "https://github.com/TanglmChris/keel/issues/194",
        text: "A recurring check that asks the model to poll for messages burned the whole quota. Never have it poll with the model.",
      },
      {
        date: "2026-10-04",
        source: "codex exec --help, codex-cli 0.159.3",
        text: "`-s` takes read-only, workspace-write, or danger-full-access. `-C` sets the directory it works in and `-o` the file its last message is written to.",
      },
    ],
  },
  dsh: {
    executable: "/Applications/DeepSeek Harness.app/Contents/Resources/runtime/cli/bin/dsh",
    command: "cd {dir} && {executable} --profile headless - < {prompt} > {out}",
    sandbox: { helper: null, implementation: null },
    sendsTo: "DeepSeek, through the provider the profile configures (by default deepseek-official, model deepseek-flash)",
    pitfalls: [
      {
        date: "2026-10-04",
        source: "dsh --version, 0.2.0-rc.2",
        text: "The CLI lives inside the app bundle and is not on PATH.",
      },
      {
        date: "2026-10-04",
        source: "dsh headless --help, 0.2.0-rc.2",
        text: "It offers no sandbox flag and no working-directory flag. It reads and writes wherever it is started, so start it in a separate worktree.",
      },
      {
        date: "2026-10-04",
        source: "dsh headless --help, 0.2.0-rc.2",
        text: "`--json` writes newline-delimited run events instead of the final message, and `--session-id <id>` adopts an existing session.",
      },
    ],
  },
};

// Pitfalls of handing work to any external process, whichever CLI it is.
const GENERAL_PITFALLS = [
  {
    date: "2026-10-04",
    source: RTL_TOOLCHAIN,
    text: "Never share a branch or worktree with it. A delegate committed on the branch another session had checked out, staled that session's index, and nearly overwrote its commits.",
  },
  {
    date: "2026-10-04",
    source: RTL_TOOLCHAIN,
    text: "Its shell does not inherit your environment script. Write the PATH it needs into the brief.",
  },
  {
    date: "2026-10-04",
    source: "https://github.com/TanglmChris/rtl_ppa_prj/issues/104",
    text: "Bound the run and name its product. A verification handed over to run on its own for ten hours spent most of it packaging and uploading about 1.9 GB of evidence.",
  },
  {
    date: "2026-10-04",
    source: RTL_TOOLCHAIN,
    text: "macOS has no `timeout`. Run it in the background and watch it yourself.",
  },
];

function keelHome() {
  return process.env.KEEL_HOME || path.join(os.homedir(), ".keel");
}

function machineFile() {
  return path.join(keelHome(), "agents.json");
}

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

// The machine file adds entries and overrides fields. A field it declares
// outside the fact fields is reported and dropped, so the file cannot carry the
// judgement the bundle leaves out. A file Keel cannot parse contributes nothing:
// half of a file is a catalog nobody wrote.
function readMachineEntries(problems) {
  const file = machineFile();
  if (!fs.existsSync(file)) return {};
  let parsed;
  try {
    parsed = JSON.parse(fs.readFileSync(file, "utf8"));
  } catch (error) {
    problems.push(`${file} is not valid JSON (${error.message}); none of its entries are used.`);
    return {};
  }
  const agents = parsed && typeof parsed === "object" ? parsed.agents : null;
  if (!agents || typeof agents !== "object" || Array.isArray(agents)) {
    problems.push(`${file} has no "agents" object; none of its entries are used.`);
    return {};
  }
  return agents;
}

function loadCatalog() {
  const problems = [];
  const entries = {};
  for (const [name, entry] of Object.entries(BUNDLED)) {
    entries[name] = { name, source: "bundled", ...clone(entry) };
  }
  for (const [name, declared] of Object.entries(readMachineEntries(problems))) {
    if (!declared || typeof declared !== "object" || Array.isArray(declared)) {
      problems.push(`agents.json entry ${name} is not an object; it is not used.`);
      continue;
    }
    const unknown = Object.keys(declared).filter((key) => !FIELDS.includes(key));
    if (unknown.length > 0) {
      problems.push(
        `agents.json entry ${name} declares ${unknown.join(", ")}, outside the fact fields `
          + `(${FIELDS.join(", ")}); ${unknown.length === 1 ? "it was" : "they were"} dropped.`
      );
    }
    const base = entries[name] || { name, sandbox: { helper: null, implementation: null }, pitfalls: [] };
    const merged = { ...base, source: "machine" };
    for (const key of FIELDS) {
      if (key in declared) merged[key] = clone(declared[key]);
    }
    if (!merged.executable || !merged.command) {
      problems.push(`agents.json entry ${name} names no executable or no command; it is not used.`);
      continue;
    }
    merged.sandbox = { helper: null, implementation: null, ...(merged.sandbox || {}) };
    merged.pitfalls = Array.isArray(merged.pitfalls) ? merged.pitfalls : [];
    entries[name] = merged;
  }
  return { entries, problems };
}

function isExecutable(file) {
  try {
    fs.accessSync(file, fs.constants.X_OK);
    return fs.statSync(file).isFile();
  } catch {
    return false;
  }
}

// An absolute path resolves when it exists; a bare name is looked up on PATH.
function resolveExecutable(executable) {
  if (path.isAbsolute(executable)) return isExecutable(executable) ? executable : null;
  for (const dir of (process.env.PATH || "").split(path.delimiter)) {
    if (!dir) continue;
    const candidate = path.join(dir, executable);
    if (isExecutable(candidate)) return candidate;
  }
  return null;
}

function describeAgents(repo) {
  const { entries, problems } = loadCatalog();
  const declaration = readExternalAgents(repo);
  problems.push(...declaration.problems);
  const agents = Object.values(entries)
    .sort((a, b) => a.name.localeCompare(b.name))
    .map((entry) => ({
      name: entry.name,
      source: entry.source,
      executable: entry.executable,
      resolved: resolveExecutable(entry.executable),
      allowed: declaration.allow.includes(entry.name),
      command: entry.command,
      sandbox: entry.sandbox,
      sendsTo: entry.sendsTo || null,
      pitfalls: entry.pitfalls,
    }));
  return {
    schemaVersion: 1,
    command: "agents",
    agents,
    pitfalls: GENERAL_PITFALLS,
    declaration: {
      declared: declaration.declared,
      allow: declaration.allow,
      egressDeny: declaration.egressDeny,
    },
    problems,
    note: "Keel launches no agent. It lists the catalog and compiles the brief; the session runs the command.",
  };
}

function sandboxLine(sandbox) {
  return MODES.map((mode) => `${mode} ${sandbox[mode] || "none (needs a separate worktree)"}`).join("; ");
}

function pitfallLines(pitfalls) {
  return pitfalls.map((item) => `- ${item.date} (${item.source}): ${item.text}`);
}

function renderListing(payload) {
  const lines = ["External agents (read on demand; Keel launches none):"];
  for (const agent of payload.agents) {
    lines.push(
      `- ${agent.name} [${agent.source}] ${agent.resolved || "not found"} — `
        + (agent.allowed ? "allowed here" : "not allowed here")
    );
  }
  if (!payload.declaration.declared) {
    lines.push("This project declares no external_agents: block, so it allows none.");
  }
  lines.push("", "General pitfalls:", ...pitfallLines(payload.pitfalls));
  for (const problem of payload.problems) lines.push(`Problem: ${problem}`);
  lines.push("", "Show one: keel agents <name>");
  return `${lines.join("\n")}\n`;
}

function renderAgent(payload, agent) {
  const lines = [
    `${agent.name} [${agent.source}]`,
    `Executable: ${agent.executable} → ${agent.resolved || "not found"}`,
    `Command: ${agent.command}`,
    `Sandbox: ${sandboxLine(agent.sandbox)}`,
    `Sends to: ${agent.sendsTo || "not recorded"}`,
    `Allowed here: ${agent.allowed ? "yes" : "no"}`,
    "",
    "Pitfalls:",
    ...pitfallLines(agent.pitfalls),
    "",
    "General pitfalls:",
    ...pitfallLines(payload.pitfalls),
  ];
  for (const problem of payload.problems) lines.push(`Problem: ${problem}`);
  return `${lines.join("\n")}\n`;
}

const USAGE = "usage: keel agents [name] [--repo path] [--json]";

function runAgents(argv) {
  let json = false;
  let repo = process.cwd();
  let name = null;
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--json") json = true;
    else if (arg === "--repo") repo = argv[++index] || "";
    else if (arg === "--help" || arg === "-h") {
      process.stdout.write(`${USAGE}\n`);
      return 0;
    } else if (name === null && !arg.startsWith("-")) name = arg;
    else {
      process.stderr.write(`keel agents: unexpected argument ${arg}\n${USAGE}\n`);
      return 2;
    }
  }
  const payload = describeAgents(path.resolve(repo));
  if (name !== null) {
    const agent = payload.agents.find((item) => item.name === name);
    if (!agent) {
      process.stderr.write(
        `keel agents: no agent named ${name}; known: ${payload.agents.map((item) => item.name).join(", ")}\n`
      );
      return 1;
    }
    process.stdout.write(json ? `${JSON.stringify({ ...payload, agents: [agent] }, null, 2)}\n`
      : renderAgent(payload, agent));
    return 0;
  }
  process.stdout.write(json ? `${JSON.stringify(payload, null, 2)}\n` : renderListing(payload));
  return 0;
}

module.exports = {
  BUNDLED,
  GENERAL_PITFALLS,
  describeAgents,
  loadCatalog,
  resolveExecutable,
  runAgents,
};
