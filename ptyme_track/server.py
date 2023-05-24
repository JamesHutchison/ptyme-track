import datetime
import hashlib
import json
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from genericpath import exists

from ptyme_track.ptyme_env import SECRET, SECRET_PATH, SERVER_ID, SERVER_URL

secret_path = Path(SECRET_PATH)

if secret_path.exists():
    SECRET = secret_path.read_text().strip()  # noqa: F811


class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # get the current time and sign the request
        signed_time = json.dumps(sign_time()).encode("utf-8")
        self.wfile.write(signed_time)
        return


def sign_time():
    # sign the current time
    cur_time = datetime.datetime.utcnow()
    time_as_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
    hash_str = SECRET + time_as_str
    hash_sig = hashlib.sha256(hash_str.encode("utf-8")).hexdigest()
    return {"server_id": SERVER_ID, "time": time_as_str, "sig": hash_sig}


def run_forever(server_class=HTTPServer, handler_class=MyRequestHandler) -> None:
    server_host = urlparse(SERVER_URL).hostname
    server_port = urlparse(SERVER_URL).port
    httpd = server_class((server_host, server_port), handler_class)
    httpd.serve_forever()


def generate_secret():
    with open(SECRET_PATH, "w") as f:
        f.write(str(uuid.uuid4()))
    git_ignore = Path(".gitignore")
    if git_ignore.exists():
        contents = git_ignore.read_text()
        if SECRET_PATH not in contents:
            to_write = contents + "\n# ptyme server secret\n" + SECRET_PATH
            if contents.endswith("\n"):
                to_write += "\n"
            git_ignore.write_text(to_write)


if __name__ == "__main__":
    run_forever()
