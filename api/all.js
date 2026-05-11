const { isAdmin, loadState, sendJson } = require("./_store");

module.exports = async function handler(req, res) {
  if (req.method !== "GET") {
    return sendJson(res, 405, { error: "Method not allowed" });
  }

  if (!isAdmin(req)) {
    return sendJson(res, 403, { error: "Admin access required" });
  }

  try {
    return sendJson(res, 200, await loadState());
  } catch (error) {
    return sendJson(res, 500, { error: error.message || "Status API unavailable" });
  }
};
