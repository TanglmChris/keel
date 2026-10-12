#!/usr/bin/env node
"use strict";

// Keel plugin PreToolUse write guard: deterministic denial of out-of-Touch
// file edits while an explicit keel/guard.json manifest is active. Absence of
// the manifest allows everything silently; a present-but-untrusted manifest
// fails closed. The hook never writes state, never spawns the keel CLI, and
// always exits 0 — denial is expressed only through hook output. While no
// manifest is active it may instead run the newer installed copy of itself
// (forward.js, #204); while one is, the loaded guard keeps deciding, so a task
// finishes under the guard it started with. The
// repository is the guard's scope: a path resolving outside it is not a product
// write and passes through, decided before the manifest is read so that no
// manifest state can reach it.

const crypto = require("crypto");
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

const MANIFEST_SCHEMA = "keel-write-guard/v1";
const FILE_EDIT_TOOLS = new Map([
  ["Edit", "file_path"],
  ["Write", "file_path"],
  ["NotebookEdit", "notebook_path"],
]);

function readStdin() {
  try {
    return fs.readFileSync(0, "utf8");
  } catch {
    return "";
  }
}

function deny(reason) {
  process.stdout.write(
    `${JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: reason,
      },
    })}\n`
  );
}

// Hand the decision to the user for this one call (#280): the host asks, and
// nothing is stored, so the next call is asked again.
function ask(reason) {
  process.stdout.write(
    `${JSON.stringify({
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "ask",
        permissionDecisionReason: reason,
      },
    })}\n`
  );
}

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function manifestShapeValid(manifest) {
  return (
    manifest
    && manifest.schema === MANIFEST_SCHEMA
    && typeof manifest.change === "string"
    && manifest.change !== ""
    && typeof manifest.task === "string"
    && manifest.task !== ""
    && Array.isArray(manifest.touch)
    && manifest.touch.length > 0
    && manifest.touch.every((item) => typeof item === "string" && item !== "")
    && Array.isArray(manifest.authority)
    && manifest.authority.length > 0
    && manifest.authority.every(
      (item) =>
        item
        && typeof item.path === "string"
        && /^[0-9a-f]{64}$/.test(String(item.sha256 || ""))
    )
  );
}

function globPattern(value) {
  const escaped = value.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(
    `^${escaped
      .replace(/\*\*/g, "\u0000")
      .replace(/\*/g, "[^/]*")
      .replace(/\u0000/g, ".*")}$`
  );
}

function pathAllowed(candidate, touch) {
  return touch.some((entry) => {
    const normalized = entry.replace(/\\/g, "/").replace(/^\.\//, "");
    if (normalized.endsWith("/")) return candidate.startsWith(normalized);
    if (normalized.includes("*")) return globPattern(normalized).test(candidate);
    return candidate === normalized;
  });
}

// A checked task keeps its records writable so it can finish the Evidence its
// completion gate requires, but earns no further product authorization. Byte
// hashing used to enforce this by accident, since ticking the box changed
// tasks.md; now it is stated. An unreadable or unmatched tasks.md is not read as
// checked — every gate that compiles the capsule catches that, and denying
// product writes on a parse miss would trade a real capability for a guess.
function taskIsChecked(repo, manifest) {
  const file = path.join(
    repo, "openspec", "changes", manifest.change, "tasks.md"
  );
  let content = "";
  try {
    content = fs.readFileSync(file, "utf8");
  } catch {
    return false;
  }
  const id = manifest.task.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = content.match(
    new RegExp(`^\\s*-\\s*\\[([ xX])\\]\\s*${id}(?![0-9.])`, "m")
  );
  return Boolean(match && match[1].toLowerCase() === "x");
}

// A path is not the file it names. `path.resolve` never follows a symbolic
// link, while the `cwd` the operating system reports usually already has, so
// one file could be spelled two ways and get two containment answers: measured
// as a write denied by its resolved path and allowed through a link to the
// same directory, which walked straight past the manifest. The guarded target
// is usually a file about to be created, so what can be resolved is its
// nearest existing ancestor; when nothing resolves, the unresolved path is
// what remains, which is exactly the comparison that shipped.
//
// `src/core/helper.js` answers the same question and must keep answering it
// the same way. It is deliberately not shared as an import: this hook is a
// standalone script the host executes, and depending on `src/core` would make
// the guard fail wherever the package layout differs from this repository's.
function realPathOrNearest(target) {
  let current = path.resolve(target);
  const trailing = [];
  for (;;) {
    try {
      return path.join(fs.realpathSync(current), ...trailing);
    } catch {
      const parent = path.dirname(current);
      if (parent === current) return path.resolve(target);
      trailing.unshift(path.basename(current));
      current = parent;
    }
  }
}

function repoRelative(repo, target) {
  return path.relative(
    realPathOrNearest(repo),
    realPathOrNearest(path.resolve(repo, target))
  );
}

// --- push-branch check (#257) -------------------------------------------------
//
// While keel/config.yaml declares `push:<branch glob>`, every `git push` a Bash
// call runs must target a matching branch, with or without a task manifest.
// The globs are read here rather than through the declaration's validator, so
// a typo elsewhere in `authorize:` — which voids the declaration — leaves the
// check standing: a broken declaration fails toward more checking (D3).

const EXPLICIT_FORM = "`git push origin <branch>`";

function gitOut(cwd, args) {
  const result = spawnSync("git", ["-C", cwd, ...args], { encoding: "utf8", timeout: 3000 });
  return result.status === 0 ? String(result.stdout || "").trim() : null;
}

// `push:` globs and `push-protected:` entries ({ glob, role }) of `authorize:`.
function readPushGlobs(top) {
  let text = "";
  try {
    text = fs.readFileSync(path.join(top, "keel", "config.yaml"), "utf8");
  } catch {
    return { globs: [], protectedEntries: [] };
  }
  const globs = [];
  const protectedEntries = [];
  let inBlock = false;
  for (const line of text.split(/\r?\n/)) {
    if (/^\s*#/.test(line) || line.trim() === "") continue;
    if (/^authorize\s*:\s*$/.test(line)) {
      inBlock = true;
      continue;
    }
    if (!inBlock) continue;
    if (!/^\s/.test(line)) break;
    const bare = line.replace(/\s+#.*$/, "");
    const entry = bare.match(/^\s+-\s*push:(\S+)\s*$/);
    if (entry) globs.push(entry[1]);
    const guarded = bare.match(/^\s+-\s*push-protected:([^@\s]+)(?:@(\S+))?\s*$/);
    if (guarded) protectedEntries.push({ glob: guarded[1], role: guarded[2] || null });
  }
  return { globs, protectedEntries };
}

// The chat role bound to the worktree at `top` (#245), for a role-limited
// protected branch (#280 D3). Read directly: this hook never spawns the CLI.
function sessionRole(top) {
  for (const variable of ["KEEL_CHAT_ROLE", "KEEL_MAIL_ROLE"]) {
    const value = (process.env[variable] || "").trim();
    if (value) return value;
  }
  const common = gitOut(top, ["rev-parse", "--path-format=absolute", "--git-common-dir"]);
  if (!common) return null;
  try {
    const roles = JSON.parse(fs.readFileSync(path.join(fs.realpathSync(common), "keel-chat", "roles.json"), "utf8"));
    return roles[fs.realpathSync(top)] || null;
  } catch {
    return null;
  }
}

// Modes in which the host cannot be relied on to ask (#280 D3, F2).
const MODES_THAT_CANNOT_ASK = new Set(["bypassPermissions", "dontAsk"]);

// Shell words and the separators between commands. Quotes are honoured, and a
// word that the shell would expand (`$`, a backtick) is marked, because its
// value is not knowable here.
function shellSegments(command) {
  const segments = [];
  let words = [];
  let word = null;
  let expands = false;
  // A redirection's target is not an argument (#286): the next word is dropped.
  let dropNext = false;
  const finishWord = () => {
    if (word !== null) {
      if (dropNext) dropNext = false;
      else words.push({ text: word, expands });
    }
    word = null;
    expands = false;
  };
  const finishSegment = () => {
    finishWord();
    dropNext = false;
    if (words.length) segments.push(words);
    words = [];
  };
  // Heredoc bodies are data, not commands: `<<'EOF'` … `EOF` is skipped from
  // the end of its line to the terminator, so a body line reading like a push
  // is not taken for one.
  const pendingHeredocs = [];
  for (let i = 0; i < command.length; i += 1) {
    const c = command[i];
    if (c === "<" && command[i + 1] === "<" && command[i + 2] !== "<") {
      const marker = command.slice(i + 2).match(/^-?\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1/);
      if (marker) {
        pendingHeredocs.push(marker[2]);
        finishWord();
        i += 1 + marker[0].length;
        continue;
      }
    }
    if (c === "\n" && pendingHeredocs.length) {
      finishSegment();
      let rest = i + 1;
      while (pendingHeredocs.length) {
        const terminator = pendingHeredocs.shift();
        const lines = command.slice(rest).split("\n");
        let consumed = 0;
        for (const line of lines) {
          consumed += line.length + 1;
          if (line.replace(/^\t+/, "") === terminator) break;
        }
        rest += consumed;
      }
      i = rest - 1;
      continue;
    }
    // A redirection — `>`, `>>`, `<`, `2>`, `2>&1`, `>&2`, `&>` — and its target
    // are dropped, never read as arguments (#286 D1). Heredocs are handled above.
    if (c === ">" || c === "<" || (c === "&" && command[i + 1] === ">")) {
      if (c === "&") i += 1;
      if (word !== null && /^\d+$/.test(word) && !expands) {
        word = null;
        expands = false;
      } else {
        finishWord();
      }
      let j = i + 1;
      if (command[j] === ">" || command[j] === "<") j += 1;
      if (command[j] === "&") {
        const fd = command.slice(j + 1).match(/^(\d+|-)/);
        if (fd) {
          i = j + fd[0].length;
          continue;
        }
      }
      dropNext = true;
      i = j - 1;
      continue;
    }
    if (c === "'") {
      const end = command.indexOf("'", i + 1);
      word = (word || "") + command.slice(i + 1, end === -1 ? command.length : end);
      i = end === -1 ? command.length : end;
    } else if (c === '"') {
      let j = i + 1;
      let text = "";
      while (j < command.length && command[j] !== '"') {
        if (command[j] === "\\" && j + 1 < command.length) {
          text += command[j + 1];
          j += 2;
          continue;
        }
        if (command[j] === "$" || command[j] === "`") expands = true;
        text += command[j];
        j += 1;
      }
      word = (word || "") + text;
      i = j;
    } else if (c === "\\" && i + 1 < command.length) {
      word = (word || "") + command[i + 1];
      i += 1;
    } else if (c === "$" || c === "`") {
      expands = true;
      word = (word || "") + c;
    } else if (c === ";" || c === "\n" || c === "&" || c === "|" || c === "(" || c === ")") {
      finishSegment();
    } else if (/\s/.test(c)) {
      finishWord();
    } else {
      word = (word || "") + c;
    }
  }
  finishSegment();
  return segments;
}

const PREFIX_COMMANDS = new Set(["env", "command", "exec", "nohup", "time", "sudo"]);
const SHELLS = new Set(["bash", "sh", "zsh", "eval"]);
const PUSH_FLAGS = new Set([
  "-u", "--set-upstream", "-f", "--force", "--force-if-includes", "--no-force-if-includes",
  "-n", "--dry-run", "--no-verify", "--verify", "-q", "--quiet", "-v", "--verbose",
  "--porcelain", "--progress", "--no-progress", "--atomic", "--no-atomic", "--no-signed",
  "--thin", "--no-thin", "--follow-tags", "--no-follow-tags", "-4", "--ipv4", "-6", "--ipv6",
  "--prune", "--no-recurse-submodules", "--force-with-lease", "--signed", "-d", "--delete",
]);
const PUSH_VALUED = new Set(["-o", "--push-option", "--repo", "--receive-pack", "--exec"]);
const PUSH_UNDETERMINED = new Set(["--all", "--branches", "--mirror", "--tags"]);

// The pushes a command runs, each as { dir, cdBefore, args } or { undetermined }.
function findPushes(command, cwd) {
  const pushes = [];
  let cdBefore = false;
  for (const words of shellSegments(command)) {
    let i = 0;
    while (i < words.length && /^[A-Za-z_][A-Za-z0-9_]*=/.test(words[i].text)) i += 1;
    while (i < words.length && PREFIX_COMMANDS.has(words[i].text)) i += 1;
    const head = words[i] ? words[i].text : "";
    if (head === "cd" || head === "pushd") {
      cdBefore = true;
      continue;
    }
    if (SHELLS.has(head)) {
      if (/\bgit\b[\s\S]*\bpush\b/.test(words.slice(i + 1).map((w) => w.text).join(" "))) {
        pushes.push({ undetermined: `it runs \`git push\` inside \`${head}\`` });
      }
      continue;
    }
    if (head !== "git") continue;
    let dir = cwd;
    i += 1;
    let unknownGlobal = null;
    while (i < words.length && words[i].text.startsWith("-")) {
      const option = words[i].text;
      if (option === "-C" && words[i + 1]) {
        dir = path.resolve(dir, words[i + 1].text);
        i += 2;
      } else if (option === "-c" && words[i + 1]) {
        i += 2;
      } else if (option === "--no-pager" || option === "-P") {
        i += 1;
      } else {
        unknownGlobal = option;
        i += 1;
      }
    }
    if (!words[i] || words[i].text !== "push") continue;
    if (unknownGlobal) {
      pushes.push({ undetermined: `the git option \`${unknownGlobal}\` is not one the guard reads` });
      continue;
    }
    pushes.push({ dir, cdBefore, args: words.slice(i + 1) });
  }
  return pushes;
}

function currentBranch(dir) {
  return gitOut(dir, ["symbolic-ref", "--short", "-q", "HEAD"]);
}

// The branch a push with no refspec goes to: its configured push destination.
function pushDestination(dir) {
  const ref = gitOut(dir, ["rev-parse", "--symbolic-full-name", "@{push}"]);
  if (!ref || !ref.startsWith("refs/remotes/")) return null;
  const rest = ref.slice("refs/remotes/".length);
  const remotes = (gitOut(dir, ["remote"]) || "").split(/\s+/).filter(Boolean)
    .sort((a, b) => b.length - a.length);
  const remote = remotes.find((name) => rest.startsWith(`${name}/`));
  return remote ? rest.slice(remote.length + 1) : null;
}

// Target branches of one push, or { undetermined: reason }.
function pushTargets(push) {
  if (push.undetermined) return push;
  const positionals = [];
  let deleting = false;
  for (let i = 0; i < push.args.length; i += 1) {
    const word = push.args[i];
    if (word.expands) return { undetermined: `\`${word.text}\` is expanded by the shell` };
    const text = word.text;
    if (text === "--") {
      positionals.push(...push.args.slice(i + 1).map((w) => w.text));
      break;
    }
    if (!text.startsWith("-") || text === "-") {
      positionals.push(text);
      continue;
    }
    const name = text.includes("=") ? text.slice(0, text.indexOf("=")) : text;
    if (PUSH_UNDETERMINED.has(name)) return { undetermined: `\`${name}\` pushes refs the guard cannot list` };
    if (name === "-d" || name === "--delete") deleting = true;
    if (PUSH_VALUED.has(name)) {
      if (!text.includes("=")) i += 1;
      continue;
    }
    if (PUSH_FLAGS.has(name) || name.startsWith("--force-with-lease") || name.startsWith("--signed")
      || name.startsWith("--recurse-submodules")) {
      continue;
    }
    if (/^-[a-zA-Z0-9]{2,}$/.test(text) && [...text.slice(1)].every((c) => PUSH_FLAGS.has(`-${c}`))) {
      if (text.includes("d")) deleting = true;
      continue;
    }
    return { undetermined: `the push option \`${text}\` is not one the guard reads` };
  }
  const refspecs = positionals.slice(1);
  const needsCurrent = () => {
    if (push.cdBefore) return { undetermined: "the directory changes before it, so its branch is unknown here" };
    return null;
  };
  if (!refspecs.length) {
    const unknown = needsCurrent();
    if (unknown) return unknown;
    const branch = pushDestination(push.dir);
    return branch ? { targets: [branch] } : { undetermined: "the branch has no configured push destination" };
  }
  const targets = [];
  for (const raw of refspecs) {
    const spec = raw.replace(/^\+/, "");
    let dst = spec;
    if (!deleting && spec.includes(":")) dst = spec.slice(spec.indexOf(":") + 1);
    else if (spec.startsWith(":")) dst = spec.slice(1);
    if (!dst) return { undetermined: `\`${raw}\` names no destination` };
    if (dst === "HEAD" || dst === "@") {
      const unknown = needsCurrent();
      if (unknown) return unknown;
      dst = currentBranch(push.dir);
      if (!dst) return { undetermined: "HEAD is detached" };
    }
    if (dst.startsWith("refs/heads/")) dst = dst.slice("refs/heads/".length);
    else if (dst.startsWith("refs/")) return { undetermined: `\`${raw}\` is not a branch` };
    targets.push(dst);
  }
  return { targets };
}

function checkPushes(event) {
  const command = event.tool_input && typeof event.tool_input.command === "string"
    ? event.tool_input.command : "";
  if (!/\bgit\b/.test(command) || !/\bpush\b/.test(command)) return 0;
  const cwd = typeof event.cwd === "string" && event.cwd ? event.cwd : process.cwd();
  const asks = [];
  for (const push of findPushes(command, cwd)) {
    const top = gitOut(push.dir || cwd, ["rev-parse", "--show-toplevel"]);
    if (!top) continue;
    const { globs, protectedEntries } = readPushGlobs(top);
    if (!globs.length && !protectedEntries.length) continue;
    const declared = [
      ...globs.map((glob) => `\`push:${glob}\``),
      ...protectedEntries.map((e) => `\`push-protected:${e.glob}${e.role ? `@${e.role}` : ""}\``),
    ].join(", ");
    const result = pushTargets(push);
    if (result.undetermined) {
      deny(
        `Keel push guard: keel/config.yaml limits push to ${declared}, and the `
          + `guard cannot tell which branch this push targets: ${result.undetermined}. `
          + `Name the branch, as ${EXPLICIT_FORM}.`
      );
      return 0;
    }
    const unlisted = result.targets.filter((branch) => !globs.some((glob) => globPattern(glob).test(branch)));
    const outside = [];
    for (const branch of unlisted) {
      const entry = protectedEntries.find((e) => globPattern(e.glob).test(branch));
      if (!entry) {
        outside.push(branch);
        continue;
      }
      if (entry.role) {
        const role = sessionRole(top);
        if (role !== entry.role) {
          deny(
            `Keel push guard: \`${branch}\` is protected for role ${entry.role}, and this `
              + `session is ${role ? `role ${role}` : "bound to no chat role"}; only an ${entry.role} `
              + "session may ask to push it."
          );
          return 0;
        }
      }
      asks.push(branch);
    }
    if (outside.length) {
      deny(
        `Keel push guard: this command pushes to ${outside.map((b) => `\`${b}\``).join(", ")}, `
          + `and keel/config.yaml limits push to ${declared}. Push a matching branch, `
          + "or ask the owner; the declaration is theirs to widen."
      );
      return 0;
    }
  }
  if (asks.length) {
    const mode = typeof event.permission_mode === "string" ? event.permission_mode : "";
    const branches = asks.map((b) => `\`${b}\``).join(", ");
    if (MODES_THAT_CANNOT_ASK.has(mode)) {
      deny(
        `Keel push guard: ${branches} is protected, so each push needs the user's `
          + `confirmation, and permission mode ${mode} cannot be relied on to ask. `
          + "Switch to a mode that asks, or let the user push it."
      );
      return 0;
    }
    ask(
      `Keel push guard: ${branches} is a protected branch (keel/config.yaml `
        + "push-protected). Confirm only if the user approves this one push; the next push asks again."
    );
  }
  return 0;
}

function main() {
  const input = readStdin();
  let event = {};
  try {
    event = JSON.parse(input || "{}");
  } catch {
    event = {};
  }
  const repo =
    typeof event.cwd === "string" && event.cwd ? event.cwd : process.cwd();

  // An active task keeps the guard it started under: hand off only while no
  // manifest exists. A copy that fails to run returns null, and this guard's
  // own decision follows.
  if (!fs.existsSync(path.join(repo, "keel", "guard.json"))) {
    const handed = handOff(__filename, input, 8000);
    if (handed !== null) return handed;
  }

  if (event.tool_name === "Bash") return checkPushes(event);

  const pathField = FILE_EDIT_TOOLS.get(event.tool_name);
  if (!pathField) return 0;

  // The repository is the guard's scope, so this boundary is settled before the
  // manifest is read at all. It needs only the event's cwd and target, so no
  // manifest state — absent, invalid, drifted, or completed — has anything to
  // say about a path outside it. Deciding it here rather than further down is
  // what stops a branch added to the manifest section from denying a file the
  // guard never protected; that ordering has already failed twice.
  const target = event.tool_input ? event.tool_input[pathField] : null;
  if (typeof target !== "string" || !target) return 0;
  const relative = repoRelative(repo, target);
  if (
    !relative
    || relative === ".."
    || relative.startsWith(`..${path.sep}`)
    || path.isAbsolute(relative)
  ) {
    return 0;
  }
  const candidate = relative.replace(/\\/g, "/");

  const manifestPath = path.join(repo, "keel", "guard.json");
  if (!fs.existsSync(manifestPath)) return 0;

  let manifest = null;
  try {
    manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  } catch {
    manifest = null;
  }
  if (!manifestShapeValid(manifest)) {
    deny(
      "Keel write guard: keel/guard.json is present but invalid, so file "
        + "edits fail closed. Run `keel guard clear`, then `keel gate "
        + "task-start` and `keel guard start` to reauthorize."
    );
    return 0;
  }
  const pointer = `${manifest.change}#${manifest.task}`;
  // Two states used to arrive at the same place, and they need different
  // answers. A task id absent from a live `tasks.md` is a parse miss the guard
  // must not guess about — see `taskIsChecked`. A change directory that is not
  // there at all is a fact: the manifest points at work that has been archived
  // or removed, and `keel guard status` already classifies it as drifted.
  //
  // Untreated, the archived case was wrong in both directions. A write outside
  // the stale Touch was denied by a message naming a task in an archived change
  // and telling the reader to reauthorize it, which cannot be done; a write
  // *inside* it passed silently, so an archived task went on granting write
  // authority. Denying here fixes both, and denying rather than allowing is
  // what stops `openspec archive` from quietly disabling the guard.
  const changeDir = path.join(repo, "openspec", "changes", manifest.change);
  if (!fs.existsSync(changeDir)) {
    deny(
      `Keel write guard: this manifest is stale — it guards ${pointer}, but `
        + `openspec/changes/${manifest.change} no longer exists, so the task it `
        + "names cannot be reauthorized and its Touch list authorizes nothing. "
        + "File edits fail closed. Run `keel guard clear`, then start the task "
        + "you are actually working on with `keel gate task-start`."
    );
    return 0;
  }
  // The record layer: the guarded change's own directory holds the records the
  // task produces — its checkbox, Evidence, and Review — not the product it
  // changes. `keel gate task-complete` already refuses to attribute this
  // directory as an outside-Touch failure, so denying it here made the guard
  // stop the one thing the completion gate is waiting for. Derived from the
  // manifest's existing `change` field, so no manifest shape changes.
  const recordPrefix = `openspec/changes/${manifest.change}/`;
  if (candidate.startsWith(recordPrefix)) return 0;

  for (const entry of manifest.authority) {
    // Same boundary: bytes under the guarded change's own directory are
    // records, and the capsule fingerprint — which carries no checkbox state
    // and no Evidence values — is what separates a record write from a
    // contract change. `keel guard status` and `keel gate task-complete`
    // compile the capsule and compare it; this hook cannot, and must not guess.
    if (entry.path.replace(/\\/g, "/").startsWith(recordPrefix)) continue;
    const file = path.join(repo, entry.path);
    let fresh = null;
    try {
      fresh = sha256(fs.readFileSync(file));
    } catch {
      fresh = null;
    }
    if (fresh !== entry.sha256) {
      deny(
        `Keel write guard: task authority drift detected for ${pointer} `
          + `(${entry.path} changed since guard start), so file edits fail `
          + "closed. Re-run `keel gate task-start` and `keel guard start` to "
          + "reauthorize, or `keel guard clear` to stop enforcement."
      );
      return 0;
    }
  }

  if (taskIsChecked(repo, manifest)) {
    deny(
      `Keel write guard: ${pointer} is checked complete, so it authorizes no `
        + `further product writes — ${candidate} is denied. Its own `
        + `${recordPrefix} records stay writable so the task can finish its `
        + "Evidence. Run `keel guard clear`, then authorize the next task "
        + "explicitly with `keel gate task-start`."
    );
    return 0;
  }

  if (pathAllowed(candidate, manifest.touch)) return 0;

  deny(
    `Keel write guard: ${candidate} is outside Touch for ${pointer}. `
      + `Touch allows: ${manifest.touch.join(", ")}. Stop and report an `
      + "Out-of-scope Need, update the task authority and reauthorize via "
      + "`keel gate task-start` and `keel guard start`, or run "
      + "`keel guard clear` to stop enforcement."
  );
  return 0;
}

process.exit(main());
