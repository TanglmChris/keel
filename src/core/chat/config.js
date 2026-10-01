"use strict";

// Per-project chat settings (issue #187, design D13): a committed
// `keel/chat.json`, kept apart from `keel/config.yaml` because that reader is
// flat on purpose and the chat needs nested maps (Slack user -> role, group ->
// channel). An absent file is local chat with no Slack and no archive. A file
// that does not parse turns Slack and archive off and says why; local chat
// keeps working, because a typo in an integration setting must not silence
// the sessions that never used it.

const fs = require("fs");
const path = require("path");

const CHAT_CONFIG_RELATIVE_PATH = path.join("keel", "chat.json");

function loadChatConfig(worktree) {
  const file = path.join(worktree, CHAT_CONFIG_RELATIVE_PATH);
  let text;
  try {
    text = fs.readFileSync(file, "utf8");
  } catch {
    return { config: {}, error: null, file };
  }
  try {
    const parsed = JSON.parse(text);
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
      return { config: {}, error: `${CHAT_CONFIG_RELATIVE_PATH} is not a JSON object.`, file };
    }
    return { config: parsed, error: null, file };
  } catch (error) {
    return { config: {}, error: `${CHAT_CONFIG_RELATIVE_PATH} does not parse: ${error.message}`, file };
  }
}

module.exports = {
  CHAT_CONFIG_RELATIVE_PATH,
  loadChatConfig,
};
