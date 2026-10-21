"use strict";

// `keel docx`: Markdown with embedded SVG to Word, on request (#405).
//
// The converter ships with the `keel-md-docx` skill; its third-party packages
// do not. `setup` lists them and installs nothing until it is given `--yes`,
// which the skill asks the user for first, and then installs only into the
// environment Keel manages under `$KEEL_HOME/docx/` — a Python virtual
// environment and an npm prefix, never the system's.

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");
const { resolveInterpreter, describeTried, MINIMUM_PYTHON } = require("../../scripts/run_python");
const PACKAGE_JSON = require("../../package.json");

const SKILL_SCRIPTS = path.join(__dirname, "..", "..", "plugins", "keel", "skills", "keel-md-docx", "scripts");

// What setup installs, as the registries listed it on 2026-10-21 for macOS
// arm64 (#405); the versions that install are the ones requirements.txt and
// package.json pin.
const PACKAGES = [
  { name: "python-docx", via: "pip", version: ">=1.1,<2 (1.2.0)", licence: "MIT", size: "0.25 MB" },
  { name: "lxml", via: "pip", version: ">=5,<7 (6.0.2)", licence: "BSD-3-Clause", size: "8.6 MB" },
  { name: "Pillow", via: "pip", version: ">=10,<13 (12.0.0)", licence: "MIT-CMU", size: "4.65 MB" },
  { name: "marked", via: "npm", version: "17.0.5", licence: "MIT", size: "0.44 MB" },
  {
    name: "sharp",
    via: "npm",
    version: "0.35.5",
    licence: "Apache-2.0",
    size: "0.96 MB, plus its platform binary (Apache-2.0) and libvips (LGPL-3.0-or-later, 18.2 MB)",
  },
];

const USAGE = [
  "Usage:",
  "  keel docx setup [--yes]   list what the export needs; install it into the Keel-managed environment with --yes",
].join("\n");

function docxHome() {
  return path.join(process.env.KEEL_HOME || path.join(os.homedir(), ".keel"), "docx");
}

function environmentPython(home) {
  return process.platform === "win32"
    ? path.join(home, "python", "Scripts", "python.exe")
    : path.join(home, "python", "bin", "python");
}

function npmCommand() {
  return process.env.KEEL_DOCX_NPM || (process.platform === "win32" ? "npm.cmd" : "npm");
}

function printPlan(home) {
  const lines = [
    `keel docx: Markdown with SVG to Word needs these packages, installed into ${home}:`,
    ...PACKAGES.map((item) => `  ${item.name} ${item.version} (${item.via}) — ${item.licence} — ${item.size}`),
    `  Python ${MINIMUM_PYTHON.join(".")} or newer runs a virtual environment in ${path.join(home, "python")};`,
    `  npm installs into ${path.join(home, "node")}. Nothing goes into the system Python or Node,`,
    "  and no font or runtime is downloaded. Sizes are registry figures, not measured installs.",
  ];
  process.stdout.write(`${lines.join("\n")}\n`);
}

function step(name, command, args) {
  const result = spawnSync(command, args, {
    stdio: "inherit",
    shell: process.platform === "win32",
  });
  if (result.error || result.status !== 0) {
    const why = result.error ? result.error.message : `exited ${result.status}`;
    process.stderr.write(`keel docx setup: ${name} failed (${why}); the environment is not ready.\n`);
    return false;
  }
  return true;
}

function setup(argv) {
  let yes = false;
  for (const arg of argv) {
    if (arg === "--yes") yes = true;
    else {
      process.stderr.write(`keel docx setup: unexpected argument ${arg}\n${USAGE}\n`);
      return 2;
    }
  }
  const home = docxHome();
  const ready = path.join(home, "ready.json");
  printPlan(home);
  if (!yes) {
    const state = fs.existsSync(ready) ? "The environment is ready." : "Nothing was installed.";
    process.stdout.write(`${state} To install or reinstall, run \`keel docx setup --yes\`.\n`);
    return 0;
  }

  const { candidate, version, tried } = resolveInterpreter();
  if (!candidate) {
    process.stderr.write(
      `keel docx setup: Python ${MINIMUM_PYTHON.join(".")} or newer is required. `
        + `Tried ${describeTried(tried) || "nothing"}. Install one, or set KEEL_PYTHON.\n`
    );
    return 1;
  }
  // Written last, so an interrupted setup reads as not set up.
  fs.rmSync(ready, { force: true });
  fs.mkdirSync(path.join(home, "node"), { recursive: true });
  fs.copyFileSync(path.join(SKILL_SCRIPTS, "package.json"), path.join(home, "node", "package.json"));
  const ok = step("python -m venv", candidate.command, [...candidate.prefixArgs, "-m", "venv", path.join(home, "python")])
    && step("pip install", environmentPython(home), ["-m", "pip", "install", "-r", path.join(SKILL_SCRIPTS, "requirements.txt")])
    && step("npm install", npmCommand(), ["install", "--prefix", path.join(home, "node"), "--no-audit", "--no-fund"]);
  if (!ok) return 1;
  fs.writeFileSync(ready, `${JSON.stringify({
    keel: PACKAGE_JSON.version,
    python: version,
    packages: PACKAGES.map((item) => `${item.name} ${item.version}`),
  }, null, 2)}\n`);
  process.stdout.write(`keel docx: the environment in ${home} is ready.\n`);
  return 0;
}

function runDocx(argv) {
  const [sub, ...rest] = argv;
  if (sub === undefined || sub === "--help" || sub === "-h" || sub === "help") {
    process.stdout.write(`${USAGE}\n`);
    return sub === undefined ? 2 : 0;
  }
  if (sub === "setup") return setup(rest);
  process.stderr.write(`keel docx: unknown subcommand ${sub}\n${USAGE}\n`);
  return 2;
}

module.exports = { runDocx, docxHome, PACKAGES, SKILL_SCRIPTS };
