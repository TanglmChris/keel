"use strict";

const fs = require("fs");
const path = require("path");

// The closed vocabulary of actions a repository may standing-authorize. It is
// closed so an entry outside it can be reported by name: a free-form grant
// cannot tell a typo from a decision, and silently dropping one leaves the
// author believing they authorized something they did not.
const STANDING_AUTHORIZATION_ACTIONS = ["commit", "push", "release", "archive"];

const CONFIG_RELATIVE_PATH = path.join("keel", "config.yaml");

// The declaration shares keel/config.yaml with fast_check, so the reader stays
// line-oriented rather than pulling in a YAML dependency for a format Keel
// controls and keeps flat on purpose.
function readStandingAuthorization(repo) {
  const configPath = path.join(repo, "keel", "config.yaml");
  const declared = [];
  const unknown = [];
  if (!fs.existsSync(configPath)) return { declared, unknown };
  let inBlock = false;
  for (const line of fs.readFileSync(configPath, "utf8").split(/\r?\n/)) {
    if (/^\s*#/.test(line)) continue;
    if (/^authorize\s*:\s*$/.test(line)) {
      inBlock = true;
      continue;
    }
    if (!inBlock) continue;
    if (line.trim() === "") continue;
    const entry = line.match(/^\s+-\s*(\S+)\s*$/);
    // Anything that is not a list item closes the block; the next top-level
    // key belongs to the rest of the file.
    if (!entry) break;
    if (STANDING_AUTHORIZATION_ACTIONS.includes(entry[1])) declared.push(entry[1]);
    else unknown.push(entry[1]);
  }
  // Fail closed. A declaration Keel cannot fully read authorizes nothing,
  // because the alternative is granting the entries beside a typo while the
  // author believes they granted the typo too.
  if (unknown.length > 0) return { declared: [], unknown };
  return { declared, unknown };
}

module.exports = {
  CONFIG_RELATIVE_PATH,
  STANDING_AUTHORIZATION_ACTIONS,
  readStandingAuthorization,
};
