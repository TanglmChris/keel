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
  probeCapabilities,
  renderCapabilities,
} = require("../src/core/capabilities");
const {
  projectRuntime,
  renderProjection,
} = require("../src/core/projection");
const {
  compileGoalProjection,
  renderGoalProjection,
} = require("../src/core/goal");
const {
  compileHelperBrief,
  captureHelperBaseline,
  verifyHelperEvidence,
  renderHelper,
} = require("../src/core/helper");
const {
  compileTasksView,
  renderTasksView,
} = require("../src/core/tasksview");
const {
  GuardInputError,
  clearGuard,
  guardStatus,
  renderGuard,
  startGuard,
} = require("../src/core/guard");

const PACKAGE_ROOT = path.resolve(__dirname, "..");
const PACKAGE_JSON = require(path.join(PACKAGE_ROOT, "package.json"));
const INSTALL_SCRIPT = path.join(PACKAGE_ROOT, "scripts", "install_to_repo.py");
const DEFAULT_UPDATE_SOURCE = "github:TanglmChris/keel";
const VALID_TARGETS = new Set(["claude", "codex", "opencode", "both"]);
const KEEL_SKILLS = [
  "keel-align-expectations",
  "keel-debug-failure",
  "keel-handoff",
  "keel-review-checklist",
  "keel-tdd-or-test-first",
];
const OPENSPEC_COMMAND_IDS = ["propose", "explore", "apply", "sync", "archive"];
const OPENSPEC_SKILLS = [
  "openspec-propose",
  "openspec-explore",
  "openspec-apply-change",
  "openspec-sync-specs",
  "openspec-archive-change",
];
const OPENSPEC_OVERLAY_ACTIONS = ["propose", "apply", "archive"];
const OPENSPEC_SURFACE_OVERLAY_START =
  `<!-- keel:openspec-surface-overlay version=${PACKAGE_JSON.version} -->`;
const OPENSPEC_SURFACE_OVERLAY_END =
  "<!-- keel:openspec-surface-overlay:end -->";
const OPENSPEC_SURFACE_OVERLAY_RE =
  /<!--\s*keel:openspec-surface-overlay(?:\s+[^>]*)?\s*-->[\s\S]*?<!--\s*keel:openspec-surface-overlay:end\s*-->/;

const HELP = `keel ${PACKAGE_JSON.version}

Usage:
  keel context [repo] [--change name] [--task id] [--json] [--clear-handoff]
  keel capabilities [repo] [--target claude|codex|opencode] [--json]
  keel project [repo] --target claude|codex|opencode --event startup|resume|compaction|goal|task-view|worktree|subagent-start|subagent-stop [--authorize goal|task-view|subagent] [--expected-owner owner] [--native-complete] [--change name] [--task id] [--json]
  keel project tasks [repo] --target claude [--change name] [--json]
  keel gate task-start|task-complete|change-close [repo] [--change name] [--task id] [--action sync|archive] [--base git-ref] [--no-guard] [--record] [--json]
  keel guard start|status|clear [repo] [--change name] [--task id] [--force] [--json]
  keel lenses list|add [name] [repo] [--force]
  keel openspec [args...]
  keel --init [repo] [--target claude|codex|opencode] [--dry-run] [--force-template-update]
  keel --install [repo] [--target claude|codex|opencode] [--dry-run] [--force-template-update]
  keel --clear [repo] [--target claude|codex|opencode] [--dry-run]
  keel --uninstall [repo] [--target claude|codex|opencode] [--dry-run]
  keel --update [--dry-run] [--source npm-package-or-git-spec]
  keel --check [repo] [--target claude|codex|opencode]
  keel --doctor [repo] [--target claude|codex|opencode]
  keel --version
  keel --help

Defaults:
  repo defaults to the current working directory.
  target defaults to claude.
  --update refreshes the global keel CLI, not project protocol files.
  update source defaults to ${DEFAULT_UPDATE_SOURCE}.

Project layout:
  continuity is recomputed from OpenSpec on every invocation.
  keel/HANDOFF.md is an optional keel-handoff/v1 pointer override.
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
  keel --init
  keel --install
  keel --install --target codex
  keel --install --target opencode
  keel --install --dry-run
  keel --check
  keel --doctor
  keel --install --force-template-update
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
    updateSource: null,
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
    guardSubcommand: null,
    lensesSubcommand: null,
    lensName: null,
    openspecArgs: [],
    force: false,
    projectionEvent: null,
    authorizations: [],
    expectedOwner: null,
    nativeComplete: false,
    projectSubcommand: null,
    expectedFingerprint: null,
    helperQuestion: null,
    helperCommand: null,
    helperReads: [],
    helperExternal: [],
    helperVerify: false,
    helperCaptureBaseline: false,
    helperBaseline: null,
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
    if (arg === "--event" || arg === "--authorize" || arg === "--expected-owner") {
      index += 1;
      if (index >= argv.length) {
        fail(`${arg} requires a value`);
      }
      if (arg === "--authorize") {
        if (!parsed.authorizations.includes(argv[index])) {
          parsed.authorizations.push(argv[index]);
        }
      } else {
        const key = arg === "--event" ? "projectionEvent" : "expectedOwner";
        if (parsed[key] !== null) fail(`${arg} was provided more than once`);
        parsed[key] = argv[index];
      }
      continue;
    }
    if (arg === "--native-complete") {
      parsed.nativeComplete = true;
      continue;
    }
    if (arg === "--expected-fingerprint") {
      index += 1;
      if (index >= argv.length) {
        fail("--expected-fingerprint requires a value");
      }
      if (parsed.expectedFingerprint !== null) {
        fail("--expected-fingerprint was provided more than once");
      }
      parsed.expectedFingerprint = argv[index];
      continue;
    }
    if (arg === "--brief" || arg === "--command" || arg === "--baseline") {
      index += 1;
      if (index >= argv.length) {
        fail(`${arg} requires a value`);
      }
      const key =
        arg === "--brief"
          ? "helperQuestion"
          : arg === "--command"
            ? "helperCommand"
            : "helperBaseline";
      if (parsed[key] !== null) {
        fail(`${arg} was provided more than once`);
      }
      parsed[key] = argv[index];
      continue;
    }
    if (arg === "--read" || arg === "--external") {
      index += 1;
      if (index >= argv.length) {
        fail(`${arg} requires a value`);
      }
      const key = arg === "--read" ? "helperReads" : "helperExternal";
      parsed[key].push(argv[index]);
      continue;
    }
    if (arg === "--verify") {
      parsed.helperVerify = true;
      continue;
    }
    if (arg === "--capture-baseline") {
      parsed.helperCaptureBaseline = true;
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
          + "guidance is bundled with the keel-align-expectations skill as "
          + "on-demand references"
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
    !["context", "gate", "capabilities", "project", "guard"].includes(
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
      || parsed.authorizations.length > 0
      || parsed.expectedOwner !== null
      || parsed.nativeComplete
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
      || parsed.authorizations.length > 0
      || parsed.expectedOwner !== null
      || parsed.nativeComplete
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
  if (parsed.noGuard && parsed.action !== "gate") {
    fail("--no-guard applies only to keel gate task-start");
  }
  if (parsed.record && parsed.action !== "gate") {
    fail("--record applies only to keel gate task-start");
  }
  if (parsed.projectSubcommand !== "goal" && parsed.expectedFingerprint !== null) {
    fail("--expected-fingerprint applies only to keel project goal");
  }
  if (parsed.action === "project" && parsed.projectSubcommand !== null) {
    if (!["goal", "helper", "tasks"].includes(parsed.projectSubcommand)) {
      fail(
        `unknown project subcommand: ${parsed.projectSubcommand}; `
          + "only keel project goal, keel project helper, and keel project "
          + "tasks are supported"
      );
    }
    if (
      parsed.projectionEvent !== null
      || parsed.authorizations.length > 0
      || parsed.nativeComplete
    ) {
      fail(
        "keel project goal/helper/tasks do not take --event, --authorize, or "
          + "--native-complete; those apply only to keel project without a "
          + "subcommand"
      );
    }
    if (parsed.projectSubcommand === "tasks" && parsed.task !== null) {
      fail(
        "keel project tasks projects a whole change checklist; "
          + "--task is not supported"
      );
    }
  }
  const helperFlagsUsed =
    parsed.helperQuestion !== null
    || parsed.helperCommand !== null
    || parsed.helperReads.length > 0
    || parsed.helperExternal.length > 0
    || parsed.helperVerify
    || parsed.helperCaptureBaseline
    || parsed.helperBaseline !== null;
  if (helperFlagsUsed && parsed.projectSubcommand !== "helper") {
    fail(
      "--brief, --command, --read, --external, --verify, --capture-baseline, "
        + "and --baseline apply only to keel project helper"
    );
  }

  return parsed;
}

function pythonCandidates() {
  if (process.env.KEEL_PYTHON) {
    return [{ command: process.env.KEEL_PYTHON, prefixArgs: [] }];
  }

  const candidates = [];
  if (process.platform === "win32") {
    candidates.push({ command: "py", prefixArgs: ["-3"] });
    candidates.push({ command: "python", prefixArgs: [] });
    candidates.push({ command: "python3", prefixArgs: [] });
  } else {
    candidates.push({ command: "python3", prefixArgs: [] });
    candidates.push({ command: "python", prefixArgs: [] });
  }
  return candidates;
}

function commandExists(candidate) {
  const result = spawnSync(
    candidate.command,
    [...candidate.prefixArgs, "--version"],
    { encoding: "utf8" }
  );
  return !result.error && result.status === 0;
}

function npmCommand() {
  return process.platform === "win32" ? "npm.cmd" : "npm";
}

function openspecCandidates() {
  const localBin = path.join(
    PACKAGE_ROOT,
    "node_modules",
    ".bin",
    process.platform === "win32" ? "openspec.cmd" : "openspec"
  );
  const candidates = [];
  if (fs.existsSync(localBin)) {
    candidates.push(localBin);
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
  const npm = npmCommand();

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
    return 0;
  }

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
    if (packResult.error) {
      process.stderr.write(
        `keel: failed to run npm pack: ${packResult.error.message}\n`
      );
      return 1;
    }
    if (packResult.status !== 0) {
      return typeof packResult.status === "number" ? packResult.status : 1;
    }

    const tarball = findPackedTarball(packResult.stdout, tempDir);
    const installResult = spawnSync(npm, ["install", "-g", tarball], {
      stdio: "inherit",
      shell: process.platform === "win32",
    });
    if (installResult.error) {
      process.stderr.write(
        `keel: failed to run npm install: ${installResult.error.message}\n`
      );
      return 1;
    }
    return typeof installResult.status === "number" ? installResult.status : 1;
  } catch (error) {
    process.stderr.write(`keel: update failed: ${error.message}\n`);
    return 1;
  } finally {
    fs.rmSync(tempDir, { recursive: true, force: true });
  }
}

function runPython(script, args) {
  if (!fs.existsSync(script)) {
    process.stderr.write(`keel: missing packaged script: ${script}\n`);
    return 1;
  }

  for (const candidate of pythonCandidates()) {
    if (!commandExists(candidate)) {
      continue;
    }
    const result = spawnSync(
      candidate.command,
      [...candidate.prefixArgs, script, ...args],
      { stdio: "inherit" }
    );
    return typeof result.status === "number" ? result.status : 1;
  }

  process.stderr.write(
    "keel: Python 3 is required. Install python3/python, or set KEEL_PYTHON.\n"
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
  return args;
}

function openspecToolsForTarget(target) {
  return target;
}

function runOpenSpec(args, repo, options) {
  const command = options.dryRun ? "openspec" : findOpenSpecCommand();
  if (!command) {
    process.stderr.write(
      "keel: OpenSpec CLI is provided by Keel's npm dependencies but was not found. Reinstall keel so npm installs its dependencies.\n"
    );
    return 1;
  }
  return runCommand(command, args, {
    cwd: repo,
    dryRun: options.dryRun,
  });
}

function runProjectInit(options) {
  if (options.updateSource !== null) {
    fail("--source only applies to --update");
  }

  const repo = path.resolve(options.repo || process.cwd());
  if (!options.dryRun) {
    fs.mkdirSync(repo, { recursive: true });
  }

  const openspecTools = openspecToolsForTarget(options.target);
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
    return refreshOpenSpecSurfaceOverlay(repo, options.target, {
      dryRun: options.dryRun,
    }).status;
  }

  return 0;
}

function printDoctorLine(name, status, detail = "") {
  process.stdout.write(`${name}: ${status}${detail ? ` - ${detail}` : ""}\n`);
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

function openspecSkillRootForTarget(target) {
  if (target === "claude") return path.join(".claude", "skills");
  if (target === "codex") return path.join(".codex", "skills");
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
      remediation: "run keel --init --target claude or openspec update --force",
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
    remediation: "run keel --init --target opencode or openspec update --force",
  };
}

function commandPathForAction(target, repo, action) {
  if (target === "claude") {
    return path.join(repo, ".claude", "commands", "opsx", `${action}.md`);
  }
  if (target === "codex") {
    return path.join(codexHome(), "prompts", `opsx-${action}.md`);
  }
  return path.join(repo, ".opencode", "commands", `opsx-${action}.md`);
}

function openspecOverlaySurfacesForTarget(target, repo) {
  const skillRoot = openspecSkillRootForTarget(target);
  return OPENSPEC_OVERLAY_ACTIONS.flatMap((action) => {
    if (action === "propose" && target === "opencode") {
      return [];
    }
    const skillName =
      action === "propose"
        ? "openspec-propose"
        : action === "apply"
          ? "openspec-apply-change"
          : "openspec-archive-change";
    return [
      {
        action,
        path: path.join(repo, skillRoot, skillName, "SKILL.md"),
      },
      {
        action,
        path: commandPathForAction(target, repo, action),
      },
    ];
  });
}

function overlayTitleForAction(action) {
  if (action === "propose") return "Keel Authoring Overlay";
  return action === "apply"
    ? "Keel Apply Overlay"
    : "Keel Archive Overlay";
}

function keelOpenSpecOverlay(action) {
  if (action === "propose") {
    const lines = [
      OPENSPEC_SURFACE_OVERLAY_START,
      "## Keel Authoring Overlay",
      "",
      "Keel rules below take precedence over conflicting generic OpenSpec instructions in this file.",
      "",
      "### Expectation alignment before specs and tasks finalize",
      "",
      "- Before specs and executable tasks are finalized, run `keel-align-expectations`: quick path for complete low-risk requests, deep path when a material choice can change user-visible behavior, an external interface, acceptance, security/privacy/permission boundaries, data migration, protocol/state/timing/reset semantics, generated equivalence, irreversible cost, or a dependency commitment.",
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
  const actionBody =
    action === "apply"
      ? [
          "- The current agent remains the Keel task owner and selects one unchecked task or a small contiguous task group from `tasks.md`.",
          "- Run the Task Authoring Gate: each relevant critical expectation must be covered by a slice, deferred to a durable owner, or explicitly discarded.",
          "- Run the Slice Start Gate: selected current slices must name source expectations and include Read, Touch, Acceptance, Commands, and Stop/Autonomy boundaries before implementation.",
          "- Rough future slices may remain drafts, but cannot be selected for implementation or marked complete.",
          "- Obey the selected task contract: Read is required starting context, Touch is the write boundary, Commands prove Acceptance, and the Autonomy boundary controls fallback decisions.",
          "- Target-native subagents return report/evidence only; they cannot mark tasks complete, update OpenSpec state, commit, sync, archive, or change Acceptance.",
          "- The current agent reviews all subagent output, command evidence, and diffs before marking any task complete.",
          "- When implementation exposes a material expectation, acceptance boundary, or user-owned decision absent from durable authority, stop before implementing that choice, rerun `keel-align-expectations`, and reauthor the affected proposal/design/spec/task authority first.",
          "- A discovered repository fact that does not change accepted behavior or scope may be recorded and execution continues inside the existing task boundary without a product interview.",
          "- Invoke OpenSpec through `keel openspec` (for example `keel openspec validate`); a bare `openspec` command may not be on PATH.",
        ]
      : [
          "- The current agent owns final sync/archive decisions and must verify task evidence, follow-up ownership, and completion gates before proceeding.",
          "- Before final sync/archive, each related critical expectation must have behavior evidence, a durable follow-up owner, or an explicit discard reason.",
          "- Target-native subagents may help with bounded assessment or evidence production only; they cannot archive, sync, change acceptance, or bypass completion gates.",
          "- The current agent reviews any subagent report before running `openspec-sync-specs`, `/opsx:sync`, or `/opsx:archive`.",
          "- Do not treat generic OpenSpec archive delegation language as authority to transfer Keel ownership.",
          "- Invoke OpenSpec through `keel openspec` (for example `keel openspec validate`); a bare `openspec` command may not be on PATH.",
          "- When `/opsx:sync` has already promoted the change's spec delta, run the archive with `--skip-specs` so the promoted delta is not re-applied; archive is not idempotent over an already-synced delta.",
          "- After archiving, run `keel guard clear` to drop the change's guard manifest; the read-only gate never clears it for you.",
        ];

  const lines = [
    OPENSPEC_SURFACE_OVERLAY_START,
    `## ${overlayTitleForAction(action)}`,
    "",
    "Keel rules below take precedence over conflicting generic OpenSpec instructions in this file.",
    "",
    "### Target-native subagent gate",
    "",
    "- The current agent remains responsible for Keel ownership, task/archive decisions, scope control, and final reporting.",
    "- Use a target-native subagent only when the current agent decides it is useful for a bounded helper step.",
    "- Target-native subagents return report/evidence only; the current agent reviews the output before acting.",
    "- The subagent brief must name the selected change/task, required read context, allowed write boundary or read-only diagnostic scope, expected commands/evidence, and prohibited actions.",
    "- Prohibited actions include scope expansion, Acceptance changes, completion marking, sync/archive decisions, commits, handoff changes, and cross-runtime delegation unless the selected task or user explicitly authorizes them.",
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

function refreshOpenSpecSurfaceOverlay(repo, target, options = {}) {
  const surfaces = openspecOverlaySurfacesForTarget(target, repo);
  const counts = {
    refreshed: 0,
    current: 0,
    missing: 0,
  };

  if (options.dryRun) {
    for (const surface of surfaces) {
      process.stdout.write(
        `keel: would refresh OpenSpec ${surface.action} overlay in ${surface.path}\n`
      );
    }
    return { status: 0, ...counts };
  }

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
    fs.writeFileSync(surface.path, next, "utf8");
    counts.refreshed += 1;
  }

  if (counts.refreshed > 0 || counts.current > 0) {
    process.stdout.write(
      "keel: OpenSpec apply/archive overlay "
        + `refreshed=${counts.refreshed} current=${counts.current} `
        + `missing=${counts.missing}\n`
    );
  }

  return { status: 0, ...counts };
}

function hasCurrentOpenSpecOverlay(filePath) {
  if (!fs.existsSync(filePath)) {
    return false;
  }
  return fs
    .readFileSync(filePath, "utf8")
    .includes(OPENSPEC_SURFACE_OVERLAY_START);
}

function countOpenSpecOverlays(paths) {
  const current = paths.filter(hasCurrentOpenSpecOverlay);
  return { existing: current.length, total: paths.length };
}

function overlayRemediation(target) {
  return `run keel --init --target ${target} or keel --install --target ${target}`;
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
    printDoctorLine("native plugin source", sourceStatus, sourceDetail);
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
  }

  const openspecSkillRoot = openspecSkillRootForTarget(target);
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
    "keel-* skills are delivered by the installed Keel plugin (see native plugin status above); install the plugin if it is missing"
  );

  const commands = commandSurfaceForTarget(target, repo);
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

  const overlayPaths = openspecOverlaySurfacesForTarget(target, repo).map(
    (surface) => surface.path
  );
  const overlayCounts = countOpenSpecOverlays(overlayPaths);
  const overlayDetail =
    surfaceStatus(overlayCounts) === "ok"
      ? formatCount(overlayCounts, "apply/archive skills and commands")
      : `${formatCount(
          overlayCounts,
          "apply/archive skills and commands"
        )}; ${overlayRemediation(target)}`;
  printDoctorLine(
    "Keel apply/archive overlay",
    surfaceStatus(overlayCounts),
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

  const python = pythonCandidates().find(commandExists);
  printDoctorLine(
    "python3",
    python ? "ok" : "missing",
    python ? formatCommand(python.command, python.prefixArgs) : "set KEEL_PYTHON or install Python 3"
  );

  const openspec = findOpenSpecCommand();
  if (!openspec) {
    printDoctorLine(
      "openspec",
      "missing",
      "reinstall keel so npm installs its OpenSpec dependency"
    );
  } else {
    const bareOpenSpecOnPath =
      !path.isAbsolute(openspec)
      || runCommand("openspec", ["--version"], {
        stdio: "ignore",
        silentNotFound: true,
      }) === 0;
    printDoctorLine(
      "openspec",
      bareOpenSpecOnPath ? "ok" : "warning",
      bareOpenSpecOnPath
        ? openspec
        : `${openspec} is keel-resolvable but bare \`openspec\` is not on PATH — use \`keel openspec\``
    );
  }

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
  printLensSurface(repo, options.target);

  return checkStatus;
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

  if (options.action === "openspec") {
    const openspec = findOpenSpecCommand();
    if (!openspec) {
      process.stderr.write(
        "keel: openspec is not resolvable; reinstall keel so npm installs "
          + "its OpenSpec dependency\n"
      );
      return 1;
    }
    return runCommand(openspec, options.openspecArgs, { stdio: "inherit" });
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
    return ["started", "active", "absent", "cleared"].includes(result.status)
      ? 0
      : 3;
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
    if (options.projectSubcommand === "goal") {
      const result = compileGoalProjection(repo, options);
      process.stdout.write(
        options.json
          ? `${JSON.stringify(result, null, 2)}\n`
          : renderGoalProjection(result)
      );
      return result.status === "ready" ? 0 : 3;
    }
    if (options.projectSubcommand === "tasks") {
      const result = compileTasksView(repo, options);
      process.stdout.write(
        options.json
          ? `${JSON.stringify(result, null, 2)}\n`
          : renderTasksView(result)
      );
      return result.status === "ready" ? 0 : 3;
    }
    if (options.projectSubcommand === "helper") {
      let result;
      try {
        if (options.helperCaptureBaseline) {
          result = captureHelperBaseline(repo, options);
        } else if (options.helperVerify) {
          result = verifyHelperEvidence(repo, options);
        } else {
          result = compileHelperBrief(repo, options);
        }
      } catch (error) {
        process.stderr.write(`keel: helper input error: ${error.message}\n`);
        return 1;
      }
      process.stdout.write(
        options.json
          ? `${JSON.stringify(result, null, 2)}\n`
          : renderHelper(result)
      );
      const okStates = ["ready", "verified", "captured"];
      return okStates.includes(result.status) ? 0 : 3;
    }
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
    return refreshOpenSpecSurfaceOverlay(
      path.resolve(options.repo || process.cwd()),
      options.target,
      { dryRun: options.dryRun }
    ).status;
  }

  if (options.action === "update") {
    return runGlobalUpdate(options);
  }

  if (options.action === "clear" || options.action === "uninstall") {
    return runPython(INSTALL_SCRIPT, installerArgs(options, ["--uninstall"]));
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
    return runPython(INSTALL_SCRIPT, installerArgs({ ...options, dryRun: true }));
  }

  if (options.action === "doctor") {
    return runDoctor(options);
  }

  fail("missing action");
}

function main() {
  const options = parseArgs(process.argv.slice(2));
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

process.exit(main());
