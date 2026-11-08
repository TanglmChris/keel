"use strict";

// `keel feedback "<one sentence>"` (#505): drafts a fixed-structure issue for
// the Keel repository from inside any project, redacted before anything is
// shown, and lists near-duplicates. It creates nothing here; that is a later
// step under a declaration or a confirmation.

const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const PACKAGE_JSON = require("../../package.json");

// The target is Keel itself, read from the package's own repository URL: the
// command is feedback to Keel, and a flag would make it a general issue filer.
const KEEL_REPO = (() => {
  const url = typeof PACKAGE_JSON.repository === "string" ? PACKAGE_JSON.repository : PACKAGE_JSON.repository.url;
  const match = String(url).match(/github\.com[:/]([^/]+\/[^/.]+)(?:\.git)?$/);
  return match ? match[1] : "TanglmChris/keel";
})();

const USAGE = [
  "keel feedback \"<one sentence>\" [--command <cmd>] [--output-file <file>] [--expected <text>] [--repro <text>] [--impact <text>] [--host <name>] [--doctor] [--create [--confirmed]]",
  "  Draft an issue for the Keel repository: the version, the command and its output, redacted. Creates nothing without --create;",
  "  --create needs `issue:TanglmChris/keel` in this project's authorize: or --confirmed (the user approved this draft).",
].join("\n");

// Redaction runs on everything shown. The order matters: block and token
// shapes first, then the looser key=value form, then paths.
const RULES = [
  ["private-key", /-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)/g, "[private key]"],
  ["token", /\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|xox[abprs]-[A-Za-z0-9-]{10,}|xapp-[A-Za-z0-9-]{10,}|AKIA[0-9A-Z]{16})\b/g, "[token]"],
  ["token", /\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{5,}/g, "[token]"],
  ["token", /\bBearer\s+[A-Za-z0-9._~+/=-]{8,}/g, "Bearer [token]"],
  ["url-credential", /([A-Za-z][A-Za-z0-9+.-]*:\/\/)[^\s/:@]+:[^\s/@]+@/g, "$1[credential]@"],
  ["secret", /\b([A-Za-z0-9_.-]*(?:token|secret|password|passwd|api[_-]?key|private[_-]?key|access[_-]?key)[A-Za-z0-9_.-]*)([ \t]*[=:][ \t]*)(["']?)(?!\[)[^\s"']{4,}/gi, "$1$2$3[redacted]"],
  ["slack-id", /\b[UWCDGTB](?=[A-Z0-9]*\d)[A-Z0-9]{8,11}\b/g, "[slack-id]"],
  ["email", /[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}/g, "[email]"],
];

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// Returns the text with every match replaced, and a count per kind. A value is
// never reported, only how many were.
function redact(text, context = {}) {
  const counts = {};
  let out = String(text);
  for (const [kind, pattern, replacement] of RULES) {
    out = out.replace(pattern, (...match) => {
      counts[kind] = (counts[kind] || 0) + 1;
      return replacement.replace(/\$(\d)/g, (_, n) => match[Number(n)] || "");
    });
  }
  const roots = [];
  for (const [value, short] of [[context.project, "<project>"], [context.home || os.homedir(), "~"]]) {
    if (!value) continue;
    for (const variant of new Set([value, safeRealpath(value)])) {
      if (variant && variant !== "/") roots.push([variant, short]);
    }
  }
  roots.sort((a, b) => b[0].length - a[0].length);
  for (const [value, short] of roots) {
    out = out.replace(new RegExp(`${escapeRegExp(value)}(?=$|[/\\s"'\`)\\]:,;])`, "gm"), () => {
      counts.path = (counts.path || 0) + 1;
      return short;
    });
  }
  return { text: out, counts };
}

function safeRealpath(value) {
  try {
    return fs.realpathSync(value);
  } catch {
    return value;
  }
}

function merge(total, counts) {
  for (const [kind, n] of Object.entries(counts)) total[kind] = (total[kind] || 0) + n;
}

function git(cwd, args) {
  const result = spawnSync("git", ["-C", cwd, ...args], { encoding: "utf8", timeout: 5000 });
  return result.status === 0 ? String(result.stdout || "").trim() : null;
}

function parse(argv) {
  const options = { words: [], unknown: null, missing: null };
  const valued = { "--command": "command", "--output-file": "outputFile", "--expected": "expected", "--repro": "repro", "--impact": "impact", "--host": "host" };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--help" || arg === "-h") options.help = true;
    else if (arg === "--doctor") options.doctor = true;
    else if (arg === "--create") options.create = true;
    else if (arg === "--confirmed") options.confirmed = true;
    else if (valued[arg]) {
      if (i + 1 >= argv.length) options.missing = arg;
      else options[valued[arg]] = argv[++i];
    } else if (arg.startsWith("--")) options.unknown = options.unknown || arg;
    else options.words.push(arg);
  }
  return options;
}

// What is collected, and nothing else (#505 D4).
function environment(cwd, options) {
  const host = options.host || (process.env.CLAUDECODE ? "claude" : "unknown");
  const entry = path.join(__dirname, "..", "..", "bin", "keel.js");
  const context = spawnSync(process.execPath, [entry, "context"], { cwd, encoding: "utf8", timeout: 20000 });
  const lines = String(context.stdout || "").split(/\r?\n/)
    .filter((line) => /^(Keel context|Next action):/.test(line));
  const facts = [
    `Keel: ${PACKAGE_JSON.version}`,
    `Node: ${process.version}`,
    `Platform: ${process.platform} ${process.arch}`,
    `Host: ${host}`,
    ...lines,
  ];
  if (options.doctor) {
    const doctor = spawnSync(process.execPath, [entry, "--doctor"], { cwd, encoding: "utf8", timeout: 30000 });
    facts.push("", "`keel --doctor`:", "```", String(doctor.stdout || "").trimEnd(), "```");
  }
  return facts;
}

function readOutput(cwd, file) {
  if (!file) return null;
  try {
    const text = fs.readFileSync(path.resolve(cwd, file), "utf8");
    const lines = text.split(/\r?\n/);
    const kept = lines.length > 80 ? [...lines.slice(0, 80), `… (${lines.length - 80} more lines not included)`] : lines;
    return kept.join("\n").slice(0, 8000);
  } catch (error) {
    return `(could not read ${file}: ${error.code || error.message})`;
  }
}

function build(cwd, options) {
  const project = git(cwd, ["rev-parse", "--show-toplevel"]) || cwd;
  const counts = {};
  const clean = (text) => {
    const result = redact(text, { project });
    merge(counts, result.counts);
    return result.text;
  };
  const summary = clean(options.words.join(" ").trim());
  const placeholder = (value, text) => (value ? clean(value) : text);
  const output = readOutput(cwd, options.outputFile);
  const evidence = [];
  if (options.command) evidence.push("命令：", "```", clean(options.command), "```");
  if (output !== null) evidence.push("输出：", "```", clean(output), "```");
  const body = [
    "## 现象", "", summary, "",
    "## 期望", "", placeholder(options.expected, "（未填写）"), "",
    "## 复现", "", placeholder(options.repro, "（未填写）"), "",
    "## 证据", "", evidence.length ? evidence.join("\n") : "（未提供命令或输出）", "",
    "## 影响", "", placeholder(options.impact, "（未填写）"), "",
    "## 环境", "", ...environment(cwd, options).map((line) => (line.startsWith("`") || line.startsWith("```") || line === "" ? clean(line) : `- ${clean(line)}`)), "",
    "---",
    "由 `keel feedback` 起草；未带任何准入标签，是否值得做由负责人决定。", "",
  ].join("\n");
  return { title: summary.split(/\r?\n/)[0].slice(0, 120), body, counts };
}

// The three longest distinct ASCII words of at least four characters, else the
// first twelve characters (#505 D5).
function keywords(summary) {
  const words = [...new Set((summary.match(/[A-Za-z0-9][A-Za-z0-9_.:-]{3,}/g) || []).map((w) => w.toLowerCase()))]
    .sort((a, b) => b.length - a.length).slice(0, 3);
  return words.length ? words.join(" ") : summary.slice(0, 12);
}

function ghAvailable() {
  const result = spawnSync("gh", ["--version"], { encoding: "utf8", timeout: 10000 });
  return !result.error && result.status === 0;
}

function duplicates(title) {
  if (!ghAvailable()) return { searched: false, reason: "gh is not available", found: [] };
  const result = spawnSync("gh", [
    "issue", "list", "--repo", KEEL_REPO, "--state", "all", "--search", keywords(title),
    "--limit", "5", "--json", "number,title,state,url",
  ], { encoding: "utf8", timeout: 30000 });
  if (result.status !== 0) {
    return { searched: false, reason: String(result.stderr || "gh failed").trim().split(/\r?\n/)[0], found: [] };
  }
  try {
    return { searched: true, found: JSON.parse(result.stdout || "[]").slice(0, 5) };
  } catch {
    return { searched: false, reason: "gh printed something that is not JSON", found: [] };
  }
}

function shellQuote(value) {
  return `'${String(value).replace(/'/g, `'\\''`)}'`;
}

function saveDraft(draft) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "keel-feedback-"));
  const file = path.join(dir, "issue.md");
  fs.writeFileSync(file, `# ${draft.title}\n\n${draft.body}`);
  return file;
}

function describe(draft, file, dup) {
  const lines = ["Keel feedback draft — nothing was created.", "", `Title: ${draft.title}`, "", draft.body];
  const kinds = Object.entries(draft.counts).map(([kind, n]) => `${kind} ${n}`);
  lines.push(`Redacted ${Object.values(draft.counts).reduce((a, b) => a + b, 0)} value(s)${kinds.length ? ` (${kinds.join(", ")})` : ""}; the values are not printed.`);
  lines.push(`Saved: ${file}`, "");
  if (!dup.searched) {
    lines.push(`Similar issues: not searched (${dup.reason}).`);
  } else if (!dup.found.length) {
    lines.push("Similar issues: none found.");
  } else {
    lines.push("Similar issues (up to 5):");
    for (const issue of dup.found) lines.push(`  #${issue.number} ${issue.title} (${issue.state}) ${issue.url}`);
    lines.push("To add to one yourself (Keel runs no comment):");
    lines.push(`  gh issue comment ${dup.found[0].number} --repo ${KEEL_REPO} --body-file ${file}`);
  }
  lines.push("To create it:", `  gh issue create --repo ${KEEL_REPO} --title ${shellQuote(draft.title)} --body-file ${file}`);
  return lines.join("\n");
}

// `issue:TanglmChris/keel` in the project's own `authorize:` waives the
// per-issue confirmation (#505 D6). A declaration Keel cannot read grants
// nothing, as everywhere else.
function authorized(project) {
  try {
    const { declared } = require("./config").readStandingAuthorization(project);
    return declared.some((entry) => entry === `issue:${KEEL_REPO}` || entry.startsWith(`issue:${KEEL_REPO}@`));
  } catch {
    return false;
  }
}

// No label, assignee or milestone is ever passed, and nothing else of any
// issue is touched (#505 D6).
function create(draft, file) {
  const result = spawnSync("gh", ["issue", "create", "--repo", KEEL_REPO, "--title", draft.title, "--body-file", file], {
    encoding: "utf8", timeout: 60000,
  });
  if (result.error || result.status !== 0) {
    const why = result.error ? result.error.code || result.error.message : String(result.stderr || "gh failed").trim().split(/\r?\n/)[0];
    return { ok: false, why };
  }
  const url = String(result.stdout || "").trim().split(/\r?\n/).pop();
  return { ok: true, url };
}

function runFeedback(argv) {
  const options = parse(argv);
  if (options.help) {
    process.stdout.write(`${USAGE}\n`);
    return 0;
  }
  if (options.unknown || options.missing || !options.words.length) {
    const why = options.unknown ? `unknown option ${options.unknown}` : options.missing ? `${options.missing} needs a value` : "a one-sentence summary is required";
    process.stderr.write(`keel feedback: ${why}\n${USAGE}\n`);
    return 2;
  }
  const cwd = process.cwd();
  const draft = build(cwd, options);
  const file = saveDraft(draft);
  process.stdout.write(`${describe(draft, file, duplicates(draft.title))}\n`);
  if (!options.create) return 0;
  if (!options.confirmed && !authorized(git(cwd, ["rev-parse", "--show-toplevel"]) || cwd)) {
    process.stderr.write(
      `keel feedback: not created. This project does not declare \`issue:${KEEL_REPO}\` in authorize:, so the user must approve this draft first; `
        + "rerun with --create --confirmed once they have.\n"
    );
    return 3;
  }
  const made = create(draft, file);
  if (!made.ok) {
    process.stderr.write(`keel feedback: not created (${made.why}). The draft is saved at ${file}; run the \`gh issue create\` command above when gh works.\n`);
    return 4;
  }
  process.stdout.write(`Created: ${made.url}\n`);
  return 0;
}

module.exports = { KEEL_REPO, USAGE, redact, keywords, runFeedback };
