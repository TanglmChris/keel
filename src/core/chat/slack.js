"use strict";

// The Slack Web API client the bridge uses (issue #187, design D15–D17). It
// uses Node's built-in `fetch`, so the bridge adds no dependency.
//
// Write methods take a JSON body; read methods and connection setup take a
// form body, which every Web API method accepts. `KEEL_SLACK_API_BASE` points
// the client at a test server. A token is sent only in the Authorization
// header and is never part of an error message.

const DEFAULT_BASE = "https://slack.com/api";
const FORM_METHODS = new Set([
  "auth.test",
  "apps.connections.open",
  "conversations.history",
  "conversations.replies",
]);

class SlackError extends Error {
  constructor(method, error, { retryAfter = null, status = null } = {}) {
    super(`Slack ${method} failed: ${error}${status ? ` (HTTP ${status})` : ""}`);
    this.method = method;
    this.error = error;
    this.retryAfter = retryAfter;
    this.status = status;
  }
}

function apiBase() {
  return (process.env.KEEL_SLACK_API_BASE || DEFAULT_BASE).replace(/\/+$/, "");
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function call(method, params, token) {
  const headers = { Authorization: `Bearer ${token}` };
  let body;
  if (FORM_METHODS.has(method)) {
    const form = new URLSearchParams();
    for (const [key, value] of Object.entries(params || {})) {
      if (value === undefined || value === null) continue;
      form.set(key, typeof value === "object" ? JSON.stringify(value) : String(value));
    }
    headers["Content-Type"] = "application/x-www-form-urlencoded";
    body = form.toString();
  } else {
    headers["Content-Type"] = "application/json; charset=utf-8";
    body = JSON.stringify(params || {});
  }
  let response;
  try {
    response = await fetch(`${apiBase()}/${method}`, { method: "POST", headers, body });
  } catch (error) {
    throw new SlackError(method, `network error: ${error.cause ? error.cause.code || error.cause.message : error.message}`);
  }
  if (response.status === 429) {
    const retryAfter = Number(response.headers.get("retry-after")) || 1;
    throw new SlackError(method, "ratelimited", { retryAfter, status: 429 });
  }
  let parsed = null;
  try {
    parsed = await response.json();
  } catch {
    throw new SlackError(method, "response was not JSON", { status: response.status });
  }
  if (!parsed || parsed.ok !== true) {
    throw new SlackError(method, (parsed && parsed.error) || "unknown_error", { status: response.status });
  }
  return parsed;
}

// Waits out a 429 for as long as Slack asks; other failures retry with
// backoff up to `attempts` times and then throw.
async function callWithRetry(method, params, token, { attempts = 4, onWait = null } = {}) {
  let failures = 0;
  let backoff = 1000;
  for (;;) {
    try {
      return await call(method, params, token);
    } catch (error) {
      if (!(error instanceof SlackError)) throw error;
      if (error.retryAfter !== null) {
        if (onWait) onWait(method, error.retryAfter);
        await sleep(error.retryAfter * 1000);
        continue;
      }
      failures += 1;
      if (failures >= attempts || ["invalid_auth", "not_authed", "channel_not_found", "missing_scope", "account_inactive"].includes(error.error)) {
        throw error;
      }
      await sleep(backoff);
      backoff = Math.min(backoff * 2, 5 * 60 * 1000);
    }
  }
}

module.exports = {
  SlackError,
  call,
  callWithRetry,
  sleep,
};
