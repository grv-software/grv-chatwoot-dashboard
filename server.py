#!/usr/bin/env python3
"""
GRV SAC – servidor local com proxy para nxticket.com.br
Acesse: http://localhost:8765
"""
import http.server, urllib.request, urllib.parse, os, sys

PORT = 8765
TARGET = "https://nxticket.com.br"
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {self.command} {self.path} → {args[1] if len(args)>1 else ''}")

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            self._static()

    def _proxy(self):
        url = TARGET + self.path
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read()
                self.send_response(r.status)
                self.send_header("Content-Type", r.headers.get("Content-Type", "application/json"))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self.send_error(502, str(e))

    def _static(self):
        path = "/index.html" if self.path in ("/", "") else self.path
        filepath = os.path.join(DIR, path.lstrip("/"))
        if not os.path.isfile(filepath):
            self.send_error(404); return
        ext = filepath.rsplit(".", 1)[-1]
        ct = {"html": "text/html", "js": "text/javascript", "css": "text/css"}.get(ext, "application/octet-stream")
        with open(filepath, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", f"{ct}; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

if __name__ == "__main__":
    os.chdir(DIR)
    print(f"\n  GRV SAC Dashboard rodando em http://localhost:{PORT}\n  Ctrl+C para parar.\n")
    with http.server.HTTPServer(("", PORT), Handler) as srv:
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n  Servidor encerrado.")
