#!/usr/bin/env node
"use strict";

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");
const {
  renderContext,
  resolveContext,
} = require("../src/core/context");
const {
  GateInputError,
  renderGate,
  runGate,
} = require("../src/core/gates");
const {
  isKeelSourceRepo,
  probeCapabilities,
  renderCapabilities,
} = require("../src/core/capabilities");
const {
  projectRuntime,
  renderProjection,
} = require("../src/core/projection");
const {
  GuardInputError,
  clearGuard,
  guardStatus,
  renderGuard,
  startGuard,
} = require("../src/core/guard");
const {
  STANDING_AUTHORIZATION_ACTIONS,
  readPrecedentStore,
  readStandingAuthorization,
  roleMatches,
  readFullModePaths,
  readExecutorTier,
  readMergeDeclaration,
  fullModePathsUnreadableMessage,
  readTriagePolicy,
  triageIssue,
} = require("../src/core/config");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const PACKAGE_JSON = require(path.join(PACKAGE_ROOT, "package.json"));
const INSTALL_SCRIPT = path.join(PACKAGE_ROOT, "scripts", "install_to_repo.py");
const DEFAULT_UPDATE_SOURCE = "@christang/keel";
const VALID_TARGETS = new Set(["claude", "codex", "opencode", "both"]);
const KEEL_SKILLS = [
  "align-expectations",
  "debug-failure",
  "review-checklist",
  "tdd-or-test-first",
];
const OPENSPEC_COMMAND_IDS = ["propose", "explore", "apply", "sync", "archive"];
const OPENSPEC_SKILLS = [
  "openspec-propose",
  "openspec-explore",
  "openspec-apply-change",
  "openspec-sync-specs",
  "openspec-archive-change",
];
// `sync` is here because `AGENTS.md` gates it exactly as it gates archive —
// `keel gate change-close --action sync|archive` plus `review-checklist`.
// Archive's surface said so and sync's said nothing, so an agent invoking
// the sync workflow read generic upstream instructions with no mention of the gate
// that decides whether the sync may complete. `explore` is deliberately absent:
// it reads and reports, reaches no gate, and changes no state, so an overlay
// there would read as governance where there is none.
const OPENSPEC_OVERLAY_ACTIONS = ["propose", "apply", "archive", "sync"];
const OPENSPEC_SURFACE_OVERLAY_START =
  `<!-- keel:openspec-surface-overlay version=${PACKAGE_JSON.version} -->`;
const OPENSPEC_SURFACE_OVERLAY_END =
  "<!-- keel:openspec-surface-overlay:end -->";
// The one thing a gated surface says about subagents (#414): neither a rule
// nor a nudge, because the gates and the Touch guard already bind whoever runs.
const SUBAGENT_SENTENCE =
  "- A subagent is the model's choice and is treated as the main agent is: the gates, the `Touch` write guard, and the evidence rules apply to whoever runs a step.";
const OPENSPEC_SURFACE_OVERLAY_RE =
  /<!--\s*keel:openspec-surface-overlay(?:\s+[^>]*)?\s*-->[\s\S]*?<!--\s*keel:openspec-surface-overlay:end\s*-->/;

const HELP = `keel ${PACKAGE_JSON.version}

Usage:
  keel context [repo] [--change name] [--task id] [--json] [--clear-handoff]
  keel capabilities [repo] [--target claude|codex|opencode] [--json]
  keel project --target claude|codex|opencode --event startup|resume|compaction|worktree [--expected-owner owner] [--change name] [--task id] [--json]
  keel gate task-start|task-complete [repo] [--change name] [--task id] [--base git-ref] [--no-guard] [--record] [--keep-evidence M1,M3] [--json]
  keel gate change-close [repo] [--change name] --action sync|archive [--base git-ref] [--json]
  keel guard start|status|clear [repo] [--change name] [--task id] [--force] [--json]
  keel lenses list|add [name] [repo] [--force]
  keel chat role|group|post|dm|unread|read|show|<group> ... [--repo path]   (group chat between sessions; see keel chat help)
  keel mail role|send|list|read|hook [repo] ...   (cross-host mailbox; see keel mail help)
  keel triage [repo] [--labels <l1,l2>] [--issue <n>] [--json]
  keel agents [name] [--repo path] [--json]   (external model CLIs, read on demand; Keel launches none)
  keel branches [repo] [--role <role>] [--json]   (a role's merged task branches, with their sha; fetches and deletes nothing)
  keel branches prune [repo] [--role <role>] [--json]   (delete them, local and remote, under authorize: delete-branch:merged; exit 3 without it)
  keel shift request|check|ready|start|resume|status ...   (a role's shift change; see keel shift --help)
  keel lock acquire|release|list ...                    (shared resource leases; see keel lock --help)
  keel worktrees [--repo <path>] [--issues <file>] [--json] (read-only worktree overview)
  keel patrol [--issues <file>] [--idle <dur>] [--since-last [--notify]] [--nudge] [--json] [--repo <path>]   (the coordinator's patrol; keel patrol task prints its schedule)
  keel tick [--repo <path>] [--json]                   (one model-free step for a host scheduler; keel tick task prints the job)
  keel openspec [args...]
  keel --init [repo] [--target claude|codex|opencode] [--dry-run] [--force-template-update]
  keel --install [repo] [--target claude|codex|opencode] [--dry-run] [--force-template-update] [--with-git-hooks]
  keel --clear [repo] [--target claude|codex|opencode] [--dry-run]
  keel --uninstall [repo] [--target claude|codex|opencode] [--dry-run]
  keel --update [--dry-run] [--source npm-package-or-git-spec] [--adopt]
  keel --check [repo] [--target claude|codex|opencode]
  keel --doctor [repo] [--target claude|codex|opencode]
  keel --version
  keel --help

Defaults:
  repo defaults to the current working directory.
  target defaults to claude.
  --update refreshes the global keel CLI and the Claude and Codex plugins it
  finds installed, not project protocol files.
  update source defaults to ${DEFAULT_UPDATE_SOURCE}.

Project layout:
  continuity is recomputed from OpenSpec on every invocation.
  keel/HANDOFF.md is an optional pointer override: YAML front matter holding
    schema: keel-handoff/v1, owner (a pointer into openspec/changes/<change>/),
    action (discuss, author, task-start, task-complete, or change-close), and
    reason, and no other field. keel context --clear-handoff removes it.
  keel-* behavioral skills are delivered by the installed Keel plugin, not by the CLI.
  repeat keel --install to refresh project protocol files.

Examples:
  keel context
  keel context --json
  keel context --change my-change --task 1.1
  keel context --clear-handoff
  keel gate task-start --change my-change --task 1.1 --json
  keel gate task-complete --change my-change --task 1.1 --json
  keel gate change-close --change my-change --action archive --json
  keel guard start --change my-change --task 1.1 --json
  keel guard status --json
  keel guard clear --json
  keel lenses list
  keel lenses add web
  keel lenses add web --force
  keel triage --labels auto
  keel triage --issue 42
  keel --init
  keel --install
  keel --install --target codex
  keel --install --target opencode
  keel --install --dry-run
  keel --check
  keel --doctor
  keel --install --force-template-update
  keel --install --with-git-hooks
  keel --update
  keel --update --dry-run
  keel --clear --dry-run
  keel --uninstall --dry-run
`;

function printHelp() {
  process.stdout.write(HELP);
}

function printVersion() {
  process.stdout.write(`keel ${PACKAGE_JSON.version}\n`);
}

function fail(message, exitCode = 2) {
  process.stderr.write(`keel: ${message}\n`);
  process.stderr.write("Run keel --help for usage.\n");
  process.exit(exitCode);
}

function parseArgs(argv) {
  const parsed = {
    action: null,
    repo: null,
    target: "claude",
    dryRun: false,
    forceTemplateUpdate: false,
    withGitHooks: false,
    updateSource: null,
    adopt: false,
    help: false,
    version: false,
    change: null,
    task: null,
    json: false,
    clearHandoff: false,
    gateStage: null,
    closeAction: null,
    base: null,
    noGuard: false,
    record: false,
    keepEvidence: null,
    guardSubcommand: null,
    lensesSubcommand: null,
    lensName: null,
    labels: null,
    issue: null,
    openspecArgs: [],
    force: false,
    projectionEvent: null,
    expectedOwner: null,
    projectSubcommand: null,
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--help" || arg === "-h") {
      parsed.help = true;
      continue;
    }
    if (arg === "--version" || arg === "-v") {
      parsed.version = true;
      continue;
    }
    if (arg === "context" && parsed.action === null && parsed.repo === null) {
      parsed.action = "context";
      continue;
    }
    if (arg === "gate" && parsed.action === null && parsed.repo === null) {
      parsed.action = "gate";
      continue;
    }
    if (arg === "guard" && parsed.action === null && parsed.repo === null) {
      parsed.action = "guard";
      continue;
    }
    if (arg === "lenses" && parsed.action === null && parsed.repo === null) {
      parsed.action = "lenses";
      continue;
    }
    if (arg === "triage" && parsed.action === null && parsed.repo === null) {
      parsed.action = "triage";
      continue;
    }
    if (arg === "--labels" && parsed.action === "triage") {
      parsed.labels = argv[++index] || "";
      continue;
    }
    if (arg === "--issue" && parsed.action === "triage") {
      parsed.issue = argv[++index] || "";
      continue;
    }
    if (arg === "openspec" && parsed.action === null && parsed.repo === null) {
      parsed.action = "openspec";
      parsed.openspecArgs = argv.slice(index + 1);
      break;
    }
    if (arg === "--force") {
      parsed.force = true;
      continue;
    }
    if (
      arg === "capabilities"
      && parsed.action === null
      && parsed.repo === null
    ) {
      parsed.action = "capabilities";
      continue;
    }
    if (arg === "project" && parsed.action === null && parsed.repo === null) {
      parsed.action = "project";
      continue;
    }
    if (
      ["--init", "--install", "--clear", "--uninstall", "--update", "--check", "--doctor"].includes(arg)
    ) {
      if (parsed.action !== null) {
        fail(`choose only one action; already saw ${parsed.action}`);
      }
      parsed.action = arg.slice(2);
      continue;
    }
    if (arg === "--dry-run") {
      parsed.dryRun = true;
      continue;
    }
    if (arg === "--json") {
      parsed.json = true;
      continue;
    }
    if (arg === "--clear-handoff") {
      parsed.clearHandoff = true;
      continue;
    }
    if (arg === "--no-guard") {
      parsed.noGuard = true;
      continue;
    }
    if (arg === "--record") {
      parsed.record = true;
      continue;
    }
    if (arg === "--keep-evidence") {
      index += 1;
      if (index >= argv.length) {
        fail("--keep-evidence requires a comma-separated list of M<n> labels");
      }
      if (parsed.keepEvidence !== null) {
        fail("--keep-evidence was provided more than once");
      }
      parsed.keepEvidence = argv[index]
        .split(",")
        .map((entry) => entry.trim())
        .filter(Boolean);
      continue;
    }
    if (arg === "--change" || arg === "--task") {
      index += 1;
      if (index >= argv.length) {
        fail(`${arg} requires a value`);
      }
      const key = arg === "--change" ? "change" : "task";
      if (parsed[key] !== null) {
        fail(`${arg} was provided more than once`);
      }
      parsed[key] = argv[index];
      continue;
    }
    if (arg === "--action" || arg === "--base") {
      index += 1;
      if (index >= argv.length) {
        fail(`${arg} requires a value`);
      }
      const key = arg === "--action" ? "closeAction" : "base";
      if (parsed[key] !== null) {
        fail(`${arg} was provided more than once`);
      }
      parsed[key] = argv[index];
      continue;
    }
    if (arg === "--event" || arg === "--expected-owner") {
      index += 1;
      if (index >= argv.length) {
        fail(`${arg} requires a value`);
      }
      const key = arg === "--event" ? "projectionEvent" : "expectedOwner";
      if (parsed[key] !== null) fail(`${arg} was provided more than once`);
      parsed[key] = argv[index];
      continue;
    }
    if (arg.startsWith("--change=") || arg.startsWith("--task=")) {
      const key = arg.startsWith("--change=") ? "change" : "task";
      if (parsed[key] !== null) {
        fail(`--${key} was provided more than once`);
      }
      parsed[key] = arg.slice(key.length + 3);
      continue;
    }
    if (arg === "--force-template-update") {
      parsed.forceTemplateUpdate = true;
      continue;
    }
    if (arg === "--with-git-hooks") {
      parsed.withGitHooks = true;
      continue;
    }
    if (arg === "--adopt") {
      parsed.adopt = true;
      continue;
    }
    if (arg === "--target") {
      index += 1;
      if (index >= argv.length) {
        fail("--target requires claude, codex, or opencode");
      }
      parsed.target = argv[index];
      continue;
    }
    if (arg.startsWith("--target=")) {
      parsed.target = arg.slice("--target=".length);
      continue;
    }
    if (arg === "--profile" || arg.startsWith("--profile=")) {
      fail(
        "--profile is no longer supported: web, hardware, and hardware-dsl "
          + "guidance is now user-authored lenses in keel/lenses/*.md "
          + "(scaffold with `keel lenses add`)"
      );
    }
    if (arg === "--repo") {
      index += 1;
      if (index >= argv.length) {
        fail("--repo requires a path");
      }
      if (parsed.repo !== null) {
        fail("repo path was provided more than once");
      }
      parsed.repo = argv[index];
      continue;
    }
    if (arg.startsWith("--repo=")) {
      if (parsed.repo !== null) {
        fail("repo path was provided more than once");
      }
      parsed.repo = arg.slice("--repo=".length);
      continue;
    }
    if (arg === "--source") {
      index += 1;
      if (index >= argv.length) {
        fail("--source requires an npm package or git spec");
      }
      if (parsed.updateSource !== null) {
        fail("update source was provided more than once");
      }
      parsed.updateSource = argv[index];
      continue;
    }
    if (arg.startsWith("--source=")) {
      if (parsed.updateSource !== null) {
        fail("update source was provided more than once");
      }
      parsed.updateSource = arg.slice("--source=".length);
      continue;
    }
    if (arg.startsWith("-")) {
      fail(`unknown option: ${arg}`);
    }
    if (parsed.action === "gate" && parsed.gateStage === null) {
      parsed.gateStage = arg;
      continue;
    }
    if (parsed.action === "guard" && parsed.guardSubcommand === null) {
      parsed.guardSubcommand = arg;
      continue;
    }
    if (parsed.action === "project" && parsed.projectSubcommand === null) {
      parsed.projectSubcommand = arg;
      continue;
    }
    if (parsed.action === "lenses" && parsed.lensesSubcommand === null) {
      parsed.lensesSubcommand = arg;
      continue;
    }
    if (
      parsed.action === "lenses"
      && parsed.lensesSubcommand === "add"
      && parsed.lensName === null
    ) {
      parsed.lensName = arg;
      continue;
    }
    if (parsed.repo !== null) {
      fail("repo path was provided more than once");
    }
    parsed.repo = arg;
  }

  if (parsed.target === "both") {
    parsed.target = "claude";
  }

  if (!VALID_TARGETS.has(parsed.target)) {
    fail(`invalid target: ${parsed.target}`);
  }
  if (
    !["context", "gate", "capabilities", "project", "guard", "triage"].includes(
      parsed.action
    )
    && (
      parsed.change !== null
      || parsed.task !== null
      || parsed.json
      || parsed.clearHandoff
      || parsed.closeAction !== null
      || parsed.base !== null
      || parsed.projectionEvent !== null
      || parsed.expectedOwner !== null
    )
  ) {
    fail("selection and JSON options apply only to keel context or keel gate");
  }
  if (parsed.action !== "context" && parsed.clearHandoff) {
    fail("--clear-handoff applies only to keel context");
  }
  if (
    parsed.action === "capabilities"
    && (
      parsed.change !== null
      || parsed.task !== null
      || parsed.closeAction !== null
      || parsed.base !== null
    )
  ) {
    fail("capabilities accepts only repo, --target, and --json");
  }
  if (
    parsed.action !== "project"
    && (
      parsed.projectionEvent !== null
      || parsed.expectedOwner !== null
    )
  ) {
    fail("projection options apply only to keel project");
  }
  if (parsed.action !== "project" && parsed.projectSubcommand !== null) {
    fail("project subcommands apply only to keel project");
  }
  if (parsed.action !== "guard" && parsed.guardSubcommand !== null) {
    fail("guard subcommands apply only to keel guard");
  }
  if (
    parsed.force
    && parsed.action !== "guard"
    && !(parsed.action === "lenses" && parsed.lensesSubcommand === "add")
  ) {
    fail("--force applies only to keel guard start or keel lenses add");
  }
  if (parsed.action === "lenses") {
    if (!["list", "add"].includes(parsed.lensesSubcommand || "")) {
      fail("lenses requires list or add");
    }
    if (parsed.lensesSubcommand === "add" && !parsed.lensName) {
      fail("keel lenses add requires a lens name");
    }
    if (parsed.lensesSubcommand === "list" && parsed.lensName) {
      fail("keel lenses list does not take a lens name");
    }
  } else if (parsed.lensesSubcommand !== null || parsed.lensName !== null) {
    fail("lens subcommands apply only to keel lenses");
  }
  if (parsed.action === "triage") {
    // At least one attribute, rather than labels specifically: a repository
    // that admits by issue number alone should not have to pass an empty label
    // list to be answered. The requirement stays because Keel never fetches the
    // issue, so a caller supplying nothing is expecting a fetch.
    if (parsed.labels === null && parsed.issue === null) {
      fail(
        "keel triage requires --labels or --issue; Keel never fetches the "
          + "issue, so pass what `gh issue view --json labels,number` returned"
      );
    }
    if (parsed.issue !== null && !/^[1-9]\d*$/.test(parsed.issue)) {
      fail(
        `--issue takes an issue number as a bare number, such as --issue 62; `
          + `got ${parsed.issue || "nothing"}`
      );
    }
  } else {
    if (parsed.labels !== null) fail("--labels applies only to keel triage");
    if (parsed.issue !== null) fail("--issue applies only to keel triage");
  }
  if (parsed.noGuard && parsed.action !== "gate") {
    fail("--no-guard applies only to keel gate task-start");
  }
  if (parsed.record && parsed.action !== "gate") {
    fail("--record applies only to keel gate task-start");
  }
  // `keel project goal`, `helper`, and `tasks` were removed in 5.173.0 (#414):
  // native goals, subagents, and task lists need no Keel projection. A word
  // after `keel project` is refused by name rather than read as a repository.
  if (parsed.action === "project" && parsed.projectSubcommand !== null) {
    fail(
      `unknown project subcommand: ${parsed.projectSubcommand}; keel project `
        + "takes only --event startup|resume|compaction|worktree"
    );
  }

  return parsed;
}

// The interpreter rule lives in `scripts/run_python.js` and is imported rather
// than restated. This file used to carry its own candidate list that asked only
// whether a command runs, so `keel --doctor` reported `python3: ok` for the
// same 3.9.6 the runner refuses — measured 2026-08-02. Two statements of one
// threshold drift the moment either moves; one statement cannot.
const {
  MINIMUM_PYTHON,
  resolveInterpreter,
  describeTried,
} = require(path.join(__dirname, "..", "scripts", "run_python.js"));

function npmCommand() {
  return process.platform === "win32" ? "npm.cmd" : "npm";
}

// npm hoists: installed as a dependency, Keel's OpenSpec bin lands in the
// consumer project's `node_modules/.bin`, and Keel's own package root has no
// `node_modules` at all. Searching only the package root worked in exactly one
// layout — a checkout of this repository, where Keel is the direct consumer —
// which is why every scenario stayed green while `keel openspec` failed on a
// plain install (issue #129). Walk outward the way Node resolves a module:
// nearest wins, so a project pinning its own OpenSpec is honored over one
// further up. The `.bin` entry is the published contract between npm and a
// consumer; resolving through the dependency's internal bin path instead would
// bind Keel to a path that belongs to the dependency.
// An archive moves the change directory on the filesystem. A file Git tracked
// there stays tracked only at the path it was added at, so one that an ignore
// rule matches — evidence a change's own .gitignore excludes and was
// force-added — is dropped by the archive commit (#352). The files tracked
// before the move are recorded, and those the archived path leaves ignored are
// re-added afterwards.
function archiveTracking(repo, args) {
  const name = args.slice(1).find((arg) => !arg.startsWith("-"));
  if (!name || !/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(name)) return null;
  const listed = spawnSync("git", ["ls-files", "-z", "--", `openspec/changes/${name}/`], { cwd: repo, encoding: "utf8" });
  if (listed.error || listed.status !== 0) return null;
  const prefix = `openspec/changes/${name}/`;
  const files = listed.stdout.split("\0").filter((file) => file.startsWith(prefix)).map((file) => file.slice(prefix.length));
  return files.length > 0 ? { name, files } : null;
}

function keepArchivedTracked(repo, tracking) {
  const archive = path.join(repo, "openspec", "changes", "archive");
  let entries = [];
  try {
    entries = fs.readdirSync(archive);
  } catch {
    return;
  }
  const dirs = entries.filter((entry) => entry === tracking.name || entry.endsWith(`-${tracking.name}`))
    .map((entry) => path.join(archive, entry))
    .filter((dir) => tracking.files.some((file) => fs.existsSync(path.join(dir, file))))
    .sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  if (dirs.length === 0) return;
  const moved = tracking.files.map((file) => path.relative(repo, path.join(dirs[0], file)).split(path.sep).join("/"))
    .filter((file) => fs.existsSync(path.join(repo, file)));
  if (moved.length === 0) return;
  const ignored = spawnSync("git", ["check-ignore", "--no-index", "-z", "--stdin"], {
    cwd: repo, encoding: "utf8", input: `${moved.join("\0")}\0`,
  });
  const dropped = ignored.status === 0 ? ignored.stdout.split("\0").filter(Boolean) : [];
  if (dropped.length === 0) return;
  const added = spawnSync("git", ["add", "-f", "--", ...dropped], { cwd: repo, encoding: "utf8" });
  if (added.error || added.status !== 0) {
    process.stderr.write(`keel: ${dropped.length} tracked file(s) the archive move left ignored could not be re-added; run git add -f on them (#352)\n`);
    return;
  }
  process.stdout.write(`keel: re-added ${dropped.length} tracked file(s) the archive move left ignored (#352)\n`);
}

function openspecBinNames() {
  return process.platform === "win32"
    ? ["openspec.cmd", "openspec.exe", "openspec"]
    : ["openspec"];
}

function openspecCandidates() {
  const candidates = [];
  let directory = PACKAGE_ROOT;
  for (;;) {
    for (const name of openspecBinNames()) {
      const candidate = path.join(directory, "node_modules", ".bin", name);
      if (fs.existsSync(candidate)) candidates.push(candidate);
    }
    const parent = path.dirname(directory);
    if (parent === directory) break;
    directory = parent;
  }
  candidates.push(process.platform === "win32" ? "openspec.cmd" : "openspec");
  candidates.push("openspec");
  return [...new Set(candidates)];
}

function runCommand(command, args, options = {}) {
  if (options.dryRun) {
    process.stdout.write(
      `keel: would run ${formatCommand(command, args)}`
        + (options.cwd ? ` in ${options.cwd}` : "")
        + "\n"
    );
    return 0;
  }

  const result = spawnSync(command, args, {
    cwd: options.cwd || process.cwd(),
    env: options.env || process.env,
    stdio: options.stdio || "inherit",
    encoding: options.encoding || "utf8",
    shell: process.platform === "win32",
  });
  if (result.error) {
    if (options.silentNotFound && result.error.code === "ENOENT") {
      return 127;
    }
    process.stderr.write(
      `keel: failed to run ${command}: ${result.error.message}\n`
    );
    return 1;
  }
  return typeof result.status === "number" ? result.status : 1;
}

// Which OpenSpec answered is not cosmetic. `openspecCandidates` prefers the
// installed dependency and otherwise falls back to PATH in silence, so a
// worktree with no `node_modules` validates against whatever version happens
// to be installed globally — measured here as 1.4.1 against a lockfile that
// resolves 1.6.0, which rejects a requirement the shipped template writes.
// A green pipeline and a red worktree were the same command run against two
// different programs. Keel states which one; it does not install or select.
function openspecReportedVersion(command) {
  const result = spawnSync(command, ["--version"], {
    encoding: "utf8",
    shell: process.platform === "win32",
  });
  if (result.error || result.status !== 0) return null;
  const match = `${result.stdout || ""}${result.stderr || ""}`.match(
    /\d+\.\d+\.\d+/
  );
  return match ? match[0] : null;
}

// The OpenSpec that wrote this repository's surfaces: the highest
// `generatedBy` stamp among its OpenSpec skills (#168). Every target's root is
// read, including `.agents/skills`, where OpenSpec 1.13 writes Codex's.
const OPENSPEC_SURFACE_ROOTS = [
  path.join(".claude", "skills"),
  path.join(".codex", "skills"),
  path.join(".agents", "skills"),
  path.join(".opencode", "skills"),
];

function surfaceGeneratorVersion(repo) {
  let newest = null;
  for (const root of OPENSPEC_SURFACE_ROOTS) {
    let entries = [];
    try {
      entries = fs.readdirSync(path.join(repo, root));
    } catch {
      continue;
    }
    for (const entry of entries) {
      if (!entry.startsWith("openspec-")) continue;
      let text;
      try {
        text = fs.readFileSync(path.join(repo, root, entry, "SKILL.md"), "utf8");
      } catch {
        continue;
      }
      const match = text.match(/generatedBy:\s*"?(\d+\.\d+\.\d+)/);
      if (match && (!newest || compareVersions(match[1], newest) > 0)) {
        newest = match[1];
      }
    }
  }
  return newest;
}

// What the project declares about Keel plugin auto-update (#164). Claude reads
// it first from `autoUpdate` on the marketplace's `extraKnownMarketplaces`
// entry, and `keel --install --target claude` writes it. The host reports no
// auto-update state Keel could read, so this is the declaration only; whether
// updates actually arrive is the host's to show.
function pluginAutoUpdateDeclaration(repo) {
  const settingsPath = path.join(repo, ".claude", "settings.json");
  const observation =
    "Keel reads the declaration; the host does not expose whether updates run";
  let entry;
  try {
    const settings = JSON.parse(fs.readFileSync(settingsPath, "utf8"));
    entry = ((settings && settings.extraKnownMarketplaces) || {})[
      "keel-marketplace"
    ];
  } catch {
    entry = undefined;
  }
  if (entry && entry.autoUpdate === true) {
    // A declaration in a file Git does not track exists in this checkout only:
    // every other clone of the project starts with auto-update off (#168).
    const inWorkTree = spawnSync("git", ["rev-parse", "--is-inside-work-tree"], {
      cwd: repo,
      encoding: "utf8",
    });
    const tracked = spawnSync(
      "git",
      ["ls-files", "--error-unmatch", ".claude/settings.json"],
      { cwd: repo, encoding: "utf8" }
    );
    if (
      !inWorkTree.error
      && inWorkTree.status === 0
      && String(inWorkTree.stdout).trim() === "true"
      && tracked.status !== 0
    ) {
      return [
        "warning",
        ".claude/settings.json declares keel-marketplace autoUpdate: true, "
          + "but Git does not track the file, so only this checkout declares "
          + "it; commit it with `git add .claude/settings.json`",
      ];
    }
    return [
      "ok",
      `.claude/settings.json declares keel-marketplace autoUpdate: true; ${observation}`,
    ];
  }
  if (entry && entry.autoUpdate === false) {
    return [
      "manual",
      ".claude/settings.json declares keel-marketplace autoUpdate: false, "
        + "which is the project's choice; updates arrive only through "
        + "`claude plugin update`",
    ];
  }
  return [
    "manual",
    "not declared, so Claude leaves auto-update off for this marketplace; "
      + "run keel --install --target claude, or enable it under /plugin → "
      + "Marketplaces",
  ];
}

// The root is the repository under diagnosis, never PACKAGE_ROOT. Rooting this
// at Keel's own install location made the line a statement about a repository
// the reader was never shown: a consumer pinning 9.9.9 was told the version
// Keel's checkout pins, and a global install — which ships no lockfile — was
// told `unreadable` forever, which is exactly the drift this check was added
// to expose. There is no fallback to PACKAGE_ROOT on purpose; falling back
// would reinstate the misattribution and leave the reader unable to tell which
// case they were in.
//
// Three outcomes, not two. A repository with no lockfile and one whose lockfile
// names no OpenSpec both *declare* nothing, which is the ordinary case for any
// project that does not depend on OpenSpec directly. A lockfile that exists and
// cannot be parsed is a read failure. Collapsing them would either warn at
// everyone or hide a real failure.
//
// The lockfile is the one npm installs from: `npm-shrinkwrap.json` when it
// exists, else `package-lock.json`. A package that publishes itself — Keel
// does since #164 — carries the shrinkwrap, because npm never publishes a
// `package-lock.json`.
function declaredOpenSpecVersion(repo) {
  const lockName = ["npm-shrinkwrap.json", "package-lock.json"].find((name) =>
    fs.existsSync(path.join(repo, name))
  );
  if (!lockName) return { state: "none", version: null, lockName: null };
  let lock;
  try {
    lock = JSON.parse(fs.readFileSync(path.join(repo, lockName), "utf8"));
  } catch {
    return { state: "unreadable", version: null, lockName };
  }
  for (const [name, entry] of Object.entries(lock.packages || {})) {
    if (name.endsWith("@fission-ai/openspec") && entry && entry.version) {
      return { state: "declared", version: entry.version, lockName };
    }
  }
  return { state: "none", version: null, lockName };
}

// "Not installed" and "installed and Keel cannot reach it" need different
// advice: reinstalling is the only remedy for the first and cannot help with the
// second, and issue #129 measured a whole class of installs being sent to it.
// The package directory is the evidence — it is present whenever npm placed the
// dependency, whatever happened to its `.bin` entry.
function installedOpenSpecPackage() {
  let directory = PACKAGE_ROOT;
  for (;;) {
    const candidate = path.join(
      directory,
      "node_modules",
      "@fission-ai",
      "openspec",
      "package.json"
    );
    if (fs.existsSync(candidate)) return candidate;
    const parent = path.dirname(directory);
    if (parent === directory) return null;
    directory = parent;
  }
}

// The remedy for an openspec Keel could not run, split by whether npm has
// already done the thing the other branch would ask for.
function unresolvedOpenSpecAdvice() {
  const installed = installedOpenSpecPackage();
  return installed
    ? `the OpenSpec dependency is installed at ${path.dirname(installed)} but `
      + "Keel could not run it — check that its node_modules/.bin entry exists "
      + "and is executable; reinstalling will not change this"
    : "reinstall keel so npm installs its OpenSpec dependency";
}

function findOpenSpecCommand() {
  for (const command of openspecCandidates()) {
    const status = runCommand(command, ["--version"], {
      stdio: "ignore",
      silentNotFound: true,
    });
    if (status === 0) {
      return command;
    }
  }
  return null;
}

function formatCommand(command, args) {
  const quote = (value) => {
    if (/^[A-Za-z0-9_./:@+-]+$/.test(value)) {
      return value;
    }
    return JSON.stringify(value);
  };
  return [command, ...args].map(quote).join(" ");
}

function findPackedTarball(packStdout, tempDir) {
  try {
    const parsed = JSON.parse(packStdout);
    const packEntries = Array.isArray(parsed) ? parsed : [parsed];
    for (const entry of packEntries) {
      if (entry && typeof entry.filename === "string") {
        const candidate = path.join(tempDir, entry.filename);
        if (fs.existsSync(candidate)) {
          return candidate;
        }
      }
    }
  } catch {
    // Fall back to scanning the pack destination below.
  }

  const tarballs = fs
    .readdirSync(tempDir)
    .filter((entry) => entry.endsWith(".tgz"))
    .map((entry) => path.join(tempDir, entry));

  if (tarballs.length === 1) {
    return tarballs[0];
  }

  throw new Error(
    `expected one packed tarball in ${tempDir}, found ${tarballs.length}`
  );
}

// One owner-run update for the machine (#204): the global CLI first, then
// the Keel plugin of each host that has one installed, through that host's own
// documented commands. Every component reports exactly one line saying what
// changed, when it applies, and what is left for the owner, because a plugin
// installed on disk is not a plugin the running sessions use, and the two used
// to be reported as the same thing. Hooks and projections never reach this.
function updateLine(component, status, detail) {
  process.stdout.write(`keel update: ${component}: ${status} - ${detail}\n`);
}

function hostRun(executable, args) {
  return spawnSync(executable, args, {
    encoding: "utf8",
    shell: process.platform === "win32",
    timeout: 5 * 60 * 1000,
  });
}

// A read-only `plugin list --json` normally answers in 1–3 s, and once hung
// for minutes through a proxy (#354). It gets its own short limit, and a query
// that fails is reported as one, never as a host with no Keel. A query that
// times out is retried once: on the owner's link the same query took 58 s
// once and about 1 s on the next runs (#365).
function hostQuery(executable, args) {
  const limit = Number(process.env.KEEL_UPDATE_QUERY_TIMEOUT_MS) || 30 * 1000;
  const run = () => spawnSync(executable, args, {
    encoding: "utf8",
    shell: process.platform === "win32",
    timeout: limit,
  });
  const timedOut = (attempt) => attempt.error && attempt.error.code === "ETIMEDOUT";
  let result = run();
  if (timedOut(result)) result = run();
  if (result.error && result.error.code === "ENOENT") return { absent: true };
  if (timedOut(result)) {
    return { failed: `timed out twice, after ${limit / 1000} s each` };
  }
  if (result.error) return { failed: result.error.message };
  // On Windows the call goes through cmd.exe, which reports a missing command
  // as a nonzero exit rather than ENOENT.
  if (
    result.status !== 0 && process.platform === "win32"
    && /is not recognized as an internal or external command/i.test(result.stderr || "")
  ) {
    return { absent: true };
  }
  if (result.status !== 0) return { failed: `exited ${result.status}` };
  try {
    return { json: JSON.parse(result.stdout) };
  } catch {
    return { failed: "printed no JSON" };
  }
}

// What each host reports about its installed Keel plugin, or null when the
// host is absent or has none. Both hosts answer `plugin list --json`, in
// different shapes (2026-10-03: Claude a list of {id, version, installPath},
// Codex {installed: [{pluginId, version, marketplaceSource, source}]}).
// Each returns the Keel entry, null for a host with none, or { failed } when
// the query itself failed.
function claudeKeel(executable) {
  const queried = hostQuery(executable, ["plugin", "list", "--json"]);
  if (queried.failed) return { failed: `\`claude plugin list --json\` ${queried.failed}` };
  const listed = queried.json;
  const entry = (Array.isArray(listed) ? listed : [])
    .find((item) => item && typeof item.id === "string" && item.id.startsWith("keel@"));
  if (!entry) return null;
  return {
    id: entry.id,
    market: entry.id.slice("keel@".length),
    version: entry.version || null,
    lastUpdated: entry.lastUpdated || null,
  };
}

// The Codex marketplace needs only its catalog and the plugin it names; a
// sparse clone fetches those instead of the whole repository, which a slow
// link cannot clone within Codex's 30 s limit (#329).
const CODEX_SPARSE_PATHS = [".agents/plugins", "plugins/keel"];
const CODEX_SPARSE_FLAGS = CODEX_SPARSE_PATHS.map((entry) => `--sparse ${entry}`).join(" ");

function codexKeel(executable) {
  const queried = hostQuery(executable, ["plugin", "list", "--json"]);
  if (queried.failed) return { failed: `\`codex plugin list --json\` ${queried.failed}` };
  const listed = queried.json;
  const items = listed && Array.isArray(listed.installed) ? listed.installed : [];
  const entry = items.find((item) => item && item.name === "keel" && item.installed !== false);
  if (!entry) return null;
  const market = entry.marketplaceSource || {};
  return {
    id: entry.pluginId || `keel@${entry.marketplaceName}`,
    market: entry.marketplaceName,
    version: entry.version || null,
    sourceType: market.sourceType || "unknown",
    source: market.source || "",
    path: entry.source && entry.source.path ? entry.source.path : null,
  };
}

function readOrNull(file) {
  try {
    return fs.readFileSync(file);
  } catch {
    return null;
  }
}

function hostFails(executable, args) {
  const result = hostRun(executable, args);
  return Boolean(result.error) || result.status !== 0;
}

// Why a host step failed: its spawn error, or its exit status with the last
// line it wrote to stderr, so the cause is visible the first time (#359).
function hostFailure(result) {
  if (result.error) return result.error.message;
  const last = String(result.stderr || "").trim().split(/\r?\n/).pop().trim();
  return `exited ${result.status}${last ? `: ${last}` : ""}`;
}

function runHostSteps(component, name, executable, steps) {
  for (const args of steps) {
    const result = hostRun(executable, args);
    if (result.error || result.status !== 0) {
      updateLine(component, "failed", `\`${name} ${args.join(" ")}\` ${hostFailure(result)}`);
      return false;
    }
  }
  return true;
}

function versionChange(before, after) {
  return before && after && before !== after ? `updated ${before} -> ${after}` : `current ${after || before || "unknown"}`;
}

// Right after a release the Claude marketplace, read from Git, names a version
// the npm registry this machine reaches does not serve yet, and the plugin
// update exits with npm's E404; a rerun minutes later succeeds (#421). That is
// read as lag only when the registry's own latest is older than the version
// asked for; an E404 the registry cannot explain stays a failure.
function registryLag(result, npm) {
  const said = `${result.stdout || ""}\n${result.stderr || ""}`;
  const match = /E404 No match found for version (\d+\.\d+\.\d+[^\s'"]*)/.exec(said);
  if (!match) return null;
  const limit = Number(process.env.KEEL_UPDATE_QUERY_TIMEOUT_MS) || 30 * 1000;
  const view = spawnSync(npm, ["view", PACKAGE_JSON.name, "version", "--prefer-online"], {
    encoding: "utf8",
    shell: process.platform === "win32",
    timeout: limit,
  });
  if (view.error || view.status !== 0) return null;
  const latest = String(view.stdout || "").trim();
  if (!/^\d+\.\d+\.\d+/.test(latest) || compareVersions(match[1], latest) <= 0) return null;
  return { wanted: match[1], latest };
}

function updateClaudePlugin(options, npm) {
  const component = "claude plugin";
  const executable = process.env.KEEL_UPDATE_CLAUDE || "claude";
  const queried = claudeKeel(executable);
  const installed = queried && !queried.failed ? queried : null;
  const id = installed ? installed.id : "keel@keel-marketplace";
  const market = installed ? installed.market : "keel-marketplace";
  const steps = [["plugin", "marketplace", "update", market], ["plugin", "update", id]];
  if (options.dryRun) {
    for (const args of steps) process.stdout.write(`keel: would run claude ${args.join(" ")}\n`);
    return true;
  }
  if (queried && queried.failed) {
    updateLine(component, "failed", queried.failed);
    return false;
  }
  if (!installed) {
    updateLine(component, "absent", "Claude Code is not installed here or has no Keel plugin");
    return true;
  }
  // The refresh fetches over the network, and on a proxied link it has failed
  // once and passed on a direct retry; one retry absorbs that, as for Codex (#359).
  let refreshed = hostRun(executable, steps[0]);
  if (refreshed.error || refreshed.status !== 0) refreshed = hostRun(executable, steps[0]);
  if (refreshed.error || refreshed.status !== 0) {
    updateLine(component, "failed", `\`claude ${steps[0].join(" ")}\` failed twice; ${hostFailure(refreshed)}`);
    return false;
  }
  const updated = hostRun(executable, steps[1]);
  if (updated.error || updated.status !== 0) {
    const lag = registryLag(updated, npm);
    if (lag) {
      updateLine(
        component,
        "pending",
        `the npm registry here does not serve ${lag.wanted} yet (its latest is ${lag.latest}); `
          + "rerun keel --update in a few minutes"
      );
      return true;
    }
    updateLine(component, "failed", `\`claude ${steps[1].join(" ")}\` ${hostFailure(updated)}`);
    return false;
  }
  const after = claudeKeel(executable);
  if (after && after.failed) {
    updateLine(component, "failed", `${after.failed} after the update, so its result is unverified`);
    return false;
  }
  updateLine(
    component,
    versionChange(installed.version, after && after.version),
    "running sessions use it at their next hook call; their skills after /reload-plugins"
  );
  return true;
}

function compareVersions(a, b) {
  const parts = (value) => value.split(/[.-]/).map((part) => (/^\d+$/.test(part) ? Number(part) : part));
  const left = parts(a);
  const right = parts(b);
  for (let index = 0; index < Math.max(left.length, right.length); index += 1) {
    const x = left[index] === undefined ? 0 : left[index];
    const y = right[index] === undefined ? 0 : right[index];
    if (x === y) continue;
    if (typeof x === "number" && typeof y === "number") return x - y;
    return String(x) < String(y) ? -1 : 1;
  }
  return 0;
}

function codexCacheVersion(cacheDir) {
  let entries = [];
  try {
    entries = fs.readdirSync(cacheDir, { withFileTypes: true })
      .filter((entry) => entry.isDirectory() && /^\d/.test(entry.name))
      .map((entry) => entry.name);
  } catch {
    return null;
  }
  return entries.sort(compareVersions).pop() || null;
}

// What Codex's own files say when `plugin list --json` cannot (#412): the
// marketplace's source type in config.toml and the installed version in the
// plugin cache. Both, or nothing — a query failure is never read as an absent
// host (#354), so with no install on disk the failure stands.
function codexKeelFromDisk(codexHome, market) {
  let config = "";
  try {
    config = fs.readFileSync(path.join(codexHome, "config.toml"), "utf8");
  } catch {
    return null;
  }
  const header = `[marketplaces.${market}]`;
  const lines = config.split(/\r?\n/);
  const start = lines.findIndex((line) => line.trim() === header);
  if (start < 0) return null;
  const section = {};
  for (const line of lines.slice(start + 1)) {
    if (/^\s*\[/.test(line)) break;
    const entry = line.match(/^\s*([A-Za-z_]+)\s*=\s*"([^"]*)"/);
    if (entry) section[entry[1]] = entry[2];
  }
  const cacheDir = path.join(codexHome, "plugins", "cache", market, "keel");
  const version = codexCacheVersion(cacheDir);
  if (!section.source_type || !version) return null;
  return {
    id: `keel@${market}`,
    market,
    version,
    sourceType: section.source_type,
    source: section.source || "",
    path: null,
    cacheDir,
  };
}

function updateCodexPlugin(options) {
  const component = "codex plugin";
  const executable = process.env.KEEL_UPDATE_CODEX || "codex";
  const codexHome = process.env.CODEX_HOME || path.join(os.homedir(), ".codex");
  let queried = codexKeel(executable);
  // A query that failed and Codex's own state that can carry the update: the
  // update runs from that state, and every later read comes from the cache,
  // because a query that just hung would most likely hang again.
  let listFailure = null;
  if (queried && queried.failed && !options.dryRun) {
    const fromDisk = codexKeelFromDisk(codexHome, "keel-marketplace");
    if (fromDisk) {
      listFailure = queried.failed;
      queried = fromDisk;
    }
  }
  const installed = queried && !queried.failed ? queried : null;
  const id = installed ? installed.id : "keel@keel-marketplace";
  const market = installed ? installed.market : "keel-marketplace";
  const steps = [["plugin", "marketplace", "upgrade", market], ["plugin", "add", id]];
  if (options.dryRun) {
    for (const args of steps) process.stdout.write(`keel: would run codex ${args.join(" ")}\n`);
    return true;
  }
  if (queried && queried.failed) {
    updateLine(component, "failed", queried.failed);
    return false;
  }
  if (!installed) {
    updateLine(component, "absent", "Codex is not installed here or has no Keel plugin");
    return true;
  }
  // `codex plugin marketplace upgrade` refreshes Git marketplaces only. A
  // local one follows whatever its checkout holds, which is the owner's to
  // decide, so it is named rather than re-pointed.
  if (installed.sourceType !== "git") {
    updateLine(
      component,
      "manual",
      `its marketplace is a ${installed.sourceType} source (${installed.source}), which \`codex plugin `
        + "marketplace upgrade` cannot refresh; to make it upgradable, run `codex plugin marketplace "
        + `remove ${market}\` and then codex plugin marketplace add TanglmChris/keel --ref main ${CODEX_SPARSE_FLAGS}`
    );
    return true;
  }
  // The refresh clones over the network; one retry absorbs a dropped link (#329).
  if (hostFails(executable, steps[0]) && hostFails(executable, steps[0])) {
    const codexConfig = path.join(process.env.CODEX_HOME || path.join(os.homedir(), ".codex"), "config.toml");
    updateLine(
      component,
      "failed",
      `\`codex ${steps[0].join(" ")}\` failed twice; a slow link can exceed Codex's 30 s clone limit, and a sparse `
        + `marketplace fetches only the plugin: add sparse_paths = ${JSON.stringify(CODEX_SPARSE_PATHS)} `
        + `under [marketplaces.${market}] in ${codexConfig}`
    );
    return false;
  }
  // Codex re-reads hook definitions at every call and trusts them by hash, so
  // a changed definition stops running until the owner reviews it. Compared
  // before `plugin add`, which deletes the old install's directory.
  const oldHooks = installed.version
    ? readOrNull(path.join(codexHome, "plugins", "cache", market, "keel", installed.version, "hooks", "codex.json"))
    : null;
  let newHooks = null;
  if (!listFailure) {
    const upgraded = codexKeel(executable);
    if (upgraded && upgraded.failed) {
      updateLine(component, "failed", `${upgraded.failed} after the marketplace refresh`);
      return false;
    }
    newHooks = upgraded && upgraded.path ? readOrNull(path.join(upgraded.path, "hooks", "codex.json")) : null;
  }
  if (!runHostSteps(component, "codex", executable, [steps[1]])) return false;
  let after;
  if (listFailure) {
    const version = codexCacheVersion(installed.cacheDir);
    after = version ? { version } : null;
    if (version) newHooks = readOrNull(path.join(installed.cacheDir, version, "hooks", "codex.json"));
  } else {
    after = codexKeel(executable);
    if (after && after.failed) {
      updateLine(component, "failed", `${after.failed} after the update, so its result is unverified`);
      return false;
    }
  }
  const hooksChanged = oldHooks && newHooks && !oldHooks.equals(newHooks);
  updateLine(
    component,
    versionChange(installed.version, after && after.version),
    "running sessions use it at their next hook call"
      + (hooksChanged ? "; its hook definitions changed, so Codex will ask you to review them in /hooks before they run" : "")
      + (listFailure
        ? `; \`codex plugin list --json\` did not answer (${listFailure.replace(/^`codex plugin list --json` /, "")}), so versions were read from ${installed.cacheDir}`
        : "")
  );
  return true;
}

// The version the global prefix holds (#459 D1): what `npm install -g` wrote,
// read rather than assumed, since an install that exits 0 once left the
// prefix a release behind while the line said `updated`.
function installedCli(npm) {
  const root = spawnSync(npm, ["root", "-g"], {
    encoding: "utf8",
    shell: process.platform === "win32",
    timeout: Number(process.env.KEEL_UPDATE_QUERY_TIMEOUT_MS) || 30 * 1000,
  });
  const dir = String(root.stdout || "").trim().split(/\r?\n/).pop();
  if (root.error || root.status !== 0 || !dir) {
    return { version: null, why: `npm root -g ${root.error ? root.error.message : `exited ${root.status} with ${dir ? "output" : "no output"}`}` };
  }
  const file = path.join(dir, "@christang", "keel", "package.json");
  try {
    return { version: JSON.parse(fs.readFileSync(file, "utf8")).version || null, file, why: `${file} names no version` };
  } catch (error) {
    return { version: null, file, why: `${file} cannot be read (${error.code || error.message})` };
  }
}

function updateGlobalCli(options, npm, source) {
  if (options.dryRun) {
    process.stdout.write(
      `keel: would run ${formatCommand(npm, [
        "pack",
        source,
        "--pack-destination",
        "<temporary-directory>",
        "--json",
      ])}\n`
    );
    process.stdout.write(
      `keel: would run ${formatCommand(npm, [
        "install",
        "-g",
        "<packed-tarball>",
      ])}\n`
    );
    return true;
  }

  const before = installedCli(npm);
  const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "keel-update-"));
  try {
    const packArgs = [
      "pack",
      source,
      "--pack-destination",
      tempDir,
      "--json",
    ];
    const packResult = spawnSync(npm, packArgs, {
      encoding: "utf8",
      stdio: ["inherit", "pipe", "inherit"],
      shell: process.platform === "win32",
    });
    if (packResult.error || packResult.status !== 0) {
      const why = packResult.error ? packResult.error.message : `exited ${packResult.status}`;
      updateLine("cli", "failed", `npm pack ${source} ${why}`);
      return false;
    }

    const tarball = findPackedTarball(packResult.stdout, tempDir);
    const installResult = spawnSync(npm, ["install", "-g", tarball], {
      stdio: "inherit",
      shell: process.platform === "win32",
    });
    if (installResult.error || installResult.status !== 0) {
      const why = installResult.error ? installResult.error.message : `exited ${installResult.status}`;
      updateLine("cli", "failed", `npm install -g ${path.basename(tarball)} ${why}`);
      return false;
    }
    const packed = /-(\d+\.\d+\.\d+[^/]*?)\.tgz$/.exec(path.basename(tarball));
    // From the default source the packed version is the registry's latest as
    // this machine sees it, which is what `current` means right after a
    // release whose version has not reached that registry yet (#421).
    const latest = packed && source === DEFAULT_UPDATE_SOURCE
      ? `the npm registry's latest here is ${packed[1]}; `
      : "";
    // What the prefix holds now decides the line (#459 D2–D4).
    const after = installedCli(npm);
    if (after.version && packed && after.version !== packed[1]) {
      updateLine("cli", "failed", `npm install -g ${path.basename(tarball)} exited 0, but ${after.file} holds ${after.version}`);
      return false;
    }
    const unverified = after.version ? "" : `; not verified: ${after.why}`;
    updateLine(
      "cli",
      versionChange(before.version || PACKAGE_JSON.version, after.version || (packed ? packed[1] : null)),
      `${latest}applies to the next command that runs keel${unverified}`
    );
    return true;
  } catch (error) {
    updateLine("cli", "failed", error.message);
    return false;
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

function runGlobalUpdate(options) {
  if (options.repo !== null) {
    fail("--update refreshes the global keel CLI and does not accept a repo path");
  }
  if (options.target !== "claude") {
    fail("--update refreshes the global keel CLI and does not accept --target");
  }
  if (options.forceTemplateUpdate) {
    fail("--update does not accept --force-template-update; use keel --install --force-template-update for project files");
  }

  const source =
    options.updateSource || process.env.KEEL_UPDATE_SOURCE || DEFAULT_UPDATE_SOURCE;
  const npm = process.env.KEEL_UPDATE_NPM || npmCommand();

  // Each step runs whatever the one before it did: a host that failed still
  // leaves the others to report, and any failure fails the command.
  const results = [
    updateGlobalCli(options, npm, source),
    updateClaudePlugin(options, npm),
    adoptClaudeSessions(options),
    updateCodexPlugin(options),
  ];
  return results.every(Boolean) ? 0 : 1;
}

function waitForExit(pid, limitMs) {
  if (!Number.isInteger(pid) || pid <= 0) return true;
  const deadline = Date.now() + limitMs;
  for (;;) {
    try {
      process.kill(pid, 0);
    } catch {
      return true;
    }
    if (Date.now() >= deadline) return false;
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, 200);
  }
}

// A Claude background session keeps the plugin it loaded (#424). A hand-over
// adopts the update, because it starts a new process; a session that does not
// change shift stays on the old one. Each running background session started
// before the installed plugin's `lastUpdated` is named, and with --adopt each
// idle one is restarted: `claude stop`, a wait for its process to exit (a
// resume before that starts a copy, #395), then `claude --bg --resume <id>`
// with no prompt and no flag, which keeps its id and runs no turn (measured
// 2026-10-21, Claude Code 2.1.304). A busy or waiting session, one under a
// task's write guard, and the session running this are left.
function adoptClaudeSessions(options) {
  const component = "claude sessions";
  const executable = process.env.KEEL_UPDATE_CLAUDE || "claude";
  if (options.dryRun) {
    if (options.adopt) {
      process.stdout.write("keel: would restart each idle background session started before the installed plugin: "
        + "claude stop <id>, then claude --bg --resume <session id>\n");
    }
    return true;
  }
  const plugin = claudeKeel(executable);
  const updatedAt = Date.parse((plugin && plugin.lastUpdated) || "");
  if (!plugin || plugin.failed || !Number.isFinite(updatedAt)) return true;
  const listed = hostQuery(executable, ["agents", "--json"]);
  const rows = !listed.failed && Array.isArray(listed.json) ? listed.json : null;
  if (!rows) {
    if (!options.adopt) return true;
    updateLine(component, "failed", `\`claude agents --json\` ${listed.failed || "listed no sessions"}, so none was adopted`);
    return false;
  }
  const own = process.env.CLAUDE_CODE_SESSION_ID || "";
  const older = rows.filter((row) => row && row.kind === "background" && row.status && row.sessionId
    && row.sessionId !== own && Number(row.startedAt) < updatedAt);
  if (older.length === 0) return true;
  const named = (row) => `${row.name || row.sessionId.slice(0, 8)} (${row.id || row.sessionId.slice(0, 8)})`;
  if (!options.adopt) {
    updateLine(component, "manual", `${older.length} started before the plugin was installed and still run the skills they loaded: `
      + `${older.map(named).join(", ")}; \`keel --update --adopt\` restarts the idle ones, and a shift change starts its new session on the installed plugin`);
    return true;
  }
  const adopted = [];
  const left = [];
  const failed = [];
  for (const row of older) {
    if (row.status !== "idle") {
      left.push(`${named(row)}, ${row.status}`);
      continue;
    }
    if (row.cwd && fs.existsSync(path.join(row.cwd, "keel", "guard.json"))) {
      left.push(`${named(row)}, under a task's write guard`);
      continue;
    }
    const stopped = hostRun(executable, ["stop", row.id || row.sessionId.slice(0, 8)]);
    if (stopped.error || stopped.status !== 0) {
      failed.push(`${named(row)}: \`claude stop\` ${hostFailure(stopped)}`);
      continue;
    }
    if (!waitForExit(Number(row.pid), 15 * 1000)) {
      failed.push(`${named(row)}: its process ${row.pid} was still running 15 s after \`claude stop\``);
      continue;
    }
    const resumed = spawnSync(executable, ["--bg", "--resume", row.sessionId], {
      encoding: "utf8",
      cwd: row.cwd && fs.existsSync(row.cwd) ? row.cwd : undefined,
      shell: process.platform === "win32",
      timeout: 60 * 1000,
    });
    if (resumed.error || resumed.status !== 0) {
      failed.push(`${named(row)}: \`claude --bg --resume\` ${hostFailure(resumed)}; \`claude attach ${row.id || row.sessionId.slice(0, 8)}\` reopens it`);
      continue;
    }
    adopted.push(named(row));
  }
  const parts = [];
  if (adopted.length) parts.push(`adopted ${adopted.join(", ")} — restarted on the installed plugin, same session, no turn run`);
  if (left.length) parts.push(`left ${left.join("; ")} — each adopts at its next shift change or another --adopt`);
  if (failed.length) parts.push(`could not adopt ${failed.join("; ")}`);
  updateLine(component, failed.length ? "failed" : "updated", parts.join("; "));
  return failed.length === 0;
}

function runPython(script, args) {
  if (!fs.existsSync(script)) {
    process.stderr.write(`keel: missing packaged script: ${script}\n`);
    return 1;
  }

  const { candidate, tried } = resolveInterpreter();
  if (candidate) {
    const result = spawnSync(
      candidate.command,
      [...candidate.prefixArgs, script, ...args],
      { stdio: "inherit" }
    );
    return typeof result.status === "number" ? result.status : 1;
  }

  const minimum = MINIMUM_PYTHON.join(".");
  process.stderr.write(
    `keel: Python ${minimum} or newer is required. Tried `
      + `${describeTried(tried) || "nothing"}. Install one, or set `
      + "KEEL_PYTHON.\n"
  );
  return 1;
}

function installerArgs(options, extra = []) {
  const repo = path.resolve(options.repo || process.cwd());
  const args = [repo, "--target", options.target, ...extra];
  if (options.dryRun) {
    args.push("--dry-run");
  }
  if (options.forceTemplateUpdate) {
    args.push("--force-template-update");
  }
  if (options.withGitHooks) {
    args.push("--with-git-hooks");
  }
  return args;
}

function openspecToolsForTarget(target) {
  return target;
}

// Where OpenSpec reads its one global configuration (OpenSpec 1.14
// `getGlobalConfigDir`): XDG_CONFIG_HOME on every platform when set, else
// %APPDATA% on Windows and ~/.config elsewhere.
function openspecGlobalConfigFile() {
  const base = process.env.XDG_CONFIG_HOME
    || (process.platform === "win32"
      ? process.env.APPDATA || path.join(os.homedir(), "AppData", "Roaming")
      : path.join(os.homedir(), ".config"));
  return path.join(base, "openspec", "config.json");
}

// OpenSpec reads `delivery` only from that global file, and its default,
// `both`, put every workflow on Claude twice: a skill and an `/opsx:` command
// (#406). The OpenSpec runs that generate surfaces get the user's own
// configuration with `delivery` replaced by `skills`, through a temporary
// XDG_CONFIG_HOME; the user's file is read and never written. Every other
// field, the workflow selection among them, still applies.
function withSkillsDelivery(run) {
  let config = {};
  try {
    const parsed = JSON.parse(fs.readFileSync(openspecGlobalConfigFile(), "utf8"));
    if (parsed && typeof parsed === "object" && !Array.isArray(parsed)) config = parsed;
  } catch {
    // Absent or unreadable reads as OpenSpec's defaults, as OpenSpec does.
  }
  const home = fs.mkdtempSync(path.join(os.tmpdir(), "keel-openspec-config-"));
  try {
    fs.mkdirSync(path.join(home, "openspec"));
    fs.writeFileSync(
      path.join(home, "openspec", "config.json"),
      `${JSON.stringify({ ...config, delivery: "skills" }, null, 2)}\n`
    );
    return run({ ...process.env, XDG_CONFIG_HOME: home });
  } finally {
    fs.rmSync(home, { recursive: true, force: true });
  }
}

const OPENSPEC_GENERATING_COMMANDS = new Set(["init", "update"]);

function runOpenSpec(args, repo, options) {
  const command = options.dryRun ? "openspec" : findOpenSpecCommand();
  if (!command) {
    process.stderr.write(
      "keel: OpenSpec CLI is provided by Keel's npm dependencies but was not found. Reinstall keel so npm installs its dependencies.\n"
    );
    return 1;
  }
  if (options.dryRun) return runCommand(command, args, { cwd: repo, dryRun: true });
  return withSkillsDelivery((env) => runCommand(command, args, { cwd: repo, env }));
}

function runProjectInit(options) {
  if (options.updateSource !== null) {
    fail("--source only applies to --update");
  }

  const repo = path.resolve(options.repo || process.cwd());
  if (!options.dryRun) {
    fs.mkdirSync(repo, { recursive: true });
  }

  // Never downgrade (#168): surfaces a newer OpenSpec wrote keep their
  // content. The protocol and Keel's overlays still move; only OpenSpec's own
  // `--force` rewrite is skipped, and the reason is printed.
  const surfaces = surfaceGeneratorVersion(repo);
  const resolvedCommand = findOpenSpecCommand();
  const resolved = resolvedCommand ? openspecReportedVersion(resolvedCommand) : null;
  const keepSurfaces = Boolean(
    surfaces && resolved && compareVersions(surfaces, resolved) > 0
  );
  if (keepSurfaces) {
    process.stdout.write(
      `keel: OpenSpec surfaces were written by OpenSpec ${surfaces}, newer `
        + `than the ${resolved} Keel runs; skipped \`openspec init --force\` `
        + "and `openspec update --force`, which would downgrade them (#168). "
        + "The protocol and Keel's overlays are still refreshed.\n"
    );
  }

  const openspecTools = keepSurfaces ? null : openspecToolsForTarget(options.target);
  if (openspecTools) {
    const initStatus = runOpenSpec(
      ["init", "--tools", openspecTools, "--force"],
      repo,
      options
    );
    if (initStatus !== 0) {
      return initStatus;
    }
  }

  const installStatus = runPython(INSTALL_SCRIPT, installerArgs(options));
  if (installStatus !== 0) {
    return installStatus;
  }

  if (openspecTools) {
    const updateStatus = runOpenSpec(["update", "--force"], repo, options);
    if (updateStatus !== 0) {
      return updateStatus;
    }
  }
  if (openspecTools || keepSurfaces) {
    return refreshInstalledTargetOverlays(repo, options.target, {
      dryRun: options.dryRun,
    }).status;
  }

  return 0;
}

function printDoctorLine(name, status, detail = "") {
  process.stdout.write(`${name}: ${status}${detail ? ` - ${detail}` : ""}\n`);
}

// The `version=` attribute of the managed marker is written by every install
// and, until this line existed, read back by nothing that runs locally: both
// marker parsers match `keel:start(?:\s+[^>]*)?` and throw the attributes away.
// The one reader was the plugin's SessionStart hook, and doctor reports that
// plugin's activation as manual on every target — so the check might simply not
// be running, with nothing to distinguish that from agreement. Doctor is the
// model-free fallback: the declaration comes from the working tree and the
// running version from this process, so the comparison holds with no plugin at
// all.
function declaredProtocolVersion(repo) {
  const agentsPath = path.join(repo, "AGENTS.md");
  if (!fs.existsSync(agentsPath)) return null;
  const match = fs
    .readFileSync(agentsPath, "utf8")
    .match(/<!--\s*keel:start\s+version=(\d+\.\d+\.\d+)\s*-->/);
  return match ? match[1] : null;
}

// Numeric, not lexical: "5.9.0" precedes "5.10.0" and string order says
// otherwise. Returns a negative number when `a` is behind `b`.
function compareVersions(a, b) {
  const left = a.split(".").map(Number);
  const right = b.split(".").map(Number);
  for (let i = 0; i < 3; i += 1) {
    if (left[i] !== right[i]) return left[i] - right[i];
  }
  return 0;
}

// Printed on every run, agreeing or not. A check that is silent when it passes
// cannot be told apart from a check that did not run, which is the failure this
// line exists to remove — so silence is never the report.
function printProtocolVersionDrift(repo, target) {
  const running = PACKAGE_JSON.version;
  const declared = declaredProtocolVersion(repo);
  if (!declared) {
    printDoctorLine(
      "protocol",
      "not comparable",
      `this CLI is ${running}; the repository declares no protocol version in `
        + "an AGENTS.md `keel:start` marker — run "
        + `keel --init --target ${target} to write one`
    );
    return;
  }
  const order = compareVersions(declared, running);
  if (order === 0) {
    printDoctorLine(
      "protocol",
      "ok",
      `repo declares ${declared}, this CLI is ${running}`
    );
    return;
  }
  // The two directions have different repairs, and the wrong repair is a no-op
  // that reads as a failure, so the line names the direction rather than the
  // difference. Drift never reaches the exit code: an out-of-date install is
  // not a broken one, and a doctor that goes red on release day is a doctor
  // people switch off.
  printDoctorLine(
    "protocol",
    "warning",
    order < 0
      ? `repo declares ${declared}, this CLI is ${running} — the repository is `
        + `behind its install; run keel --install --target ${target} to bring `
        + "the protocol forward; it leaves OpenSpec's surfaces as they are "
        + "(#168)"
      : `repo declares ${declared}, this CLI is ${running} — the install is `
        + "behind the repository, which carries a protocol this CLI cannot "
        + "enforce; update the Keel package"
  );
}

function codexHome() {
  const configured = (process.env.CODEX_HOME || "").trim();
  return path.resolve(configured || path.join(os.homedir(), ".codex"));
}

function countExisting(paths) {
  const existing = paths.filter((candidate) => fs.existsSync(candidate));
  return { existing: existing.length, total: paths.length };
}

function formatCount(counts, location) {
  return `${counts.existing}/${counts.total} under ${location}`;
}

function surfaceStatus(counts) {
  return counts.existing === counts.total ? "ok" : "missing";
}

function skillRootForTarget(target) {
  if (target === "claude") return path.join(".claude", "skills");
  if (target === "codex") return path.join(".agents", "skills");
  return path.join(".opencode", "skills");
}

// Which OpenSpec layout a Codex repository carries (#169). OpenSpec 1.6 wrote
// Codex's skills under `.codex/skills` and its commands as prompts in
// CODEX_HOME; 1.13 and later, including the 1.14 Keel pins, write skills under `.agents/skills` and
// no command files. A repository set up under 1.6 keeps its layout, and every
// other one — a fresh repository included — gets the one the pin writes.
function codexOpenSpecLayout(repo) {
  const holdsOpenSpec = (root) => {
    try {
      return fs
        .readdirSync(path.join(repo, root))
        .some((entry) => entry.startsWith("openspec-"));
    } catch {
      return false;
    }
  };
  return holdsOpenSpec(path.join(".codex", "skills"))
    && !holdsOpenSpec(path.join(".agents", "skills"))
    ? "legacy"
    : "agents";
}

function openspecSkillRootForTarget(target, repo) {
  if (target === "claude") return path.join(".claude", "skills");
  if (target === "codex") {
    return codexOpenSpecLayout(repo) === "legacy"
      ? path.join(".codex", "skills")
      : path.join(".agents", "skills");
  }
  return path.join(".opencode", "skills");
}

function commandSurfaceForTarget(target, repo) {
  if (target === "claude") {
    const location = path.join(".claude", "commands", "opsx");
    return {
      location,
      paths: OPENSPEC_COMMAND_IDS.map((id) =>
        path.join(repo, location, `${id}.md`)
      ),
      remediation: "run keel --init --target claude to remove them",
      retired: true,
    };
  }
  if (target === "codex" && codexOpenSpecLayout(repo) === "agents") {
    // OpenSpec 1.13 and later surface Codex's workflows as the skills counted on the
    // line above and writes no command file, so there is nothing to count here.
    return {
      location: path.join(".agents", "skills"),
      paths: [],
      remediation: "run keel --init --target codex or openspec update --force",
      skillsOnly: true,
    };
  }
  if (target === "codex") {
    const home = codexHome();
    const location = path.join(home, "prompts");
    return {
      location,
      paths: OPENSPEC_COMMAND_IDS.map((id) =>
        path.join(location, `opsx-${id}.md`)
      ),
      remediation: "run keel --init --target codex or openspec update --force",
    };
  }
  const location = path.join(".opencode", "commands");
  return {
    location,
    paths: OPENSPEC_COMMAND_IDS.map((id) =>
      path.join(repo, location, `opsx-${id}.md`)
    ),
    remediation: "run keel --init --target opencode to remove them",
    retired: true,
  };
}

function commandPathForAction(target, repo, action) {
  if (target === "claude") {
    return path.join(repo, ".claude", "commands", "opsx", `${action}.md`);
  }
  if (target === "codex") {
    return codexOpenSpecLayout(repo) === "legacy"
      ? path.join(codexHome(), "prompts", `opsx-${action}.md`)
      : null;
  }
  return path.join(repo, ".opencode", "commands", `opsx-${action}.md`);
}

function openspecOverlaySurfacesForTarget(target, repo) {
  const skillRoot = openspecSkillRootForTarget(target, repo);
  return OPENSPEC_OVERLAY_ACTIONS.flatMap((action) => {
    if (action === "propose" && target === "opencode") {
      return [];
    }
    const skillName = {
      propose: "openspec-propose",
      apply: "openspec-apply-change",
      archive: "openspec-archive-change",
      sync: "openspec-sync-specs",
    }[action];
    // Claude and OpenCode command files are no longer generated (#406); one a
    // repository still holds from a `both` delivery keeps its overlay until
    // the next `keel --init` removes it.
    const command = commandPathForAction(target, repo, action);
    const keepsCommand = command !== null
      && (target === "codex" || fs.existsSync(command));
    return [
      {
        action,
        path: path.join(repo, skillRoot, skillName, "SKILL.md"),
      },
      ...(keepsCommand ? [{ action, path: command }] : []),
    ];
  });
}

// Derived from the managed set rather than written beside it. The label was
// the literal string "apply/archive", which was correct while those were the
// managed actions and became wrong — silently — the moment a third joined them.
// `propose` is excluded because its overlay governs authoring rather than a
// state-changing command, and the doctor line counts the command surfaces.
function overlayActionLabel() {
  return OPENSPEC_OVERLAY_ACTIONS.filter((action) => action !== "propose")
    .join("/");
}

function overlayTitleForAction(action) {
  return {
    propose: "Keel Authoring Overlay",
    apply: "Keel Apply Overlay",
    archive: "Keel Archive Overlay",
    sync: "Keel Sync Overlay",
  }[action];
}

function keelOpenSpecOverlay(action) {
  if (action === "propose") {
    const lines = [
      OPENSPEC_SURFACE_OVERLAY_START,
      "## Keel Authoring Overlay",
      "",
      "Keel rules below take precedence over conflicting generic OpenSpec instructions in this file.",
      "",
      "- Invoke the OpenSpec CLI as `keel openspec …` throughout this file. The commands below are written as a bare `openspec`, which resolves only where OpenSpec is separately installed on PATH; `keel openspec` resolves either way, and `keel --doctor` reports which case this repository is.",
      "",
      "### Expectation alignment before specs and tasks finalize",
      "",
      "- Before specs and executable tasks are finalized, run `align-expectations`: quick path for complete low-risk requests, deep path when a material choice can change user-visible behavior, an external interface, acceptance, security/privacy/permission boundaries, data migration, protocol/state/timing/reset semantics, generated equivalence, irreversible cost, or a dependency commitment.",
      "- Inspect repository code, tests, docs, and existing OpenSpec authority before asking the user a question those sources can answer; record verified facts as F<n> and escalate only user-owned product choices.",
      "- Label inferred expectations as candidates; user silence never authorizes a material product decision, and unaccepted material candidates stay Q<n> or are explicitly discarded.",
      "- In deep mode ask one material decision at a time, explain why it matters, and provide a recommended answer; stop once executable authority is clear.",
      "- Route accepted outcomes to their durable owners (proposal, design, specs, tasks); create no separate alignment ledger and keep HANDOFF pointer-only.",
      "- A proposal may start as a concise hypothesis, but no affected task becomes executable while a material expectation is unaccepted, unverified, unowned, and undiscarded.",
      OPENSPEC_SURFACE_OVERLAY_END,
      "",
    ];
    return lines.join("\n");
  }
  // Sync mirrors archive's structure and not its content: the two are gated
  // identically, so the gate and the subagent sentence are the same statements
  // with `sync` in them. What differs is the artifact consequence — archive
  // warns about re-applying a promoted delta, and sync is the thing that
  // promotes it, so it says so from its own side. A reader who only ever sees
  // one of the two surfaces still learns the pairing.
  const syncBody = [
    "- Verify task evidence, follow-up ownership, and completion gates before syncing.",
    "- Sync completion is gated by `keel gate change-close --action sync` plus `review-checklist`; there is no runtime hook for it, so running the gate is the agent's own step.",
    "- Before syncing, each related critical expectation must have behavior evidence, a durable follow-up owner, or an explicit discard reason.",
    SUBAGENT_SENTENCE,
    "- Syncing promotes the change's spec delta into `openspec/specs/`. A later archive of the same change must use `--skip-specs`, because archive is not idempotent over an already-promoted delta.",
  ];
  if (action === "sync") {
    return [
      OPENSPEC_SURFACE_OVERLAY_START,
      `## ${overlayTitleForAction(action)}`,
      "",
      "Keel rules below take precedence over conflicting generic OpenSpec instructions in this file.",
      "",
      "- Invoke the OpenSpec CLI as `keel openspec …` throughout this file. The commands below are written as a bare `openspec`, which resolves only where OpenSpec is separately installed on PATH; `keel openspec` resolves either way, and `keel --doctor` reports which case this repository is.",
      "",
      ...syncBody,
      OPENSPEC_SURFACE_OVERLAY_END,
      "",
    ].join("\n");
  }
  const actionBody =
    action === "apply"
      ? [
          "- Work through the unchecked tasks of an approved `tasks.md` in order, each started by `keel gate task-start` and completed by `keel gate task-complete`; every stop trigger still halts.",
          "- Run the Task Authoring Gate: each relevant critical expectation must be covered by a slice, deferred to a durable owner, or explicitly discarded.",
          "- Run the Slice Start Gate: selected current slices must name source expectations and compile to a capsule whose Read, Touch, Acceptance, Verify checks, and Stop/Autonomy boundaries are complete before implementation.",
          "- Rough future slices may remain drafts, but cannot be selected for implementation or marked complete.",
          "- Obey the selected task contract: Read is required starting context, Touch is the write boundary, Verify checks prove Acceptance, and the Autonomy boundary controls fallback decisions.",
          "- When implementation exposes a material expectation, acceptance boundary, or user-owned decision absent from durable authority, stop before implementing that choice, rerun `align-expectations`, and reauthor the affected proposal/design/spec/task authority first.",
          "- A discovered repository fact that does not change accepted behavior or scope may be recorded and execution continues inside the existing task boundary without a product interview.",
          "- Consult the repository's standing authorization in `keel/config.yaml` before asking the user to confirm a repository action: a standing-authorized action proceeds without a per-occurrence confirmation, and an undeclared action still requires the confirmation it requires today.",
          "- A standing authorization covers the action and never substitutes for a gate, evidence, or Review; it removes the confirmation, not the record, and it is not a trigger to perform the action.",
        ]
      : [
          "- Archive completion is gated by `keel gate change-close --action archive` plus `review-checklist`; verify task evidence, follow-up ownership, and completion gates before proceeding.",
          "- Before final sync/archive, each related critical expectation must have behavior evidence, a durable follow-up owner, or an explicit discard reason.",
          "- When the `openspec-sync-specs` skill has already promoted the change's spec delta, run the archive with `--skip-specs` so the promoted delta is not re-applied; archive is not idempotent over an already-synced delta.",
          "- After archiving, run `keel guard clear` to drop the change's guard manifest; the read-only gate never clears it for you.",
          "- A repository that standing-authorizes `archive` in `keel/config.yaml` does not need the per-occurrence archive confirmation; a repository that declares nothing still needs it.",
          "- The completion gate and follow-up ownership checks still run unchanged under a standing authorization; it removes the confirmation, not the proof.",
        ];

  const lines = [
    OPENSPEC_SURFACE_OVERLAY_START,
    `## ${overlayTitleForAction(action)}`,
    "",
    "Keel rules below take precedence over conflicting generic OpenSpec instructions in this file.",
    "",
    "- Invoke the OpenSpec CLI as `keel openspec …` throughout this file. The commands below are written as a bare `openspec`, which resolves only where OpenSpec is separately installed on PATH; `keel openspec` resolves either way, and `keel --doctor` reports which case this repository is.",
    "",
    SUBAGENT_SENTENCE,
    ...actionBody,
    OPENSPEC_SURFACE_OVERLAY_END,
    "",
  ];
  return lines.join("\n");
}

function mergeOpenSpecSurfaceOverlay(content, action) {
  const overlay = keelOpenSpecOverlay(action);
  if (OPENSPEC_SURFACE_OVERLAY_RE.test(content)) {
    return content.replace(OPENSPEC_SURFACE_OVERLAY_RE, overlay.trimEnd());
  }
  const separator = content.endsWith("\n") ? "\n" : "\n\n";
  return `${content}${separator}${overlay}`;
}

// The block plus the whitespace the merge above inserted in front of it, and
// nothing else. Removing only the marked span leaves the separator behind, and
// the file it is left in belongs to OpenSpec — so the match takes the newlines
// immediately before the block and the one that closes it, and the replacement
// puts a single newline back. A blank line anywhere else in the file is not
// this code's business.
const OPENSPEC_SURFACE_OVERLAY_REMOVE_RE =
  /\n*<!--\s*keel:openspec-surface-overlay(?:\s+[^>]*)?\s*-->[\s\S]*?<!--\s*keel:openspec-surface-overlay:end\s*-->[ \t]*\n?/;

function stripOpenSpecSurfaceOverlay(content) {
  let next = content;
  // A loop rather than one replace: the merge only ever writes one block, so a
  // file carrying two is already unexpected, and leaving one of them behind is
  // the outcome this is cheapest to rule out.
  while (OPENSPEC_SURFACE_OVERLAY_RE.test(next)) {
    next = next.replace(OPENSPEC_SURFACE_OVERLAY_REMOVE_RE, (match, offset) =>
      offset === 0 ? "" : "\n"
    );
  }
  return next;
}

function removeOpenSpecSurfaceOverlay(repo, target, options = {}) {
  const counts = {
    removed: 0,
    absent: 0,
    missing: 0,
  };

  for (const surface of openspecOverlaySurfacesForTarget(target, repo)) {
    // `keel --install` without `--init` never creates the OpenSpec surfaces,
    // so a repository can legitimately reach uninstall with none of them.
    if (!fs.existsSync(surface.path)) {
      counts.missing += 1;
      continue;
    }
    const content = fs.readFileSync(surface.path, "utf8");
    const next = stripOpenSpecSurfaceOverlay(content);
    if (next === content) {
      counts.absent += 1;
      continue;
    }
    counts.removed += 1;
    if (options.dryRun) {
      process.stdout.write(
        `keel: would remove OpenSpec ${surface.action} overlay from ${surface.path}\n`
      );
      continue;
    }
    fs.writeFileSync(surface.path, next, "utf8");
  }

  // Always reported, including `removed=0`: an uninstall that found nothing to
  // clean and an uninstall that never looked leave the same tree behind, and
  // the second one is the defect this exists to close.
  process.stdout.write(
    `keel: ${options.dryRun ? "would remove " : ""}OpenSpec ${overlayActionLabel()} `
      + `overlay removed=${counts.removed} absent=${counts.absent} `
      + `missing=${counts.missing}\n`
  );

  return { status: 0, ...counts };
}

function refreshOpenSpecSurfaceOverlay(repo, target, options = {}) {
  const surfaces = openspecOverlaySurfacesForTarget(target, repo);
  const counts = {
    refreshed: 0,
    current: 0,
    missing: 0,
  };

  // A dry run and the real run classify each surface the same way, from the
  // same read-and-compare, so the plan cannot drift from the outcome. The dry
  // run used to list every surface without reading one, which over-reported as
  // badly as `--check` under-reported by never reaching this step at all.
  for (const surface of surfaces) {
    if (!fs.existsSync(surface.path)) {
      counts.missing += 1;
      continue;
    }
    const content = fs.readFileSync(surface.path, "utf8");
    const next = mergeOpenSpecSurfaceOverlay(content, surface.action);
    if (next === content) {
      counts.current += 1;
      continue;
    }
    counts.refreshed += 1;
    if (options.dryRun) {
      process.stdout.write(
        `keel: would refresh OpenSpec ${surface.action} overlay in ${surface.path}\n`
      );
      continue;
    }
    fs.writeFileSync(surface.path, next, "utf8");
  }

  if (counts.refreshed > 0 || counts.current > 0) {
    process.stdout.write(
      `keel: ${options.dryRun ? "would refresh " : ""}OpenSpec ${overlayActionLabel()} `
        + `overlay refreshed=${counts.refreshed} current=${counts.current} `
        + `missing=${counts.missing}\n`
    );
  }

  return { status: 0, ...counts };
}

// A project's session usually refreshes through the one target it runs on,
// while OpenSpec's own update rewrites every tool's surfaces at once. Each
// target the repository carries is therefore refreshed, the selected one
// first; a target with no surfaces is left uncreated (#204).
function refreshInstalledTargetOverlays(repo, selected, options = {}) {
  const targets = [selected, ...installedOpenSpecTargets(repo).filter((t) => t !== selected)];
  let status = 0;
  for (const target of targets) {
    const result = refreshOpenSpecSurfaceOverlay(repo, target, options);
    if (result.status !== 0) status = result.status;
  }
  return { status };
}

function hasCurrentOpenSpecOverlay(filePath) {
  if (!fs.existsSync(filePath)) {
    return false;
  }
  return fs
    .readFileSync(filePath, "utf8")
    .includes(OPENSPEC_SURFACE_OVERLAY_START);
}

// An overlay from another Keel version is present, not missing: it names the
// gates of the version that wrote it, and the remedy is a refresh. Reporting
// it as missing sent the reader looking for files that were there (#204).
function hasStaleOpenSpecOverlay(filePath) {
  if (!fs.existsSync(filePath)) return false;
  const content = fs.readFileSync(filePath, "utf8");
  return OPENSPEC_SURFACE_OVERLAY_RE.test(content)
    && !content.includes(OPENSPEC_SURFACE_OVERLAY_START);
}

function countOpenSpecOverlays(paths) {
  const current = paths.filter(hasCurrentOpenSpecOverlay);
  const stale = paths.filter(hasStaleOpenSpecOverlay);
  return { existing: current.length, stale: stale.length, total: paths.length };
}

function overlayStatus(counts) {
  if (counts.existing === counts.total) return "ok";
  return counts.stale > 0 && counts.existing + counts.stale === counts.total ? "stale" : "missing";
}

function overlayCountDetail(counts, location) {
  const stale = counts.stale > 0 ? `, ${counts.stale} from another Keel version` : "";
  return `${formatCount(counts, location)}${stale}`;
}

function overlayRemediation(target) {
  return `run keel --init --target ${target} or keel --install --target ${target}`;
}

// Only repository-owned surfaces enroll a target. Global Codex prompts can
// belong to a different project and must not cause this one to be rewritten.
function installedOpenSpecTargets(repo) {
  return ["claude", "codex", "opencode"].filter((target) => {
    const roots = target === "codex"
      ? [".agents/skills", ".codex/skills"]
      : [openspecSkillRootForTarget(target, repo)];
    return roots.some((root) => OPENSPEC_SKILLS.some((skill) =>
      fs.existsSync(path.join(repo, root, skill, "SKILL.md"))
    )) || (target !== "codex" && commandSurfaceForTarget(target, repo).paths
      .some((file) => fs.existsSync(file)));
  });
}

function printAdditionalOverlayHealth(repo, selectedTarget) {
  for (const target of installedOpenSpecTargets(repo)) {
    if (target === selectedTarget) continue;
    const counts = countOpenSpecOverlays(
      openspecOverlaySurfacesForTarget(target, repo).map((surface) => surface.path)
    );
    const name = { claude: "Claude", codex: "Codex", opencode: "OpenCode" }[target];
    printDoctorLine(
      `${name} Keel ${overlayActionLabel()} overlay`,
      overlayStatus(counts),
      `${overlayCountDetail(counts, "skills and commands")}`
        + (overlayStatus(counts) === "ok" ? "" : `; ${overlayRemediation(target)}`)
    );
  }
}

function printTargetSurface(repo, target) {
  process.stdout.write("\nTarget surface:\n");

  const agentsPath = path.join(repo, "AGENTS.md");
  const hasBootstrap =
    fs.existsSync(agentsPath)
    && /<!--\s*keel:start(?:\s+[^>]*)?\s*-->/.test(
      fs.readFileSync(agentsPath, "utf8")
    );
  printDoctorLine(
    "bootstrap",
    hasBootstrap ? "ok" : "missing",
    hasBootstrap
      ? "AGENTS.md carries the Keel managed bootstrap block"
      : `AGENTS.md bootstrap missing; run keel --install --target ${target}`
  );
  if (target === "claude") {
    const claudePath = path.join(repo, "CLAUDE.md");
    const hasImport =
      fs.existsSync(claudePath)
      && fs.readFileSync(claudePath, "utf8").includes("@AGENTS.md");
    printDoctorLine(
      "CLAUDE import",
      hasImport ? "ok" : "missing",
      hasImport
        ? "CLAUDE.md imports @AGENTS.md"
        : "CLAUDE.md lacks the @AGENTS.md import; run keel --install --target claude"
    );
  }

  if (target === "opencode") {
    printDoctorLine(
      "native plugin",
      "manual",
      "OpenCode has no v4 native plugin surface; existing artifacts are "
        + "compatibility-only outside v4 support"
    );
  } else {
    const manifestRelative = path.join(
      "plugins",
      "keel",
      target === "codex" ? ".codex-plugin" : ".claude-plugin",
      "plugin.json"
    );
    const manifestPath = path.join(repo, manifestRelative);
    let sourceStatus = "missing";
    let sourceDetail = `plugin source absent at ${manifestRelative}`;
    if (fs.existsSync(manifestPath)) {
      try {
        const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
        if (manifest.name === "keel" && manifest.version) {
          sourceStatus = "ok";
          sourceDetail = `plugin source valid (keel ${manifest.version}) at ${manifestRelative}`;
          if (manifest.version.split("+")[0] !== PACKAGE_JSON.version) {
            sourceStatus = "warning";
            sourceDetail =
              `plugin source version ${manifest.version} differs from CLI `
              + `${PACKAGE_JSON.version}; align both before release`;
          }
        } else {
          sourceStatus = "warning";
          sourceDetail = `plugin source invalid at ${manifestRelative}`;
        }
      } catch {
        sourceStatus = "warning";
        sourceDetail = `plugin source unreadable at ${manifestRelative}`;
      }
    }
    // Development-only check: plugins/keel/ exists only in Keel's own source
    // repository, so in a consuming project it is permanently `missing` and
    // there is nothing the author can do about it.
    if (isKeelSourceRepo(repo)) {
      printDoctorLine("native plugin source", sourceStatus, sourceDetail);
    }
    printDoctorLine(
      "native plugin runtime",
      "manual",
      "marketplace install, enablement, hook trust/activation, and behavior "
        + `need runtime evidence; install via ${
          target === "codex"
            ? "codex plugin add keel@<marketplace>"
            : "claude plugin install keel@<marketplace>"
        } and verify in a fresh session`
    );
    if (target === "claude") {
      const [status, detail] = pluginAutoUpdateDeclaration(repo);
      printDoctorLine("plugin auto-update", status, detail);
    }
  }

  const openspecSkillRoot = openspecSkillRootForTarget(target, repo);
  const openspecSkillPaths = OPENSPEC_SKILLS.map((skill) =>
    path.join(repo, openspecSkillRoot, skill, "SKILL.md")
  );
  const openspecSkillCounts = countExisting(openspecSkillPaths);
  printDoctorLine(
    "OpenSpec action skills",
    surfaceStatus(openspecSkillCounts),
    formatCount(openspecSkillCounts, openspecSkillRoot)
  );

  printDoctorLine(
    "Keel behavioral skills",
    "plugin",
    isKeelSourceRepo(repo)
      ? "keel-* skills are delivered by the installed Keel plugin (see native "
        + "plugin status above); install the plugin if it is missing"
      : "keel-* skills are delivered by the installed Keel plugin; verify it "
        + "with the runtime's own plugin listing, since Keel cannot observe "
        + "installation from this repository"
  );

  const commands = commandSurfaceForTarget(target, repo);
  if (commands.retired) {
    const leftover = commands.paths.filter((file) => fs.existsSync(file));
    printDoctorLine(
      "OpenSpec commands",
      leftover.length === 0 ? "ok" : "duplicate",
      leftover.length === 0
        ? "none; Keel generates OpenSpec's workflows as skills only (#406)"
        : `${leftover.length} command file${leftover.length === 1 ? "" : "s"} under ${commands.location} `
          + `duplicate the skills; ${commands.remediation}`
    );
  } else if (commands.skillsOnly) {
    printDoctorLine(
      "OpenSpec commands",
      "ok",
      `none; OpenSpec 1.13 and later surface Codex's workflows as the skills under `
        + `${commands.location}`
    );
  } else {
    const commandCounts = countExisting(commands.paths);
    const commandDetail =
      surfaceStatus(commandCounts) === "ok"
        ? formatCount(commandCounts, commands.location)
        : `${formatCount(commandCounts, commands.location)}; ${commands.remediation}`;
    printDoctorLine(
      "OpenSpec commands",
      surfaceStatus(commandCounts),
      commandDetail
    );
  }

  const overlayPaths = openspecOverlaySurfacesForTarget(target, repo).map(
    (surface) => surface.path
  );
  const overlayCounts = countOpenSpecOverlays(overlayPaths);
  const overlayDetail =
    overlayStatus(overlayCounts) === "ok"
      ? formatCount(overlayCounts, `${overlayActionLabel()} skills and commands`)
      : `${overlayCountDetail(
          overlayCounts,
          `${overlayActionLabel()} skills and commands`
        )}; ${overlayRemediation(target)}`;
  printDoctorLine(
    `Keel ${overlayActionLabel()} overlay`,
    overlayStatus(overlayCounts),
    overlayDetail
  );

  process.stdout.write("\n");
  process.stdout.write(renderCapabilities(probeCapabilities(repo, target)));
}

function runDoctor(options) {
  if (options.updateSource !== null) {
    fail("--source only applies to --update");
  }
  if (options.dryRun || options.forceTemplateUpdate) {
    fail("--doctor does not accept --dry-run or --force-template-update");
  }

  const repo = path.resolve(options.repo || process.cwd());
  process.stdout.write(`keel doctor for ${repo}\n`);

  // The version is printed, not just a verdict: `ok` with no number behind it
  // is a claim the reader cannot check, and it was the wrong claim here for as
  // long as this line existed.
  const minimumPython = MINIMUM_PYTHON.join(".");
  const interpreter = resolveInterpreter();
  if (interpreter.candidate) {
    printDoctorLine(
      "python3",
      "ok",
      `${formatCommand(interpreter.candidate.command, interpreter.candidate.prefixArgs)}`
        + ` (${interpreter.version})`
    );
  } else {
    const runnable = interpreter.tried.filter((entry) => entry.version);
    printDoctorLine(
      "python3",
      runnable.length > 0 ? "problem" : "missing",
      runnable.length > 0
        ? `needs ${minimumPython} or newer; found ${describeTried(runnable)}`
        : `needs ${minimumPython} or newer; set KEEL_PYTHON or install Python 3`
    );
  }

  const openspec = findOpenSpecCommand();
  if (!openspec) {
    printDoctorLine(
      "openspec",
      installedOpenSpecPackage() ? "problem" : "missing",
      unresolvedOpenSpecAdvice()
    );
  } else {
    const bareOpenSpecOnPath =
      !path.isAbsolute(openspec)
      || runCommand("openspec", ["--version"], {
        stdio: "ignore",
        silentNotFound: true,
      }) === 0;
    const resolvedVersion = openspecReportedVersion(openspec);
    const declared = declaredOpenSpecVersion(repo);
    const mismatched = Boolean(
      resolvedVersion
      && declared.state === "declared"
      && resolvedVersion !== declared.version
    );
    const where = bareOpenSpecOnPath
      ? openspec
      : `${openspec} is keel-resolvable but bare \`openspec\` is not on PATH — use \`keel openspec\``;
    // Two versions on one line need two owners. `repo` is the repository named
    // on doctor's first line; the answering build is attributed by the path
    // already printed beside it.
    const declaredText = {
      declared: `repo pins ${declared.version}`,
      none: "repo declares no OpenSpec version",
      unreadable: `repo ${declared.lockName} unreadable`,
    }[declared.state];
    const versions = `${resolvedVersion || "version unreadable"}, ${declaredText}`;
    printDoctorLine(
      "openspec",
      mismatched || !bareOpenSpecOnPath ? "warning" : "ok",
      mismatched
        ? `${where} (${versions}) — validation is answering from a different `
          + "build than this repository pins, which is what a green pipeline "
          + "and a red worktree look like. Keel reports which one answered "
          + "and selects none."
        : `${where} (${versions})`
    );
  }

  const surfaces = surfaceGeneratorVersion(repo);
  const running = openspec ? openspecReportedVersion(openspec) : null;
  if (surfaces && running) {
    const newer = compareVersions(surfaces, running) > 0;
    printDoctorLine(
      "OpenSpec surfaces",
      newer ? "warning" : "ok",
      newer
        ? `written by OpenSpec ${surfaces}, newer than the OpenSpec Keel runs `
          + `(${running}); keel --init leaves them unrewritten rather than `
          + `downgrading them, and keel --install --target ${options.target} `
          + "refreshes the protocol without touching them"
        : `written by OpenSpec ${surfaces}; Keel runs ${running}`
    );
  }

  printProtocolVersionDrift(repo, options.target);

  process.stdout.write("\nProject status:\n");
  const checkStatus = runPython(
    INSTALL_SCRIPT,
    installerArgs(options, ["--check"])
  );

  if (openspec && fs.existsSync(path.join(repo, "openspec", "schemas", "keel-spec-driven"))) {
    const schemaStatus = runCommand(
      openspec,
      ["schema", "validate", "keel-spec-driven"],
      { cwd: repo }
    );
    printDoctorLine(
      "keel-spec-driven schema",
      schemaStatus === 0 ? "ok" : "failed"
    );
  } else {
    printDoctorLine(
      "keel-spec-driven schema",
      "not checked",
      "run keel --init or keel --install first"
    );
  }

  printTargetSurface(repo, options.target);
  printAdditionalOverlayHealth(repo, options.target);
  printLensSurface(repo, options.target);
  const authorizationOk = printStandingAuthorizationSurface(repo);
  printPrecedentSurface(repo);
  printTriageSurface(repo);
  printRoutingSurface(repo);
  printExecutorTierSurface(repo);
  printMergeSurface(repo);
  printFastPrePushSurface(repo);
  printSourceRepoCliResolution(repo);
  printChatRoleDrift(repo);
  printTickIssueChecks(repo);
  printMergedBranches(repo);
  printLaunchdJobs();

  return authorizationOk ? checkStatus : 1;
}

// Chat role bindings that drifted from where sessions run (#301 D3). Nothing
// is printed without a chat store that binds roles.
// A launchd job that names a node an upgrade removed fails silently every
// interval (#387); the report does not change doctor's exit status, since the
// job belongs to the machine and not to this repository.
function printLaunchdJobs() {
  const jobs = require("../src/core/launchd").inspectJobs();
  if (!jobs.length) return;
  const gone = jobs.filter((job) => !job.exists);
  for (const job of gone) {
    printDoctorLine(
      "launchd",
      "problem",
      `${job.name} runs ${job.program || "no program"}, which does not exist; re-create it with \`${job.recreate}\``
    );
  }
  if (!gone.length) printDoctorLine("launchd", "ok", `${jobs.length} dev.keel job${jobs.length === 1 ? "" : "s"}, each naming a node that exists`);
}

// Each role's merged, unused task branches (#469 D5): a count pointing at
// `keel branches`, never a deletion.
// The issue state `keel tick` last recorded (#473 D3); nothing when no tick
// has fetched here.
function printTickIssueChecks(repo) {
  let where = null;
  try {
    where = require("../src/core/chat/store").locate(repo);
  } catch {
    where = null;
  }
  if (!where) return;
  const file = path.join(where.root, "tick", "state.json");
  let issues = null;
  try {
    issues = JSON.parse(fs.readFileSync(file, "utf8")).issues || null;
  } catch {
    issues = null;
  }
  if (!issues || !issues.state) return;
  if (issues.state === "failed") printDoctorLine("issue checks", "not checked", `${issues.text} (tick at ${issues.at})`);
  else if (issues.state === "read") printDoctorLine("issue checks", "ok", `last read by \`keel tick\` at ${issues.at}`);
  else printDoctorLine("issue checks", "ok", "nothing needs them: no issue_roles route and no issue wait");
}

function printMergedBranches(repo) {
  let where = null;
  try {
    where = require("../src/core/chat/store").locate(repo);
  } catch {
    where = null;
  }
  if (!where || !fs.existsSync(path.join(where.root, "roles.json"))) return;
  const branches = require("../src/core/branches");
  const roles = [...new Set(Object.values(JSON.parse(fs.readFileSync(path.join(where.root, "roles.json"), "utf8"))).filter(Boolean))].sort();
  const counts = [];
  for (const role of roles) {
    let names = [];
    try {
      names = [...new Set(branches.merged(where, role).branches.map((b) => b.branch))];
    } catch {
      continue;
    }
    if (names.length) counts.push(`${role} ${names.length}`);
  }
  if (!counts.length) {
    printDoctorLine("branches", "ok", "no role has a merged task branch left");
    return;
  }
  printDoctorLine("branches", "merged", `${counts.join(", ")} merged task branch(es) may be deleted; \`keel branches --role <role>\` lists them`);
}

function printChatRoleDrift(repo) {
  let where = null;
  try {
    where = require("../src/core/chat/store").locate(repo);
  } catch {
    where = null;
  }
  if (!where || !fs.existsSync(path.join(where.root, "roles.json"))) return;
  const drift = require("../src/core/chat/drift");
  const lines = drift.driftLines(drift.roleDrift(where));
  if (!lines.length) {
    printDoctorLine("chat roles", "ok", "every binding points at a worktree, and no role with something waiting has gone unattended");
    return;
  }
  for (const line of lines) printDoctorLine("chat roles", "drift", line.text);
}

// Only meaningful in Keel's own repository: a bare `keel` resolves to the
// installed package, so gate commands verify the released CLI rather than the
// working tree. The failure mode is a silently stale result, not an error, so
// it is worth stating rather than leaving to be discovered.
function printSourceRepoCliResolution(repo) {
  if (!isKeelSourceRepo(repo)) return;
  process.stdout.write("\nKeel source repository:\n");
  printDoctorLine(
    "gate CLI resolution",
    "advisory",
    "a bare `keel` runs the installed package, so gate results will not "
      + "reflect uncommitted changes to gate, contract, or capability code; "
      + "run `node bin/keel.js gate <stage> . --change <c> --task <t>` "
      + "instead — the repository argument is required"
  );
}

function readFastCheck(repo) {
  const configPath = path.join(repo, "keel", "config.yaml");
  if (!fs.existsSync(configPath)) return null;
  for (const line of fs.readFileSync(configPath, "utf8").split(/\r?\n/)) {
    const stripped = line.trim();
    if (stripped.startsWith("#")) continue;
    const match = stripped.match(/^fast_check\s*:\s*(.+?)\s*$/);
    if (match) return match[1];
  }
  return null;
}

function gitConfigHooksPath(repo) {
  const result = spawnSync(
    "git",
    ["-C", repo, "config", "--local", "--get", "core.hooksPath"],
    { encoding: "utf8" }
  );
  if (result.status !== 0) return null;
  const value = (result.stdout || "").trim();
  return value || null;
}

function printStandingAuthorizationSurface(repo) {
  process.stdout.write("\nStanding authorization:\n");
  const { declared, scopes, unknown, message, otherRoles, entries, role } = readStandingAuthorization(repo);
  if (unknown.length > 0) {
    printDoctorLine("authorize", "failed", message);
    return false;
  }
  printDoctorLine(
    "authorize",
    declared.length > 0 ? "ok" : "none",
    (declared.length > 0
      ? `declared in keel/config.yaml: ${declared.join(", ")}`
      : "undeclared; every action stays hard-stop")
      + (otherRoles.length ? `; for other roles than ${role || "this unbound session"}: ${otherRoles.join(", ")}` : "")
  );
  for (const action of STANDING_AUTHORIZATION_ACTIONS) {
    // Keyed on the action, never on the declared string. A scoped entry is
    // `issue:acme/widgets` in the file, so a membership test against the bare
    // name reports it `not authorized` on the same screen that has just listed
    // it as declared — a diagnostic contradicting itself six lines apart.
    if (!scopes.has(action)) {
      printDoctorLine(action, "not authorized");
      continue;
    }
    const scope = scopes.get(action);
    printDoctorLine(
      action,
      "authorized",
      scope ? `scoped to ${scope}` : ""
    );
  }
  // Said once, and only where it applies. Keel invokes no tracker client and
  // observes none that an agent runs, so the scope is a declaration carried to
  // the people who read it rather than a boundary anything holds. A reader who
  // took it for a sandbox would be relying on nothing.
  if ([...scopes.entries()].some(([action, scope]) => scope !== null && action !== "push" && action !== "push-protected")) {
    printDoctorLine(
      "scope",
      "carried",
      "Keel records a tracker, chat, or scratchpad scope and does not enforce "
        + "it — it invokes no tracker client and cannot observe one, so the "
        + "boundary is kept by whoever acts, not by this check"
    );
  }
  // The one scope something holds (#257): the Claude write guard reads the
  // `push:` globs and refuses a `git push` to any other branch, with or
  // without a task. Codex has no such hook, so there it is a declaration too.
  if (scopes.get("push-protected")) {
    printDoctorLine(
      "protected push",
      "asked",
      "the Claude write guard asks the user to confirm each push to these "
        + "branches, one command at a time; a role after `@` limits who may be "
        + "asked, and a mode that cannot ask (bypassPermissions, dontAsk) is refused"
    );
  }
  // Per bound role, the scoped entries that reach it (#378 D4).
  if (entries.some((entry) => entry.role)) {
    let bound = [];
    try {
      const store = require("../src/core/chat/store");
      const where = store.locate(repo);
      if (where) bound = [...new Set(Object.values(store.readRoles(where.root)).map((name) => store.canonicalRole(where.root, name)))].sort();
    } catch {
      bound = [];
    }
    for (const name of bound) {
      const reach = entries.filter((entry) => entry.scope !== null && (!entry.role || roleMatches(entry.role, name))).map((entry) => entry.entry);
      printDoctorLine("roles", name, reach.length ? reach.join(", ") : "no scoped grant");
    }
  }
  if (scopes.get("push")) {
    printDoctorLine(
      "push scope",
      "enforced",
      "the Claude write guard enforces these globs: it refuses a `git push` "
        + "to any other branch, or one whose target it cannot determine, with "
        + "or without a task; on Codex the scope is carried, not enforced"
    );
  }
  return true;
}

function printRoutingSurface(repo) {
  process.stdout.write("\nFull/Lite routing:\n");
  const { paths, unreadable } = readFullModePaths(repo);
  if (unreadable.length > 0) {
    // Same verdict the projection reaches, from the same read: a diagnostic
    // that reported health while `keel context` reported the conservative
    // state would leave a reader to pick which one to believe.
    printDoctorLine(
      "full_mode_paths",
      "failed",
      `${fullModePathsUnreadableMessage(unreadable)} Every change routes Full `
        + "until it is corrected."
    );
    return;
  }
  if (paths.length === 0) {
    printDoctorLine(
      "full_mode_paths",
      "none",
      "undeclared; routing follows the size heuristic alone"
    );
    return;
  }
  printDoctorLine(
    "full_mode_paths",
    "ok",
    `declared in keel/config.yaml: ${paths.length} `
      + `${paths.length === 1 ? "path always routes" : "paths always route"} Full`
  );
  for (const entry of paths) printDoctorLine(entry.path, "Full", entry.reason);
}

// Reported whether or not it is declared, because the default is the state a
// reader most needs to see: a repository that declared nothing is loading every
// skill's guidance and has no other surface that says so.
// Reported whether or not it is declared: the doctor is where a reader goes to
// learn what is and is not declared, and "undeclared" is itself the answer to
// "does anything here claim merges are reviewed".
function printMergeSurface(repo) {
  process.stdout.write("\nMerge:\n");
  const merge = readMergeDeclaration(repo);
  if (!merge.declared) {
    printDoctorLine("merge", "undeclared", "nothing here claims how merges happen");
    return;
  }
  if (merge.unknown.length > 0) {
    printDoctorLine("merge", "unreadable", merge.message);
    return;
  }
  printDoctorLine(
    "merge",
    merge.kind === "repository" ? `repository:${merge.check}` : merge.kind,
    merge.kind === "repository"
      ? `declared in keel/config.yaml - the default branch merges when ${merge.check} passes, with no human review; the agent still never merges`
      : "declared in keel/config.yaml - a person merges"
  );
}

function printExecutorTierSurface(repo) {
  process.stdout.write("\nExecutor tier:\n");
  const { declared, tier, unknown, message } = readExecutorTier(repo);
  if (unknown.length > 0) {
    printDoctorLine("executor_tier", "unreadable", message);
    return;
  }
  printDoctorLine(
    "executor_tier",
    tier,
    (declared ? "declared in keel/config.yaml" : "undeclared; the default")
      + " - affects which skill guidance is read and nothing else"
  );
}

function printTriageSurface(repo) {
  process.stdout.write("\nUnattended triage:\n");
  const { labels, issues, unreadable } = readTriagePolicy(repo);
  // An unreadable declaration is reported as broken rather than as absent. The
  // owner who typed it needs to know their file is the reason nothing runs,
  // which "undeclared" would tell them is not the case.
  if (unreadable.length > 0) {
    printDoctorLine(
      "triage",
      "unreadable",
      `keel/config.yaml declares triage entries Keel could not read — `
        + `${unreadable.join(", ")}; no issue starts work unattended until the `
        + "declaration is corrected"
    );
    return;
  }
  // Only the declared sources are named. Naming a source with nothing under it
  // would read as a policy that exists, on the one surface asked to answer
  // "what may start work here" in a single line.
  const declared = [];
  if (labels.length > 0) declared.push(`issues labelled ${labels.join(", ")}`);
  if (issues.length > 0) declared.push(`issues numbered ${issues.join(", ")}`);
  printDoctorLine(
    "triage",
    declared.length > 0 ? "ok" : "none",
    declared.length > 0
      ? `${declared.join(", and ")} may start work unattended; `
        + "admission decides nothing after it, and no declaration authorizes a merge"
      : "undeclared; no issue starts work unattended"
  );
}

function printPrecedentSurface(repo) {
  process.stdout.write("\nPrecedent store:\n");
  const store = readPrecedentStore(repo);
  if (store.precedents.length === 0) {
    printDoctorLine(
      "precedents",
      "none",
      store.declared
        ? `declared at ${store.declared}, which holds no precedents here; `
          + "an absent store behaves exactly as an undeclared one"
        : "undeclared; no precedent informs any decision"
    );
    return;
  }
  const authorized = store.precedents.filter(
    (item) => item.status === "authorized"
  ).length;
  printDoctorLine("precedents", String(store.precedents.length), store.declared);
  printDoctorLine(
    "authorized",
    String(authorized),
    `${store.precedents.length - authorized} recorded, offered as a `
      + "recommendation rather than applied"
  );
  const incomplete = store.precedents.filter((item) => !item.complete);
  printDoctorLine(
    "incomplete",
    String(incomplete.length),
    incomplete.length > 0
      ? `missing a Rationale, so not applicable to any decision: ${incomplete
        .map((item) => item.name)
        .join(", ")}`
      : "every precedent states why, which is the part that transfers"
  );
}

function printFastPrePushSurface(repo) {
  process.stdout.write("\nFast pre-push surface:\n");
  const fastCheck = readFastCheck(repo);
  printDoctorLine(
    "fast_check",
    fastCheck ? "ok" : "none",
    fastCheck
      ? `declared in keel/config.yaml: ${fastCheck}`
      : "undeclared; add a fast_check line to keel/config.yaml"
  );
  const hookPresent = fs.existsSync(path.join(repo, ".githooks", "pre-push"));
  printDoctorLine(
    "pre-push hook",
    hookPresent ? "ok" : "none",
    hookPresent
      ? ".githooks/pre-push present"
      : "run keel --install --with-git-hooks to scaffold it"
  );
  const hooksPath = gitConfigHooksPath(repo);
  printDoctorLine(
    "core.hooksPath",
    hooksPath === ".githooks" ? "ok" : hooksPath ? "other" : "unset",
    hooksPath || "default (.git/hooks)"
  );
}

const SHIPPED_LENS_DIR = path.join(PACKAGE_ROOT, "assets", "lenses");
const EXPECTED_LENS_TEMPLATES = ["web", "hardware", "hardware-dsl"];

function targetSkillsDir(repo, target) {
  if (target === "codex") return path.join(repo, ".agents", "skills");
  if (target === "opencode") return path.join(repo, ".opencode", "skills");
  return path.join(repo, ".claude", "skills");
}

function legacyProfileSkills(repo, target) {
  try {
    return fs
      .readdirSync(targetSkillsDir(repo, target), { withFileTypes: true })
      .filter(
        (entry) => entry.isDirectory() && /^keel-profile-/.test(entry.name)
      )
      .map((entry) => entry.name)
      .sort();
  } catch (error) {
    return [];
  }
}

function printLensSurface(repo, target) {
  process.stdout.write("\nDomain lens surface:\n");
  const shipped = lensNames(SHIPPED_LENS_DIR);
  const missing = EXPECTED_LENS_TEMPLATES.filter(
    (name) => !shipped.includes(name)
  );
  printDoctorLine(
    "lens templates",
    missing.length === 0 ? "ok" : "incomplete",
    missing.length === 0
      ? `shipped: ${EXPECTED_LENS_TEMPLATES.join(", ")}; scaffold with keel lenses add`
      : `missing template(s): ${missing.join(", ")}`
  );
  const installed = lensNames(path.join(repo, "keel", "lenses"));
  printDoctorLine(
    "installed lenses",
    installed.length > 0 ? "ok" : "none",
    installed.length > 0
      ? `keel/lenses/: ${installed.join(", ")}`
      : "no user lenses yet; keel lenses add scaffolds one"
  );
  const legacy = legacyProfileSkills(repo, target);
  if (legacy.length > 0) {
    printDoctorLine(
      "legacy profiles",
      "migrate",
      `found ${legacy.join(", ")}; v3 keel-profile-* skills are replaced by `
        + "pluggable lenses (keel lenses add). Left untouched; not active state."
    );
  }
}

function lensNames(dir) {
  try {
    return fs
      .readdirSync(dir)
      .filter((name) => name.endsWith(".md"))
      .map((name) => name.slice(0, -3))
      .sort();
  } catch (error) {
    return [];
  }
}

function runLensesList(repo) {
  const shipped = lensNames(SHIPPED_LENS_DIR);
  const installed = lensNames(path.join(repo, "keel", "lenses"));
  process.stdout.write("Shipped lens templates (assets/lenses/):\n");
  if (shipped.length === 0) {
    process.stdout.write("  (none)\n");
  } else {
    for (const name of shipped) {
      const mark = installed.includes(name) ? " (installed)" : "";
      process.stdout.write(`  ${name}${mark}\n`);
    }
  }
  process.stdout.write("\nInstalled lenses (keel/lenses/):\n");
  if (installed.length === 0) {
    process.stdout.write("  (none) — run keel lenses add <name>\n");
  } else {
    for (const name of installed) {
      const mark = shipped.includes(name) ? "" : " (custom)";
      process.stdout.write(`  ${name}${mark}\n`);
    }
  }
  return 0;
}

function runLensesAdd(repo, name, force) {
  const source = path.join(SHIPPED_LENS_DIR, `${name}.md`);
  if (!fs.existsSync(source)) {
    const available = lensNames(SHIPPED_LENS_DIR).join(", ") || "(none)";
    fail(`unknown lens template: ${name}; shipped templates: ${available}`);
  }
  const destDir = path.join(repo, "keel", "lenses");
  const dest = path.join(destDir, `${name}.md`);
  if (fs.existsSync(dest) && !force) {
    process.stderr.write(
      `keel: keel/lenses/${name}.md already exists; pass --force to overwrite\n`
    );
    return 3;
  }
  fs.mkdirSync(destDir, { recursive: true });
  fs.copyFileSync(source, dest);
  process.stdout.write(
    `keel: wrote keel/lenses/${name}.md from the ${name} template; `
      + "edit it to fit this repository\n"
  );
  return 0;
}

function runAction(options) {
  if (options.updateSource !== null && options.action !== "update") {
    fail("--source only applies to --update");
  }
  if (options.withGitHooks && options.action !== "install") {
    fail("--with-git-hooks only applies to --install");
  }
  if (options.adopt && options.action !== "update") {
    fail("--adopt only applies to --update");
  }

  if (options.action === "openspec") {
    const openspec = findOpenSpecCommand();
    if (!openspec) {
      process.stderr.write(
        `keel: openspec is not resolvable; ${unresolvedOpenSpecAdvice()}\n`
      );
      return 1;
    }
    const archiving = options.openspecArgs[0] === "archive" ? archiveTracking(process.cwd(), options.openspecArgs) : null;
    const status = OPENSPEC_GENERATING_COMMANDS.has(options.openspecArgs[0])
      ? withSkillsDelivery((env) => runCommand(openspec, options.openspecArgs, { stdio: "inherit", env }))
      : runCommand(openspec, options.openspecArgs, { stdio: "inherit" });
    if (status === 0 && archiving) keepArchivedTracked(process.cwd(), archiving);
    if (status !== 0 || options.openspecArgs[0] !== "update") return status;
    const repo = process.cwd();
    for (const target of installedOpenSpecTargets(repo)) {
      process.stdout.write(`keel: restoring ${target} OpenSpec overlays after update\n`);
      const result = refreshOpenSpecSurfaceOverlay(repo, target);
      if (result.status !== 0) return result.status;
    }
    return status;
  }

  if (options.action === "context") {
    if (options.dryRun || options.forceTemplateUpdate || options.updateSource) {
      fail("context does not accept install or update options");
    }
    if (options.task && !options.change) {
      fail("context requires --change when --task is provided");
    }
    const repo = path.resolve(options.repo || process.cwd());
    let result;
    try {
      if (options.clearHandoff) {
        fs.rmSync(path.join(repo, "keel", "HANDOFF.md"), { force: true });
      }
      result = resolveContext(repo, options);
    } catch (error) {
      process.stderr.write(`keel: context input error: ${error.message}\n`);
      return 1;
    }
    process.stdout.write(
      options.json ? `${JSON.stringify(result, null, 2)}\n` : renderContext(result)
    );
    return 0;
  }

  if (options.action === "gate") {
    if (!options.gateStage) {
      fail("gate requires task-start, task-complete, or change-close");
    }
    if (options.dryRun || options.forceTemplateUpdate || options.updateSource) {
      fail("gate does not accept install or update options");
    }
    if (options.task && !options.change) {
      fail("gate requires --change when --task is provided");
    }
    const repo = path.resolve(options.repo || process.cwd());
    let result;
    try {
      result = runGate(repo, options.gateStage, options);
    } catch (error) {
      if (error instanceof GateInputError) {
        process.stderr.write(`keel: gate input error: ${error.message}\n`);
        return 1;
      }
      throw error;
    }
    process.stdout.write(
      options.json ? `${JSON.stringify(result, null, 2)}\n` : renderGate(result)
    );
    if (result.status === "pass") return 0;
    if (result.status === "needs-review") return 4;
    return 3;
  }

  if (options.action === "guard") {
    if (!["start", "status", "clear"].includes(options.guardSubcommand || "")) {
      fail("guard requires start, status, or clear");
    }
    if (options.dryRun || options.forceTemplateUpdate || options.updateSource) {
      fail("guard does not accept install or update options");
    }
    const repo = path.resolve(options.repo || process.cwd());
    let result;
    try {
      if (options.guardSubcommand === "start") {
        result = startGuard(repo, options);
      } else if (options.guardSubcommand === "status") {
        result = guardStatus(repo);
      } else {
        result = clearGuard(repo);
      }
    } catch (error) {
      if (error instanceof GuardInputError) {
        process.stderr.write(`keel: guard input error: ${error.message}\n`);
        return 1;
      }
      throw error;
    }
    process.stdout.write(
      options.json ? `${JSON.stringify(result, null, 2)}\n` : renderGuard(result)
    );
    return ["started", "active", "absent", "cleared", "archived"].includes(result.status)
      ? 0
      : 3;
  }

  if (options.action === "triage") {
    const repo = path.resolve(options.repo || process.cwd());
    const labels = String(options.labels || "")
      .split(",")
      .map((label) => label.trim())
      .filter(Boolean);
    const verdict = triageIssue(repo, labels, options.issue);
    const payload = {
      schemaVersion: 1,
      command: "triage",
      ...verdict,
      warnings: [
        "Admission starts work and authorizes nothing after it; every gate, "
          + "evidence requirement, Review, and the write guard still apply.",
        "An unattended run may open a pull request and may not merge one.",
        "Keel schedules nothing; the loop belongs to the host runtime.",
      ],
    };
    if (options.json) {
      process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
    } else {
      process.stdout.write(`Triage: ${verdict.status}\n${verdict.reason}\n`);
    }
    return 0;
  }
  if (options.action === "lenses") {
    if (options.dryRun || options.forceTemplateUpdate || options.updateSource) {
      fail("lenses does not accept install or update options");
    }
    const repo = path.resolve(options.repo || process.cwd());
    if (options.lensesSubcommand === "list") {
      return runLensesList(repo);
    }
    return runLensesAdd(repo, options.lensName, options.force);
  }

  if (options.action === "capabilities") {
    if (options.dryRun || options.forceTemplateUpdate || options.updateSource) {
      fail("capabilities does not accept install or update options");
    }
    const repo = path.resolve(options.repo || process.cwd());
    const result = probeCapabilities(repo, options.target);
    process.stdout.write(
      options.json
        ? `${JSON.stringify(result, null, 2)}\n`
        : renderCapabilities(result)
    );
    return 0;
  }

  if (options.action === "project") {
    if (options.dryRun || options.forceTemplateUpdate || options.updateSource) {
      fail("project does not accept install or update options");
    }
    if (options.task && !options.change) {
      fail("project requires --change when --task is provided");
    }
    const repo = path.resolve(options.repo || process.cwd());
    let result;
    try {
      result = projectRuntime(repo, options);
    } catch (error) {
      process.stderr.write(`keel: projection input error: ${error.message}\n`);
      return 1;
    }
    process.stdout.write(
      options.json
        ? `${JSON.stringify(result, null, 2)}\n`
        : renderProjection(result)
    );
    return 0;
  }

  if (options.action === "init") {
    return runProjectInit(options);
  }

  if (options.action === "install") {
    const installStatus = runPython(INSTALL_SCRIPT, installerArgs(options));
    if (installStatus !== 0) {
      return installStatus;
    }
    return refreshInstalledTargetOverlays(
      path.resolve(options.repo || process.cwd()),
      options.target,
      { dryRun: options.dryRun }
    ).status;
  }

  if (options.action === "update") {
    return runGlobalUpdate(options);
  }

  if (options.action === "clear" || options.action === "uninstall") {
    const uninstallStatus = runPython(
      INSTALL_SCRIPT,
      installerArgs(options, ["--uninstall"])
    );
    if (uninstallStatus !== 0) {
      return uninstallStatus;
    }
    return removeOpenSpecSurfaceOverlay(
      path.resolve(options.repo || process.cwd()),
      options.target,
      { dryRun: options.dryRun }
    ).status;
  }

  if (options.action === "check") {
    if (options.dryRun || options.forceTemplateUpdate) {
      fail("--check does not accept --dry-run or --force-template-update");
    }
    const checkStatus = runPython(
      INSTALL_SCRIPT,
      installerArgs(options, ["--check"])
    );
    if (checkStatus !== 0) {
      return checkStatus;
    }
    process.stdout.write("\nDry-run install plan:\n");
    const planStatus = runPython(
      INSTALL_SCRIPT,
      installerArgs({ ...options, dryRun: true })
    );
    if (planStatus !== 0) {
      return planStatus;
    }
    // The overlay refresh is a Node-side step the installer's plan never sees,
    // so without this `--check` reports an empty plan for a run that writes.
    return refreshInstalledTargetOverlays(
      path.resolve(options.repo || process.cwd()),
      options.target,
      { dryRun: true }
    ).status;
  }

  if (options.action === "doctor") {
    return runDoctor(options);
  }

  fail("missing action");
}

function main() {
  // `keel mail` parses its own arguments: it is host-neutral messaging between
  // sessions (#180), sharing no option with the gate and projection commands.
  if (process.argv[2] === "mail") {
    return require("../src/core/mail").runMail(process.argv.slice(3));
  }
  // `keel chat` likewise: the group chat between sessions (#187).
  if (process.argv[2] === "chat") {
    return require("../src/core/chat/cli").runChat(process.argv.slice(3));
  }
  // `keel shift` likewise: a coordinated shift change for a role's session.
  if (process.argv[2] === "shift") {
    return require("../src/core/shift").runShift(process.argv.slice(3));
  }
  if (process.argv[2] === "lock") {
    return require("../src/core/lock").runLock(process.argv.slice(3));
  }
  if (process.argv[2] === "patrol") {
    return require("../src/core/patrol").runPatrol(process.argv.slice(3));
  }
  // `keel tick` likewise: the model-free step a host scheduler calls (#356).
  if (process.argv[2] === "tick") {
    return require("../src/core/tick").runTick(process.argv.slice(3));
  }
  if (process.argv[2] === "worktrees") {
    return require("../src/core/worktrees").runWorktrees(process.argv.slice(3));
  }
  // `keel agents` likewise: the external model CLI catalog (#219).
  if (process.argv[2] === "agents") {
    return require("../src/core/agents").runAgents(process.argv.slice(3));
  }
  // `keel branches` likewise: a role's merged task branches (#469).
  if (process.argv[2] === "branches") {
    return require("../src/core/branches").runBranches(process.argv.slice(3));
  }
  // `keel docx` was Markdown with SVG to Word (#405). It is retired (#464 D3),
  // and the word stays known so a caller learns where the export went.
  if (process.argv[2] === "docx") {
    process.stderr.write("keel docx was retired in 5.202.0: Markdown-to-Word export is not part of Keel. Use a general document tool.\n");
    return 2;
  }
  const options = parseArgs(process.argv.slice(2));
  if (options.adopt && options.action !== "update") {
    fail("--adopt only applies to --update");
  }
  if (options.help || (!options.action && !options.version)) {
    printHelp();
    return 0;
  }
  if (options.version) {
    printVersion();
    return 0;
  }
  return runAction(options);
}

// Not `process.exit()`: stdout to a pipe is asynchronous, and exiting discards
// whatever the operating system has not yet accepted. Nothing is lost while the
// payload fits the pipe buffer, which is why this was invisible at the 64KB
// default — and under the memory pressure that shrinks buffers to a page or
// two, a consumer receives a valid prefix of an incomplete document with no
// error and no change of exit code. Setting the code instead lets the event
// loop drain the write and end the process on its own.
process.exitCode = main();
