"use strict";

// Loop guards (issue #187, design D11). Agents that answer each other can keep
// answering for ever, and a woken session that posts can wake another. Two
// checks stop that without a person watching:
//
//   rate       a role other than `owner` may post at most `limits.rate`
//              records per `limits.window_minutes` across the project
//              (default 20 per 10).
//   ping-pong  when the last `limits.pingpong` messages of a group (default 8)
//              since its latest override alternate between the same two
//              roles other than `owner`, and the first of them is within
//              `limits.pingpong_minutes` (default 10), the next post there by
//              either is refused (#297 D1). A first refusal only names
//              `--not-a-loop "<why>"`, which lets the poster through once;
//              a repeat after an override calls the owner with one `system`
//              record (D2). The owner's post clears it, or in a group of more
//              than two, any other member's.
//
// Both refuse by name, so an agent reading its error knows what stopped it.

const { loadChatConfig } = require("./config");

const DEFAULTS = { rate: 20, window_minutes: 10, pingpong: 8, pingpong_minutes: 10 };
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
    pingpong_minutes: positiveInteger(limits.pingpong_minutes, DEFAULTS.pingpong_minutes),
  };
}

// The two roles a group's recent messages alternate between, or null: only
// messages after the latest override count, and only a run whose first
// message is within `minutes` of now (#297 D1).
function pingPongPair(records, length, minutes) {
  const override = records.map((record) => Boolean(record.not_a_loop)).lastIndexOf(true);
  const messages = records.slice(override + 1).filter((record) => record.kind === "message").slice(-length);
  if (messages.length < length) return null;
  const first = Date.parse(messages[0].created || "");
  if (Number.isNaN(first) || Date.now() - first > minutes * 60 * 1000) return null;
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

// Escalated once the group's latest override or call to the owner has not
// been followed by an owner message (#297 D2).
function escalated(records) {
  for (let index = records.length - 1; index >= 0; index -= 1) {
    const record = records[index];
    if (record.from === "owner" && record.kind === "message") return false;
    if (record.not_a_loop || (record.kind === "system" && record.from === SYSTEM_SENDER)) return true;
  }
  return false;
}

// Throws the store's error when `role` may not post to `group` now. Returns
// whether `notALoop` let the post through, so the caller records the reason.
function checkPost(store, where, role, group, records, notALoop = null) {
  if (role === "owner") return { overridden: false };
  const limits = limitsFor(where);
  const pair = pingPongPair(records, limits.pingpong, limits.pingpong_minutes);
  let overridden = false;
  if (pair && pair.includes(role) && !escalated(records)) {
    if (!notALoop) {
      throw new store.ChatError(
        `The loop guard stopped this post: ${pair[0]} and ${pair[1]} have alternated the last ${limits.pingpong} `
          + `messages in ${group} within ${limits.pingpong_minutes} minutes. If this is ordinary request and reply, `
          + "post again with `--not-a-loop \"<why>\"`; if it trips again, the owner is called."
      );
    }
    overridden = true;
  } else if (pair && pair.includes(role)) {
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
    const clears = store.isDirect(group) ? "a post by the owner clears it" : "a post by the owner or another member clears it";
    throw new store.ChatError(
      `The loop guard stopped this post: ${pair[0]} and ${pair[1]} have alternated the last ${limits.pingpong} `
        + `messages in ${group} again after an override. The owner has been called; ${clears}, and --not-a-loop no longer applies.`
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
  return { overridden };
}

module.exports = {
  DEFAULTS,
  SYSTEM_SENDER,
  checkPost,
};
