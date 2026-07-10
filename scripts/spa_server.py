import http.server
import os

DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIST_DIR, **kwargs)

    def do_GET(self):
        requested = self.translate_path(self.path)
        if not os.path.isfile(requested):
            self.path = "/index.html"
        return super().do_GET()


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", 3000), SPAHandler)
    server.serve_forever()
