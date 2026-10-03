import json, time, random
from http.server import BaseHTTPRequestHandler, HTTPServer
from bot import PoolChatter

SESSIONS = {}

class H(BaseHTTPRequestHandler):
    def serve_file(self, path, ctype):
        with open(path, "rb") as f: body = f.read()
        self.send_response(200); self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body))); self.end_headers()
        self.wfile.write(body)
    def do_GET(self):
        if self.path in ("/", "/index.html"): return self.serve_file("index.html", "text/html")
        self.send_response(404); self.end_headers()
    def do_POST(self):
        if self.path != "/api/chat": self.send_response(404); self.end_headers(); return
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        sid = data.get("session", "anon")
        bot = SESSIONS.get(sid) or PoolChatter(seed=random.randint(0, 999999))
        SESSIONS[sid] = bot
        reply = bot.reply(data.get("message", ""))
        time.sleep(min(0.4 + len(reply) * 0.02, 2.0))  
        body = json.dumps({"reply": reply}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body))); self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    print(f"PoolChatter on http://localhost:{port}")
    HTTPServer(("0.0.0.0", port), H).serve_forever()
