const { defaultStatus, isAdmin, loadState, saveState, sendJson } = require("./_store");

module.exports = async function handler(req, res) {
  if (req.method !== "POST") {
    return sendJson(res, 405, { error: "Method not allowed" });
  }

  if (!isAdmin(req)) {
    return sendJson(res, 403, { error: "Admin access required" });
  }

  const usn = String(req.body?.usn || "").trim().toUpperCase();
  const field = String(req.body?.field || "").trim().toLowerCase();
  const value = Boolean(req.body?.value);
  if (!usn || field !== "entry") {
    return sendJson(res, 400, { error: "Invalid request" });
  }

  try {
    const state = await loadState();
    const current = { ...defaultStatus(), ...(state[usn] || {}) };
    current.entry = value;
    state[usn] = current;
    await saveState(state);
    return sendJson(res, 200, { usn, ...current });
  } catch (error) {
    return sendJson(res, 500, { error: error.message || "Could not update status" });
  }
};
