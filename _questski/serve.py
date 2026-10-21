"""Serve Tibia Questski on http://localhost:8080  (usage: python serve.py [port])"""
import functools
import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".js": "text/javascript", ".json": "application/json", ".svg": "image/svg+xml"}

    def end_headers(self):
        # always revalidate, so a rebuild or an edited file shows up on a normal refresh
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    handler = functools.partial(Handler, directory=SITE)
    with http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler) as httpd:
        print(f"Tibia Questski a correr em http://localhost:{PORT}  (Ctrl+C para parar)")
        httpd.serve_forever()
