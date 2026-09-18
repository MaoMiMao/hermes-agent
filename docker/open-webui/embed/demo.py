"""Serve only the local iframe verification page, without credentials or signing."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != '/':
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(Path(__file__).with_name('demo.html').read_bytes())

print('Open http://localhost:8088/')
ThreadingHTTPServer(('127.0.0.1', 8088), Handler).serve_forever()
