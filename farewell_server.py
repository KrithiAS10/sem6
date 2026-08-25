from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json
import socket
import threading
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent
STATE_FILE = ROOT / "farewell_status.json"
ADMIN_KEY = "logout2026"
LOCK = threading.Lock()
CHROME_DEVTOOLS_PROBE = "/.well-known/appspecific/com.chrome.devtools.json"


def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def default_status():
    return {"entry": False}


def get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"


class FarewellHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def is_admin(self):
        return self.headers.get("X-Admin-Key", "") == ADMIN_KEY

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == CHROME_DEVTOOLS_PROBE:
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        if parsed.path == "/api/status":
            usn = parse_qs(parsed.query).get("usn", [""])[0].strip().upper()
            if not usn:
                self.send_json({"error": "Missing USN"}, 400)
                return
            with LOCK:
                status = load_state().get(usn, default_status())
            self.send_json({"usn": usn, **default_status(), **status})
            return

        if parsed.path == "/api/all":
            if not self.is_admin():
                self.send_json({"error": "Admin access required"}, 403)
                return
            with LOCK:
                state = load_state()
            self.send_json(state)
            return

        if parsed.path == "/api/network":
            host = get_lan_ip()
            port = self.server.server_port
            self.send_json({"url": f"http://{host}:{port}/fareWell.html"})
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/api/mark":
            self.send_json({"error": "Not found"}, 404)
            return

        if not self.is_admin():
            self.send_json({"error": "Admin access required"}, 403)
            return

        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return

        usn = str(payload.get("usn", "")).strip().upper()
        field = str(payload.get("field", "")).strip().lower()
        value = bool(payload.get("value"))
        if not usn or field != "entry":
            self.send_json({"error": "Invalid request"}, 400)
            return

        with LOCK:
            state = load_state()
            current = {**default_status(), **state.get(usn, {})}
            current[field] = value
            state[usn] = current
            save_state(state)

        self.send_json({"usn": usn, **current})


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", 8000), FarewellHandler)
    lan_url = f"http://{get_lan_ip()}:8000/index.html"
    print("Farewell server running at http://localhost:8000/index.html")
    print(f"Phone/scanner URL: {lan_url}")
    print("Admin page: http://localhost:8000/index.html?admin=1")
    server.serve_forever()
