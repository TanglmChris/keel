#!/usr/bin/env node
"use strict";

// Keel plugin SessionStart projection: disposable context only.
// OpenSpec and Git stay the durable authority; this script never writes
// state, selects an ambiguous owner, records a fingerprint, creates a goal,
// or blocks the session. It always exits 0.
//
// The projection is source-aware: a compact start reinjects the recomputed
// task pointer (selection, recorded Contract fingerprint, next command) that
// a summary is most likely to lose, a resume start reinjects the selection,
// and startup, clear, or any unknown source falls back to the generic view.

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

// A newer installed copy of this script runs in its place when the host has
// installed one (forward.js, #204). A copy of this script without forward.js
// beside it simply runs its own logic.
let handOff = () => null;
try {
  ({ handOff } = require("./forward"));
} catch {
  // Copied on its own: no hand-off.
}

// This text is injected into the agent; the human reads the `systemMessage`
// line instead. Both channels ship on every branch, degraded ones included,
// and neither makes the other redundant: the host's line says what the state
// is, and this instruction is what surfaces the state the agent actually
// worked from, which is the one a user can catch being wrong.
const DISCLOSURE = "to the user in your first reply";

const TIMEOUT_MS = Number(process.env.KEEL_HOOK_TIMEOUT_MS || 8000) || 8000;
const MAX_REASONS = 3;
const MAX_REASON_LENGTH = 300;

function readStdin() {
  try {
    return fs.readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

// The human line rides the host's `systemMessage` field, which is rendered to
// the person at session start without waiting for them to type. It is a second
// channel, not a replacement: `additionalContext` still carries the full
// projection to the agent, and a host that does not recognize the field simply
// ignores it and leaves today's behavior intact.
function emit(context, humanMessage) {
  const payload = {};
  if (humanMessage) payload.systemMessage = humanMessage;
  payload.hookSpecificOutput = {
    hookEventName: "SessionStart",
    additionalContext: context,
  };
  process.stdout.write(`${JSON.stringify(payload)}\n`);
}

// Stated on the human line as well as the model payload: the person reading it
// at session start is the one who must not mistake a projection for authority.
const DISPOSABLE = "Disposable projection; OpenSpec and Git are the authority.";

// A pointer, never a body. The store grows without bound while the precedents
// relevant to any one session are a small subset, and this hook pays its cost
// on every session including post-compaction reinjection. Counts and freshness
// tell the agent the store exists and how stale it is; the precedents
// themselves load when a decision is actually being made.
//
// The reader is inlined rather than required from src/core because this script
// ships inside the plugin and must run without the CLI package resolvable.
function precedentPointer(cwd) {
  let declared = null;
  try {
    const configPath = path.join(cwd, "keel", "config.yaml");
    if (!fs.existsSync(configPath)) return null;
    for (const line of fs.readFileSync(configPath, "utf8").split(/\r?\n/)) {
      const stripped = line.trim();
      if (stripped.startsWith("#")) continue;
      const match = stripped.match(/^precedents\s*:\s*(.+?)\s*$/);
      if (match) {
        declared = match[1];
        break;
      }
    }
    if (!declared) return null;
    const resolved = path.isAbsolute(declared)
      ? declared
      : path.resolve(cwd, declared);
    if (!fs.existsSync(resolved) || !fs.statSync(resolved).isDirectory()) {
      return `precedent store declared at ${declared} but absent here; `
        + "no precedent informs any decision.";
    }
    const files = fs
      .readdirSync(resolved)
      .filter((name) => name.endsWith(".md") && name !== "README.md");
    let authorized = 0;
    let newest = 0;
    for (const name of files) {
      const full = path.join(resolved, name);
      if (/^-\s*Status:\s*authorized/mi.test(fs.readFileSync(full, "utf8"))) {
        authorized += 1;
      }
      const mtime = fs.statSync(full).mtimeMs;
      if (mtime > newest) newest = mtime;
    }
    const synced = newest
      ? new Date(newest).toISOString().slice(0, 10)
      : "never";
    return `precedents: ${files.length} (${authorized} authorized, `
      + `last synced ${synced}); bodies load at the decision, not here.`;
  } catch {
    // The projection never blocks a session. An unreadable store is the same
    // as no store for this hook's purposes.
    return null;
  }
}

// The remedy is the host's, so it is named rather than run. Only Claude's
// command is stated outright, because that is the manifest whose host command
// Keel has verified; an unprobed target gets a description instead of an
// invented command line.
const HOST_UPDATE = "your host's own plugin update command";

// The plugin's own manifest sits beside this script, so its version is read
// from `__dirname` rather than from CLAUDE_PLUGIN_ROOT: the path this file was
// loaded from is a fact, while an environment variable is a claim the host may
// not have made. Whichever target's manifest is present is the one that ran.
function pluginManifest() {
  const targets = [
    [".claude-plugin", "`claude plugin update`"],
    [".codex-plugin", HOST_UPDATE],
  ];
  for (const [dir, remedy] of targets) {
    try {
      const manifest = path.join(__dirname, "..", dir, "plugin.json");
      const value = JSON.parse(fs.readFileSync(manifest, "utf8")).version;
      if (typeof value === "string" && value.trim()) {
        return { version: value.trim(), remedy };
      }
    } catch {
      // A missing or unreadable manifest is undiscoverable, not drift.
    }
  }
  return { version: null, remedy: HOST_UPDATE };
}

// On Claude the plugin is the repository's tagged tree, cached at
// <plugins>/cache/<marketplace>/<plugin>/<version>, and the host records what
// it installed in <plugins>/installed_plugins.json (#172). Another install of
// this same plugin at a different version means the update already happened
// and this session has not reloaded it. Located from this file's own path, like
// the manifest; anything unexpected is no pending install, which leaves the
// report exactly as it was.
function pendingInstall(loaded) {
  try {
    const root = fs.realpathSync(path.resolve(__dirname, "..", "..", ".."));
    const record = path.join(root, "..", "..", "..", "..", "installed_plugins.json");
    const plugins = JSON.parse(fs.readFileSync(record, "utf8")).plugins;
    const versions = new Set();
    for (const entries of Object.values(plugins || {})) {
      for (const entry of Array.isArray(entries) ? entries : []) {
        if (!entry || typeof entry.installPath !== "string") continue;
        // Compared through the real path: node loads this file through its
        // symlinks resolved, while the host records whatever path it chose.
        const installPath = path.resolve(entry.installPath);
        let parent;
        try {
          parent = fs.realpathSync(path.dirname(installPath));
        } catch {
          continue;
        }
        if (parent !== path.dirname(root)) continue;
        if (path.join(parent, path.basename(installPath)) === root) continue;
        if (typeof entry.version === "string") versions.add(entry.version.trim());
      }
    }
    if (versions.size !== 1) return null;
    const [version] = versions;
    return version && version !== loaded ? version : null;
  } catch {
    return null;
  }
}

// The repository states which protocol it runs in the managed block the
// installer wrote. AGENTS.md is the canonical carrier; CLAUDE.md is read second
// because a repository may carry only the target-native file.
function protocolVersion(cwd) {
  for (const name of ["AGENTS.md", "CLAUDE.md"]) {
    try {
      const text = fs.readFileSync(path.join(cwd, name), "utf8");
      const match = text.match(
        /<!--\s*keel:start\s+version=(\d+\.\d+\.\d+)\s*-->/
      );
      if (match) return match[1];
    } catch {
      // Same as above: absent is not mismatched.
    }
  }
  return null;
}

// Three versions are comparable in any repository: the plugin executing this
// hook, the CLI it just invoked, and the protocol version the repository
// stamped into its managed block. Keel reports the disagreement and stops
// there — installing and updating are the host's, which already has commands
// for both.
function versionReport(cwd, cli, pathCli = null) {
  const plugin = pluginManifest();
  const found = [
    ["plugin", plugin.version],
    ["CLI", cli],
    ["protocol", protocolVersion(cwd)],
  ];
  // A PATH copy is compared only when it exists. Its absence is the
  // plugin-only install, which is not drift and not an unread version.
  if (pathCli) found.push(["PATH keel", pathCli]);
  // Missing is not mismatched. A version nobody can discover never produces a
  // line on its own, or a repository with no managed block would be warned at
  // every session until its reader stopped looking — and fewer than two
  // readable versions is not agreement either, it is nothing to compare.
  const known = found.filter(([, value]) => value);
  if (known.length < 2) return null;
  // Silence when they agree. This line exists to be noticed, and one printed
  // every session stops being read long before the session it mattered in.
  if (new Set(known.map(([, value]) => value)).size === 1) return null;
  const named = known.map(([name, value]) => `${name} ${value}`).join(", ");
  // Naming what was never read is what keeps a partial comparison from being
  // read as a complete one.
  const unread = found
    .filter(([, value]) => !value)
    .map(([name]) => name)
    .join(" and ");
  const missing = unread ? ` (${unread} undiscovered, not compared)` : "";
  // Naming the reload rather than a restart (#164): the host's
  // `/reload-plugins` swaps hooks in the running session, so "restart" sent
  // the reader to the expensive remedy for a cheap one.
  // The host puts the user's PATH ahead of plugin `bin/` directories, so a
  // global install is what the agent's own `keel` commands run even though
  // this hook ran the plugin's. Both remedies are named; neither is run.
  const pending = pendingInstall(plugin.version);
  // With an installed update pending, the PATH copy is judged against what
  // the reload will load: one that matches it shadows nothing afterwards, and
  // aligning with the loaded plugin would be a downgrade (#172).
  const target = pending || cli;
  const shadow = pathCli && pathCli !== target
    ? ` The \`keel\` on PATH (${pathCli}) shadows this plugin's CLI for the `
      + "agent's commands, because the host puts your PATH first: remove it "
      + "with `npm rm -g @christang/keel`, since the plugin carries its own, "
      + `or align it with \`npm i -g @christang/keel@${target}\`.`
    : "";
  // An update the host already installed needs only the reload (#172), so
  // naming the update command there sends the reader to what already happened.
  const remedy = pending
    ? `The host has already installed plugin ${pending}, so nothing needs updating.`
    : `Updating is ${plugin.remedy}, which Keel names and does not run.`;
  return `runtime versions disagree: ${named}${missing}. A session's hooks are `
    + "fixed when it loads the plugin, so an updated plugin applies after "
    + `\`/reload-plugins\` or at the next session start. ${remedy}${shadow}`;
}

// A handed-off run (forward.js, #204) executes the installed version, so its
// hooks, CLI, and version report are already the new ones. What it cannot
// bring forward is what the host loaded when the session started: skills,
// agents, and the declared hooks. They are compared between the loaded tree —
// the cache keeps each version under its own name beside this one — and this
// tree, and only a difference earns a line, naming the reload and nothing
// else. A loaded tree that cannot be found is reported as possibly different,
// because silence would claim a comparison that never happened.
function treeDigest(dir) {
  const hash = require("crypto").createHash("sha256");
  const walk = (current, prefix) => {
    let entries;
    try {
      entries = fs.readdirSync(current, { withFileTypes: true });
    } catch {
      return;
    }
    for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
      const full = path.join(current, entry.name);
      const name = `${prefix}${entry.name}`;
      if (entry.isDirectory()) {
        walk(full, `${name}/`);
      } else if (entry.isFile()) {
        hash.update(`${name}\0`);
        hash.update(fs.readFileSync(full));
        hash.update("\0");
      }
    }
  };
  walk(dir, "");
  return hash.digest("hex");
}

function declaredHooks(root) {
  try {
    const manifest = path.join(root, ".claude-plugin", "plugin.json");
    return JSON.stringify(JSON.parse(fs.readFileSync(manifest, "utf8")).hooks || null);
  } catch {
    return null;
  }
}

function adoptionReport() {
  const loadedVersion = (process.env.KEEL_HOOK_FORWARDED || "").trim();
  if (!loadedVersion) return null;
  const running = pluginManifest().version;
  const root = path.resolve(__dirname, "..", "..", "..");
  const loaded = path.join(path.dirname(root), loadedVersion);
  let differs;
  if (!fs.existsSync(path.join(loaded, ".claude-plugin", "plugin.json"))) {
    differs = "skills, agents, or hooks may differ";
  } else {
    const changed = [];
    for (const [name, rel] of [["skills", "plugins/keel/skills"], ["agents", "plugins/keel/agents"]]) {
      if (treeDigest(path.join(loaded, rel)) !== treeDigest(path.join(root, rel))) changed.push(name);
    }
    if (declaredHooks(loaded) !== declaredHooks(root)) changed.push("declared hooks");
    if (changed.length === 0) return null;
    differs = `${changed.join(" and ")} changed`;
  }
  return `hooks now run the installed plugin ${running} in place of the loaded `
    + `${loadedVersion}; its ${differs}, and \`/reload-plugins\` loads them — the `
    + "only step left.";
}

// The `keel` a bare command resolves, asked only when this hook ran its own
// CLI; with no such command there is nothing to compare.
function pathCliVersion(cwd) {
  const probe = runKeel(cwd, ["--version"], "keel");
  if (probe.error || probe.status !== 0) return null;
  const match = String(probe.stdout || "").match(/\d+\.\d+\.\d+/);
  return match ? match[0] : null;
}

// The Keel mark. A keel is the carina, the ridge on a bird's sternum, so the
// animal that literally has one is a bird. Every cell is drawn from
// U+2580–U+259F — the same block-element family as the host's own startup
// banner — because those code points are East-Asian-Ambiguous width: pinning
// the charset is what keeps the rows aligned under a CJK locale, and matters
// more than the shape. The rows are padded to equal width so that a future
// edit which breaks the rectangle is caught rather than silently skewed.
const MARK = [
  "▙▖▛▀▜  ▛▀▜▗▟",
  "  ▌█▐  ▌█▐  ",
  "  ▙▄▟▚▞▙▄▟  ",
].join("\n");

// The frame is modelled on the host's own welcome panel and draws from
// U+2500–U+257F, a different range than the mark. Its width is the longest
// content row, so a long change name widens the panel instead of being cut:
// the identifier is the most useful thing in the projection, and truncating
// the payload to preserve the frame would invert what the frame is for.
// Leads with a newline because the host prefixes the message with
// `<hookEvent>:<source> says: `, which would otherwise push the top rule out
// of line with the rows beneath it.
// Opt-in. The single line is what answers the reported problem — nobody is
// told anything at session start — and it ships on. The panel is presentation,
// and presentation that appears unbidden in every session of every install
// should be chosen rather than inherited. The allowlist is explicit so a typo
// leaves the default in place instead of quietly switching it on.
const PANEL_TITLE = "Keel";
const PANEL_ENABLED = /^(1|true|on|yes)$/i.test(
  String(process.env.KEEL_SESSION_PANEL || "").trim()
);

function panel(lines) {
  if (!PANEL_ENABLED) return lines.join(" ");
  const rows = [...MARK.split("\n"), "", ...lines];
  const width = Math.max(
    ...rows.map((row) => row.length),
    PANEL_TITLE.length + 8
  );
  const centred = rows.map((row) => {
    if (!row) return "";
    const isMark = /^[▀-▟ ]+$/.test(row);
    if (!isMark) return row;
    const pad = Math.floor((width - row.length) / 2);
    return " ".repeat(pad) + row;
  });
  const head = `─── ${PANEL_TITLE} `;
  return [
    "",
    `╭${head}${"─".repeat(width + 2 - head.length)}╮`,
    ...centred.map((row) => `│ ${row.padEnd(width)} │`),
    `╰${"─".repeat(width + 2)}╯`,
  ].join("\n");
}

// On Claude the plugin is the repository's tagged tree (#164), so the CLI it shipped
// with sits three levels above this script. It is recognized by the package's
// name and not by the path alone: a Codex cache holds only `plugins/keel`, and
// whatever lies above that is not this plugin's to run.
function packagedCli() {
  const root = path.join(__dirname, "..", "..", "..");
  try {
    const pkg = JSON.parse(
      fs.readFileSync(path.join(root, "package.json"), "utf8")
    );
    const cli = path.join(root, "bin", "keel.js");
    if (pkg.name === "@christang/keel" && fs.existsSync(cli)) return cli;
  } catch {
    // No package around this script: the plugin was copied on its own.
  }
  return null;
}

// An explicit KEEL_CLI first, then the CLI this plugin shipped with, then
// whatever `keel` is on PATH. The packaged CLI runs under the node running
// this hook, so it needs neither PATH nor an executable mode.
function keelCommand() {
  const explicit = (process.env.KEEL_CLI || "").trim();
  if (explicit) return { command: explicit, packaged: false };
  const own = packagedCli();
  if (own) {
    return { command: `"${process.execPath}" "${own}"`, packaged: true };
  }
  return { command: "keel", packaged: false };
}

function runKeel(cwd, args, cli) {
  return spawnSync(`${cli} ${args.join(" ")}`, {
    cwd,
    shell: true,
    encoding: "utf8",
    timeout: TIMEOUT_MS,
  });
}

// A degraded projection needs the human line most: a hook that fails silently
// is indistinguishable from a hook that never ran, which is how this whole
// failure mode was reported in the first place.
function fallback(reason) {
  emit(
    `Keel hook fallback: ${reason} Run \`keel context\` manually; `
      + "OpenSpec and Git remain the durable authority. Report this failure "
      + `and that command ${DISCLOSURE}.`,
    panel([
      `Keel: projection unavailable — ${reason} Next: keel context.`,
      DISPOSABLE,
    ])
  );
}

function main() {
  const input = readStdin();
  const handed = handOff(__filename, input, 12000);
  if (handed !== null) return handed;
  let event = {};
  try {
    event = JSON.parse(input || "{}");
  } catch {
    event = {};
  }
  const cwd =
    typeof event.cwd === "string" && event.cwd ? event.cwd : process.cwd();

  if (!fs.existsSync(path.join(cwd, "openspec"))) {
    return 0;
  }

  const cli = keelCommand();
  const version = runKeel(cwd, ["--version"], cli.command);
  const versionMatch = String(version.stdout || "").match(/(\d+)\.\d+\.\d+/);
  if (
    version.error
    || version.status !== 0
    || !versionMatch
    || Number(versionMatch[1]) < 3
  ) {
    fallback(
      "the keel CLI is missing or incompatible with this plugin; install "
        + "@christang/keel (npm install -g @christang/keel)."
    );
    return 0;
  }

  const result = runKeel(cwd, ["context", "--json"], cli.command);
  if (result.error || result.status !== 0 || !String(result.stdout || "").trim()) {
    fallback("`keel context --json` failed or timed out.");
    return 0;
  }
  let context;
  try {
    context = JSON.parse(result.stdout);
  } catch {
    fallback("keel produced malformed context output.");
    return 0;
  }

  const source = typeof event.source === "string" ? event.source : "";
  const reinject = source === "compact" || source === "resume";
  const header = source === "compact"
    ? "Keel post-compaction reinjection (disposable; recomputed from OpenSpec and Git):"
    : source === "resume"
      ? "Keel resume reinjection (disposable; recomputed from OpenSpec and Git):"
      : "Keel session projection (disposable; OpenSpec and Git are the durable authority):";

  const lines = [header];
  let human = [];
  if (context.status === "ready" && context.selection) {
    const task = context.selection.task ? `#${context.selection.task}` : "";
    human = [
      `Keel: ${context.selection.change}${task} — next: `
        + `${context.nextAction ? context.nextAction.kind : "unknown"}.`,
      DISPOSABLE,
    ];
    lines.push(
      `- context ready: ${context.selection.change}${task} `
        + `(${context.selection.source}); next action: `
        + `${context.nextAction ? context.nextAction.kind : "unknown"}.`
    );
    if (reinject) {
      const recorded = recordedContract(cwd, context.selection);
      if (recorded) {
        lines.push(
          `- recorded Contract fingerprint: ${recorded} (recorded, not `
            + "verified; gates recompile and compare before any write)."
        );
      }
      lines.push(
        "- next: re-run `keel context --json`, then `keel gate task-start` "
          + "before continuing implementation; nothing was selected or "
          + "recorded by this projection."
      );
    } else {
      if (Array.isArray(context.read) && context.read.length > 0) {
        lines.push(`- read first: ${context.read.slice(0, 5).join(", ")}.`);
      }
      lines.push(
        "- run `keel gate task-start` before implementation; this projection "
          + "selects nothing and records nothing."
      );
    }
  } else {
    const status = context.status || "unknown";
    const reasons = (context.reasons || []).slice(0, MAX_REASONS);
    human = [
      `Keel: ${status}`
        + (reasons.length > 0
          ? ` — ${String(reasons[0]).slice(0, MAX_REASON_LENGTH)}`
          : "")
        + " Next: keel context.",
      DISPOSABLE,
    ];
    lines.push(`- context status: ${status}.`);
    for (const reason of reasons) {
      lines.push(`- reason: ${String(reason).slice(0, MAX_REASON_LENGTH)}`);
    }
    lines.push(
      "- next: run `keel context` and select an owner explicitly; this hook "
        + "does not guess among candidates."
    );
  }
  const drift = versionReport(
    cwd,
    versionMatch[0],
    cli.packaged ? pathCliVersion(cwd) : null
  );
  const adoption = adoptionReport();
  if (adoption) {
    lines.push(`- ${adoption}`);
    human.splice(human.length - 1, 0, adoption[0].toUpperCase() + adoption.slice(1));
  }
  if (drift) {
    lines.push(`- ${drift}`);
    human.splice(human.length - 1, 0, drift[0].toUpperCase() + drift.slice(1));
  }
  const pointer = precedentPointer(cwd);
  if (pointer) lines.push(`- ${pointer}`);
  lines.push(`- report this state ${DISCLOSURE}; it authorizes nothing.`);
  emit(lines.join("\n"), panel(human));
  return 0;
}

function recordedContract(repo, selection) {
  if (!selection || !selection.change || !selection.task) return null;
  const tasksPath = path.join(
    repo,
    "openspec",
    "changes",
    selection.change,
    "tasks.md"
  );
  let content = "";
  try {
    content = fs.readFileSync(tasksPath, "utf8");
  } catch {
    return null;
  }
  const wanted = String(selection.task);
  let inTask = false;
  for (const line of content.split(/\r?\n/)) {
    const heading = line.match(/^\s*-\s+\[[ xX]\]\s+(\d+(?:\.\d+)+)\s+/);
    if (heading) {
      inTask = heading[1] === wanted;
      continue;
    }
    if (!inTask) continue;
    const contract = line.match(/^\s*-\s*Contract:\s*(sha256:[0-9a-f]{64})\b/);
    if (contract) return contract[1];
  }
  return null;
}

process.exit(main());
