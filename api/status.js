const { defaultStatus, loadState, sendJson } = require("./_store");

module.exports = async function handler(req, res) {
  if (req.method !== "GET") {
    return sendJson(res, 405, { error: "Method not allowed" });
  }

  const usn = String(req.query.usn || "").trim().toUpperCase();
  if (!usn) {
    return sendJson(res, 400, { error: "Missing USN" });
  }

  try {
    const state = await loadState();
    const status = state[usn] || defaultStatus();
    return sendJson(res, 200, { usn, ...defaultStatus(), ...status });
  } catch (error) {
    return sendJson(res, 500, { error: error.message || "Status API unavailable" });
  }
};
