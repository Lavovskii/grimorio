"""Serve o Grimório e o Questski em http://localhost:8080 (Questski em /quests/) sem o XAMPP  (usage: python serve.py [port])
Sem PHP: os preços do Market do Grimório (api/market.php) só funcionam com o Apache do XAMPP."""
import functools
import http.server
import os
import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # a raiz do repositório (grimorio/)


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
        print(f"Grimório em http://localhost:{PORT}/ e Questski em http://localhost:{PORT}/quests/  (Ctrl+C para parar)")
        httpd.serve_forever()
