"use strict";

// Loop guards (issue #187, design D11). Agents that answer each other can keep
// answering for ever, and a woken session that posts can wake another. Two
// checks stop that without a person watching:
//
//   rate       a role other than `owner` may post at most `limits.rate`
//              records per `limits.window_minutes` across the project
//              (default 20 per 10).
//   ping-pong  when the last `limits.pingpong` messages of a group (default 8)
//              alternate between the same two roles other than `owner`, the
//              next post there by either is refused, and Keel calls the owner
//              with one `system` record. Any other member's post clears it.
//
// Both refuse by name, so an agent reading its error knows what stopped it.

const { loadChatConfig } = require("./config");

const DEFAULTS = { rate: 20, window_minutes: 10, pingpong: 8 };
const SYSTEM_SENDER = "keel";

function positiveInteger(value, fallback) {
  return Number.isInteger(value) && value > 0 ? value : fallback;
}

function limitsFor(where) {
  const { config } = loadChatConfig(where.worktree);
  const limits = (config && typeof config.limits === "object" && config.limits) || {};
  return {
    rate: positiveInteger(limits.rate, DEFAULTS.rate),
    window_minutes: positiveInteger(limits.window_minutes, DEFAULTS.window_minutes),
    pingpong: positiveInteger(limits.pingpong, DEFAULTS.pingpong),
  };
}

// The two roles a group's recent messages alternate between, or null.
function pingPongPair(records, length) {
  const messages = records.filter((record) => record.kind === "message").slice(-length);
  if (messages.length < length) return null;
  const pair = [messages[0].from, messages[1].from];
  if (pair[0] === pair[1] || pair.includes("owner")) return null;
  for (let index = 0; index < messages.length; index += 1) {
    if (messages[index].from !== pair[index % 2]) return null;
  }
  return pair;
}

function postedSince(store, where, role, since) {
  let count = 0;
  for (const group of store.listGroupNames(where)) {
    for (const record of store.readLog(where, group)) {
      if (record.from !== role || (record.kind !== "message" && record.kind !== "todo")) continue;
      const time = Date.parse(record.created);
      if (!Number.isNaN(time) && time >= since) count += 1;
    }
  }
  return count;
}

// Throws the store's error when `role` may not post to `group` now.
function checkPost(store, where, role, group, records) {
  if (role === "owner") return;
  const limits = limitsFor(where);
  const pair = pingPongPair(records, limits.pingpong);
  if (pair && pair.includes(role)) {
    const last = records[records.length - 1];
    if (!(last && last.kind === "system" && last.from === SYSTEM_SENDER)) {
      store.writeRecord(where, {
        group,
        kind: "system",
        from: SYSTEM_SENDER,
        mentions: ["owner"],
        text: `@owner ${pair[0]} and ${pair[1]} have answered each other ${limits.pingpong} times in a row in ${group}; `
          + "the loop guard holds their next posts here until someone else posts.",
      });
    }
    throw new store.ChatError(
      `The loop guard stopped this post: ${pair[0]} and ${pair[1]} have alternated the last ${limits.pingpong} `
        + `messages in ${group}. The owner has been called; any other member's post clears it.`
    );
  }
  const since = Date.now() - limits.window_minutes * 60 * 1000;
  const posted = postedSince(store, where, role, since);
  if (posted >= limits.rate) {
    throw new store.ChatError(
      `The loop guard stopped this post: ${role} posted ${posted} records in the last ${limits.window_minutes} `
        + `minutes, the limit set by limits.rate in keel/chat.json (default ${DEFAULTS.rate}).`
    );
  }
}

module.exports = {
  DEFAULTS,
  SYSTEM_SENDER,
  checkPost,
};
