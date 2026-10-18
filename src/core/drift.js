"use strict";

// What moved a task's fingerprint, when Git can say (issue #342).
//
// Only the previous digest is kept in the anchor, so the capsule behind it is
// gone — but the commit that recorded the anchor is not. Its task sources,
// compiled by the running compiler, either reproduce the recorded digest (the
// commit is the contract that was recorded, so a diff against today names the
// field that moved), or fail to while the anchor names another Keel version
// and the commit compiles to today's fingerprint (the compiler moved, not the
// contract). Anything else is a contract edited between recording and commit,
// the case a reconstruction from Git cannot see, and nothing is claimed.

const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const STANDING_AUTHORIZATION = /^Standing authorization \(keel\/config\.yaml\):/;

function git(repo, args) {
  try {
    return execFileSync("git", ["-C", repo, ...args], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
      maxBuffer: 64 * 1024 * 1024,
    });
  } catch {
    return null;
  }
}

function runningVersion() {
  try {
    return require(path.join(__dirname, "..", "..", "package.json")).version;
  } catch {
    return null;
  }
}

function anchoredVersion(anchor) {
  const match = String(anchor || "").match(/\(keel\s+([0-9][0-9A-Za-z.+-]*)\)/);
  return match ? match[1] : null;
}

// The newest commit whose tasks.md holds the digest: the one that recorded it.
function recordingCommit(repo, relative, digest) {
  const log = git(repo, ["log", "--format=%H", "-S", digest, "--", relative]);
  if (!log) return null;
  for (const sha of log.split("\n").filter(Boolean)) {
    const content = git(repo, ["show", `${sha}:./${relative}`]);
    if (content !== null && content.includes(digest)) return sha;
  }
  return null;
}

// Only what the compiler reads: the change, the published specs, the config.
function materialize(repo, sha, change, into) {
  const listed = git(repo, [
    "ls-tree", "-r", "--name-only", sha, "--",
    `openspec/changes/${change}`, "openspec/specs", "keel/config.yaml",
  ]);
  if (listed === null) return false;
  for (const file of listed.split("\n").filter(Boolean)) {
    const content = git(repo, ["show", `${sha}:./${file}`]);
    if (content === null) return false;
    const target = path.join(into, ...file.split("/"));
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, content, "utf8");
  }
  return true;
}

function differences(before, after, at, out) {
  if (JSON.stringify(before) === JSON.stringify(after)) return;
  const isObject = (value) => value && typeof value === "object" && !Array.isArray(value);
  if (
    Array.isArray(before) && Array.isArray(after) && before.length === after.length
    && before.some((item) => item && typeof item === "object")
  ) {
    before.forEach((item, index) => differences(item, after[index], `${at}[${index}]`, out));
    return;
  }
  if (isObject(before) && isObject(after)) {
    for (const key of [...new Set([...Object.keys(before), ...Object.keys(after)])].sort()) {
      differences(before[key], after[key], at ? `${at}.${key}` : key, out);
    }
    return;
  }
  out.push(at);
}

function withoutStandingAuthorization(capsule) {
  const copy = JSON.parse(JSON.stringify(capsule));
  copy.boundaries.autonomy = copy.boundaries.autonomy.filter(
    (entry) => !STANDING_AUTHORIZATION.test(entry)
  );
  return copy;
}

// { kind: "compiler" | "authorization" | "source", commit, recordedVersion,
// runningVersion, fields } or null when nothing can be said.
function diagnoseDrift(repo, change, taskId, anchor, current) {
  // Required here rather than at the top: task-contract is the compiler this
  // module drives, and gates and context require both.
  const { compileTaskContract, parseTasks } = require("./task-contract");
  const digest = (String(anchor || "").match(/sha-?256[\s:`]*([a-f0-9]{64})/i) || [])[1];
  if (!digest || !current || !current.capsule) return null;
  const relative = `openspec/changes/${change}/tasks.md`;
  const sha = recordingCommit(repo, relative, digest.toLowerCase());
  if (!sha) return null;
  let scratch = null;
  try {
    scratch = fs.mkdtempSync(path.join(os.tmpdir(), "keel-drift-"));
    if (!materialize(repo, sha, change, scratch)) return null;
    const tasksPath = path.join(scratch, ...relative.split("/"));
    if (!fs.existsSync(tasksPath)) return null;
    const task = parseTasks(fs.readFileSync(tasksPath, "utf8")).find((item) => item.id === taskId);
    if (!task) return null;
    const then = compileTaskContract(scratch, change, task, { gitRepo: repo });
    if (then.diagnostics.length > 0 || !then.capsule) return null;
    const recordedVersion = anchoredVersion(anchor);
    const running = runningVersion();
    const base = { commit: sha, recordedVersion, runningVersion: running };
    if (then.fingerprint.value === digest.toLowerCase()) {
      const fields = [];
      differences(then.capsule, current.capsule, "", fields);
      if (fields.length === 0) return null;
      const authorizationOnly = JSON.stringify(withoutStandingAuthorization(then.capsule))
        === JSON.stringify(withoutStandingAuthorization(current.capsule));
      const named = fields.map((field) => {
        const index = field.match(/^authority\[(\d+)\]/);
        const source = index && current.capsule.authority[Number(index[1])]
          ? current.capsule.authority[Number(index[1])].source
          : null;
        return source ? `${field} (${source})` : field;
      });
      return { ...base, kind: authorizationOnly ? "authorization" : "source", fields: named };
    }
    if (
      recordedVersion && running && recordedVersion !== running
      && then.fingerprint.value === current.fingerprint.value
    ) {
      return { ...base, kind: "compiler", fields: [] };
    }
    return null;
  } catch {
    return null;
  } finally {
    if (scratch) fs.rmSync(scratch, { recursive: true, force: true });
  }
}

// The sentence a drift message carries for a diagnosis, or "".
function driftCause(diagnosis) {
  if (!diagnosis) return "";
  const short = diagnosis.commit.slice(0, 12);
  if (diagnosis.kind === "compiler") {
    return `Cause: a compiler change. The task's sources as committed in ${short}, `
      + "the commit that recorded this anchor, compile to today's fingerprint under "
      + `Keel ${diagnosis.runningVersion}, and the anchor was recorded by Keel `
      + `${diagnosis.recordedVersion}, so the fingerprint moved with the compiler and `
      + "not with the contract. Re-record with `keel gate task-start --record`; the "
      + "evidence stands and no `--keep-evidence` is needed.";
  }
  const fields = diagnosis.fields.map((field) => `\`${field}\``).join(", ");
  if (diagnosis.kind === "authorization") {
    return `Cause: since ${short}, the commit that recorded this anchor, only the `
      + `inherited standing authorization from keel/config.yaml changed (${fields}).`;
  }
  return `Cause: since ${short}, the commit that recorded this anchor, these capsule `
    + `fields changed: ${fields}.`;
}

module.exports = { anchoredVersion, diagnoseDrift, driftCause, runningVersion };
