"use strict";

const fs = require("fs");
const path = require("path");

// The closed vocabulary of actions a repository may standing-authorize. It is
// closed so an entry outside it can be reported by name: a free-form grant
// cannot tell a typo from a decision, and silently dropping one leaves the
// author believing they authorized something they did not.
const STANDING_AUTHORIZATION_ACTIONS = ["commit", "push", "release", "archive"];

// The closed vocabulary of capability tiers a repository may declare for a
// delegated task. The names describe the capability the work requires, never
// the size of the work: a tier named for size would authorize the agent's guess
// about difficulty, which is the judgement 5.7.0 refused for triage. Keel names
// no concrete model — one is target-specific and expires at the next release,
// and the declaration must still be correct after both.
const DELEGATION_TIERS = ["routine", "standard", "deep"];

const CONFIG_RELATIVE_PATH = path.join("keel", "config.yaml");

// The declarations share keel/config.yaml with fast_check, so the reader stays
// line-oriented rather than pulling in a YAML dependency for a format Keel
// controls and keeps flat on purpose.
function configList(repo, key) {
  const configPath = path.join(repo, "keel", "config.yaml");
  const entries = [];
  if (!fs.existsSync(configPath)) return entries;
  const opener = new RegExp(`^${key}\\s*:\\s*$`);
  let inBlock = false;
  for (const line of fs.readFileSync(configPath, "utf8").split(/\r?\n/)) {
    if (/^\s*#/.test(line)) continue;
    if (opener.test(line)) {
      inBlock = true;
      continue;
    }
    if (!inBlock) continue;
    if (line.trim() === "") continue;
    const entry = line.match(/^\s+-\s*(\S+)\s*$/);
    // Anything that is not a list item closes the block; the next top-level
    // key belongs to the rest of the file.
    if (!entry) break;
    entries.push(entry[1]);
  }
  return entries;
}

// Which issues may start work without asking. This is a declaration and never
// an inference: "should this issue be done" sits in the materiality categories
// that require asking, and a precedent may never move a decision out of them.
// A label is the unit because a human applies one to a specific issue, so the
// policy authorizes a class the owner curates one issue at a time rather than a
// guess about which issues look easy.
function readTriagePolicy(repo) {
  return { labels: configList(repo, "triage") };
}

function readStandingAuthorization(repo) {
  const declared = [];
  const unknown = [];
  for (const entry of configList(repo, "authorize")) {
    if (STANDING_AUTHORIZATION_ACTIONS.includes(entry)) declared.push(entry);
    else unknown.push(entry);
  }
  // Fail closed. A declaration Keel cannot fully read authorizes nothing,
  // because the alternative is granting the entries beside a typo while the
  // author believes they granted the typo too.
  if (unknown.length > 0) return { declared: [], unknown };
  return { declared, unknown };
}

// A nested block of `name: value` entries under one top-level key. Delegation
// needs a key with a value rather than a bare list, so it cannot reuse
// configList; the reader stays line-oriented for the same reason the others do.
function configMap(repo, key) {
  const configPath = path.join(repo, "keel", "config.yaml");
  const entries = {};
  if (!fs.existsSync(configPath)) return entries;
  const opener = new RegExp(`^${key}\\s*:\\s*$`);
  let inBlock = false;
  for (const line of fs.readFileSync(configPath, "utf8").split(/\r?\n/)) {
    if (/^\s*#/.test(line)) continue;
    if (opener.test(line)) {
      inBlock = true;
      continue;
    }
    if (!inBlock) continue;
    if (line.trim() === "") continue;
    const entry = line.match(/^\s+(\w+)\s*:\s*(\S+)\s*$/);
    // Anything that is not an indented entry closes the block, exactly as it
    // does for a list; the next top-level key belongs to the rest of the file.
    if (!entry) break;
    entries[entry[1]] = entry[2];
  }
  return entries;
}

// Who runs a task. Declaring a tier is what permits delegation at that tier —
// there is no separate on/off entry, because a tier with no permission and a
// permission with no tier are both incomplete, and one field cannot disagree
// with itself. An absent declaration delegates nothing, which is the default.
function readDelegationPolicy(repo) {
  const block = configMap(repo, "delegation");
  const tier = block.tier;
  // The accepted set travels with every answer so a caller reporting a refusal
  // can name the alternatives without importing the vocabulary itself. A copy,
  // because a caller that sorted or spliced it in place would edit the closed
  // set for everyone who read it afterward.
  const accepted = [...DELEGATION_TIERS];
  if (!tier) return { declared: false, tier: null, unknown: [], accepted };
  // Fail closed, the same way an unrecognized `authorize:` action does: a
  // declaration Keel cannot fully read authorizes nothing, because the author
  // of a typo believes they declared what they typed.
  if (!DELEGATION_TIERS.includes(tier)) {
    return { declared: true, tier: null, unknown: [tier], accepted };
  }
  return { declared: true, tier, unknown: [], accepted };
}

function configScalar(repo, key) {
  const configPath = path.join(repo, "keel", "config.yaml");
  if (!fs.existsSync(configPath)) return null;
  const pattern = new RegExp(`^${key}\\s*:\\s*(.+?)\\s*$`);
  for (const line of fs.readFileSync(configPath, "utf8").split(/\r?\n/)) {
    const stripped = line.trim();
    if (stripped.startsWith("#")) continue;
    const match = stripped.match(pattern);
    if (match) return match[1];
  }
  return null;
}

// Keel reads a local directory and nothing else. How that directory came to
// exist — a clone, an installed plugin, hand-authored files — is outside Keel,
// because a surface that reaches the network trades the local, offline,
// deterministic properties that make it trustworthy.
function readPrecedentStore(repo) {
  const declared = configScalar(repo, "precedents");
  if (!declared) return { declared: null, path: null, precedents: [] };
  const resolved = path.isAbsolute(declared)
    ? declared
    : path.resolve(repo, declared);
  // A declared path that is not there degrades to the no-store behavior rather
  // than to an error: a private store is exactly what a fresh clone and CI will
  // not have, and a repository declaring one must still be usable by them.
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isDirectory()) {
    return { declared, path: resolved, precedents: [] };
  }
  const precedents = fs
    .readdirSync(resolved)
    .filter((name) => name.endsWith(".md") && name !== "README.md")
    .sort()
    .map((name) => {
      const content = fs.readFileSync(path.join(resolved, name), "utf8");
      const status = (content.match(/^-\s*Status:\s*(\S+)/mi) || [])[1] || "";
      // Presence, never judgement. Keel cannot tell a good reason from a bad
      // one and must not imply it can; it can tell a reason from no reason,
      // and a conclusion with no reason cannot be carried to a situation that
      // is not literally the recorded one.
      const rationale = content
        .split(/^##\s+/m)
        .find((section) => /^Rationale\s*$/i.test(section.split(/\r?\n/)[0]));
      return {
        name: name.replace(/\.md$/, ""),
        status: status.toLowerCase(),
        complete: Boolean(
          rationale
          && rationale.split(/\r?\n/).slice(1).join("\n").trim()
        ),
      };
    });
  return { declared, path: resolved, precedents };
}

// Evaluate a declared policy against labels handed in. Keel never fetches the
// issue: the agent reads it with `gh` and passes what it found, which keeps this
// local, offline, deterministic, and testable without a network.
function triageIssue(repo, labels) {
  const { labels: accepted } = readTriagePolicy(repo);
  const carried = labels.filter((label) => label);
  if (accepted.length === 0) {
    return {
      status: "refuse",
      accepted,
      labels: carried,
      reason:
        "this repository declares no triage policy, so no issue starts work "
        + "unattended; declare accepted labels under `triage:` in "
        + "keel/config.yaml to change that. This is not a judgement about the "
        + "issue.",
    };
  }
  const matched = carried.filter((label) => accepted.includes(label));
  if (matched.length > 0) {
    return {
      status: "admit",
      accepted,
      labels: carried,
      matched,
      reason:
        `admitted by declared label ${matched.join(", ")}; admission starts `
        + "work and decides nothing after it — every later gate still applies "
        + "and a material decision still stops for the owner.",
    };
  }
  return {
    status: "refuse",
    accepted,
    labels: carried,
    reason:
      `the issue carries ${carried.length > 0 ? carried.join(", ") : "no labels"}`
      + ` and this repository accepts ${accepted.join(", ")}.`,
  };
}

module.exports = {
  CONFIG_RELATIVE_PATH,
  DELEGATION_TIERS,
  STANDING_AUTHORIZATION_ACTIONS,
  readDelegationPolicy,
  readPrecedentStore,
  readStandingAuthorization,
  readTriagePolicy,
  triageIssue,
};
