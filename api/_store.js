const STATE_KEY = "farewell_status";

function defaultStatus() {
  return { entry: false };
}

function adminKey() {
  return process.env.ADMIN_KEY || "logout2026";
}

function isAdmin(req) {
  return req.headers["x-admin-key"] === adminKey();
}

function kvConfig() {
  const url = process.env.KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
  const token =
    process.env.KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) {
    throw new Error("Vercel KV is not configured");
  }
  return { url, token };
}

async function kvCommand(command, ...args) {
  const { url, token } = kvConfig();
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify([command, ...args]),
  });

  if (!response.ok) {
    throw new Error(`KV command failed: ${response.status}`);
  }

  const data = await response.json();
  return data.result;
}

async function loadState() {
  return (await kvCommand("GET", STATE_KEY)) || {};
}

async function saveState(state) {
  await kvCommand("SET", STATE_KEY, state);
}

function sendJson(res, status, data) {
  res.status(status).json(data);
}

module.exports = {
  defaultStatus,
  isAdmin,
  loadState,
  saveState,
  sendJson,
};
