"use strict";

const fs = require("fs");
const path = require("path");

// The closed vocabulary of actions a repository may standing-authorize. It is
// closed so an entry outside it can be reported by name: a free-form grant
// cannot tell a typo from a decision, and silently dropping one leaves the
// author believing they authorized something they did not.
const STANDING_AUTHORIZATION_ACTIONS = [
  "commit",
  "push",
  "release",
  "archive",
  "continuation",
];

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

// The sub-keys a `triage:` block may declare. Closed for the same reason the
// authorization actions are: an entry outside it can then be reported by name
// instead of being silently dropped from a policy about what may run unattended.
const TRIAGE_SOURCES = ["labels", "issues"];

// The lines belonging to one top-level block, handed back unclassified. The
// list and map readers each stop at the first line they cannot use, which is
// right for a flat shape and wrong here: a `triage:` block may hold two shapes,
// and telling them apart — or refusing a mixture — needs to see all of it.
// Returns null when the key is not declared at all, which is not the same as a
// key declared with nothing under it.
function configBlockLines(repo, key) {
  const configPath = path.join(repo, "keel", "config.yaml");
  if (!fs.existsSync(configPath)) return null;
  const opener = new RegExp(`^${key}\\s*:\\s*(.*)$`);
  const lines = [];
  let inBlock = false;
  let inline = null;
  for (const line of fs.readFileSync(configPath, "utf8").split(/\r?\n/)) {
    if (/^\s*#/.test(line)) continue;
    if (!inBlock) {
      const opened = line.match(opener);
      if (!opened) continue;
      inBlock = true;
      // `triage: { issues: [62] }` is the flow style, which this reader does
      // not parse. Keeping the text lets the caller name it rather than
      // reporting an undeclared policy for a declaration plainly present.
      if (opened[1].trim() !== "") inline = opened[1].trim();
      continue;
    }
    if (line.trim() === "") continue;
    // A line at column zero is the next top-level key, whatever its shape.
    if (!/^\s/.test(line)) break;
    lines.push(line);
  }
  if (!inBlock) return null;
  return { lines, inline };
}

// Which issues may start work without asking. This is a declaration and never
// an inference: "should this issue be done" sits in the materiality categories
// that require asking, and a precedent may never move a decision out of them.
//
// Two sources, either sufficient alone. A label is applied by hand to one
// issue; so is an issue number, so both curate a class one issue at a time
// rather than guessing which issues look easy. They differ in where the
// owner's decision is written down — the label writes it on the issue, where
// the person who reported it can see an operational switch in a vocabulary
// they were asked to classify with, and the number writes it in a file only a
// committer can change (#62).
function readTriagePolicy(repo) {
  const block = configBlockLines(repo, "triage");
  const empty = { labels: [], issues: [], unreadable: [] };
  if (block === null) return empty;

  const unreadable = [];
  if (block.inline !== null) unreadable.push(block.inline);

  const sections = new Map();
  // Entries written directly under `triage:` with no sub-key. This is the
  // shape every repository declared before a second source existed, and it
  // still means labels — a bare token is never read as a number, because
  // reclassifying one would move an authorization boundary in a repository
  // nobody edited.
  const bare = [];
  let current = null;
  for (const line of block.lines) {
    const opened = line.match(/^\s+([A-Za-z_]\w*)\s*:\s*$/);
    if (opened) {
      current = opened[1];
      if (!TRIAGE_SOURCES.includes(current)) unreadable.push(current);
      else if (!sections.has(current)) sections.set(current, []);
      continue;
    }
    const entry = line.match(/^\s+-\s*(\S.*?)\s*$/);
    if (!entry) {
      unreadable.push(line.trim());
      continue;
    }
    if (current === null) bare.push(entry[1]);
    // Under a sub-key Keel could not read; the sub-key is already reported.
    else if (!sections.has(current)) unreadable.push(entry[1]);
    else sections.get(current).push(entry[1]);
  }
  // One shape or the other. A block written both ways has no reading that is
  // obviously what its author meant, and guessing at one is how a policy comes
  // to admit something nobody declared.
  if (bare.length > 0 && sections.size > 0) unreadable.push(...bare);

  const labels = bare.length > 0 ? bare : sections.get("labels") || [];
  const issues = [];
  for (const entry of sections.get("issues") || []) {
    // A bare positive integer and nothing else. `#62` is reported by name
    // rather than guessed at, because a declaration Keel half-understands is
    // how an owner comes to believe they admitted something they did not.
    if (/^[1-9]\d*$/.test(entry)) issues.push(entry);
    else unreadable.push(entry);
  }

  // Fail closed, exactly as an unrecognized `authorize:` action does: a
  // declaration Keel cannot fully read admits nothing, because the entries
  // beside a typo were not the ones its author meant to grant either.
  if (unreadable.length > 0) return { labels: [], issues: [], unreadable };
  return { labels, issues, unreadable };
}

// `change-close --action sync|archive` prints `sync` beside `archive`, and a
// reader who copies from that help text into `authorize:` reasonably copies
// both — but only `archive` is a name this vocabulary accepts (#93). Naming
// that confusion only when `sync` is the entry present keeps every other
// unrecognized name (a genuine typo) unchanged.
function standingAuthorizationUnknownMessage(unknown) {
  const base = `keel/config.yaml declares unrecognized ${
    unknown.length === 1 ? "action" : "actions"
  }: ${unknown.join(", ")}; accepted names are `
    + `${STANDING_AUTHORIZATION_ACTIONS.join(", ")}. The whole declaration `
    + "authorizes nothing until it is corrected.";
  if (!unknown.includes("sync")) return base;
  return `${base} \`sync\` is a value of \`change-close --action\`, not a `
    + "name `authorize:` accepts; declare `archive` if you mean to authorize "
    + "the gate that runs it.";
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
  if (unknown.length > 0) {
    return {
      declared: [],
      unknown,
      message: standingAuthorizationUnknownMessage(unknown),
    };
  }
  return { declared, unknown, message: null };
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

// The sentence every verdict ends on. Admission is a start and nothing else,
// and the one place a reader meets that is the reason line.
const ADMISSION_STARTS_ONLY =
  "; admission starts work and decides nothing after it — every later gate "
  + "still applies and a material decision still stops for the owner.";

// Evaluate a declared policy against the issue attributes handed in. Keel never
// fetches the issue: the agent reads it with `gh` and passes what it found,
// which keeps this local, offline, deterministic, and testable without a
// network. `issue` is the issue's number, or null when the caller has none.
function triageIssue(repo, labels, issue = null) {
  const policy = readTriagePolicy(repo);
  const { labels: accepted, issues: acceptedIssues, unreadable } = policy;
  const carried = labels.filter((label) => label);
  const number = issue === null || issue === undefined ? null : String(issue);
  const base = {
    accepted,
    acceptedIssues,
    labels: carried,
    issue: number,
    sources: [],
  };
  if (unreadable.length > 0) {
    return {
      ...base,
      status: "refuse",
      unreadable,
      reason:
        "this repository's `triage:` declaration could not be read, so no "
        + "issue starts work unattended. Keel could not read "
        + `${unreadable.map((entry) => `\`${entry}\``).join(", ")}. Declare `
        + "accepted labels under `labels:` and issue numbers under `issues:` "
        + "as bare numbers, or a bare list of labels directly under `triage:`. "
        + "A declaration that is only partly readable admits nothing, because "
        + "the entries beside a mistake are not the ones its author meant to "
        + "grant. This is not a judgement about the issue.",
    };
  }
  if (accepted.length === 0 && acceptedIssues.length === 0) {
    return {
      ...base,
      status: "refuse",
      reason:
        "this repository declares no triage policy, so no issue starts work "
        + "unattended; declare accepted labels under `triage:` in "
        + "keel/config.yaml to change that. This is not a judgement about the "
        + "issue.",
    };
  }
  const matched = carried.filter((label) => accepted.includes(label));
  const matchedIssue =
    number !== null && acceptedIssues.includes(number) ? number : null;
  if (matched.length > 0 || matchedIssue !== null) {
    const by = [];
    if (matched.length > 0) by.push(`declared label ${matched.join(", ")}`);
    if (matchedIssue !== null) {
      by.push(`issue number ${matchedIssue}, listed in keel/config.yaml`);
    }
    return {
      ...base,
      status: "admit",
      matched,
      matchedIssue,
      sources: [
        ...(matched.length > 0 ? ["label"] : []),
        ...(matchedIssue !== null ? ["issue"] : []),
      ],
      reason: `admitted by ${by.join(" and by ")}${ADMISSION_STARTS_ONLY}`,
    };
  }
  // A source the repository did not declare is left out of both halves of the
  // sentence. Naming it would read as a policy that exists and did not match,
  // which is the distinction the refusal is here to draw.
  let subject =
    `the issue carries ${carried.length > 0 ? carried.join(", ") : "no labels"}`;
  if (number !== null) subject += ` and is numbered ${number}`;
  const acceptedParts = [];
  if (accepted.length > 0) acceptedParts.push(accepted.join(", "));
  if (acceptedIssues.length > 0) {
    acceptedParts.push(`issues ${acceptedIssues.join(", ")}`);
  }
  return {
    ...base,
    status: "refuse",
    reason: `${subject} and this repository accepts ${acceptedParts.join(", and ")}.`,
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
