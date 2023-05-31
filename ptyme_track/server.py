import datetime
import json
import uuid
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from ptyme_track.ptyme_env import SECRET_PATH, SERVER_ID, SERVER_URL
from ptyme_track.secret import get_secret
from ptyme_track.signature import signature_from_time
from ptyme_track.signed_time import SignedTime
from ptyme_track.validation import validate_signed_time_given_secret


class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        # get the current time and sign the request
        signed_time = json.dumps(asdict(sign_time())).encode("utf-8")
        self.wfile.write(signed_time)
        return

    def do_POST(self) -> None:
        content_length = int(self.headers["Content-Length"])
        if content_length > 1024:
            # too big, go away
            return
        post_data = self.rfile.read(content_length)
        json_data = json.loads(post_data)
        try:
            incoming_signed_time = SignedTime(**json_data)
            incoming_signed_time.dt  # validate
        except ValueError:
            signed_time = None
            self.send_response(400)
        else:
            self.send_response(200)
            # get the current time and sign the request
            signed_time = json.dumps(validate_signed_time(incoming_signed_time)).encode("utf-8")

        self.send_header("Content-type", "application/json")
        self.end_headers()
        if signed_time:
            self.wfile.write(signed_time)
        return


def validate_signed_time(incoming_signed_time: SignedTime) -> dict:
    return validate_signed_time_given_secret(get_secret(), incoming_signed_time)


def sign_time() -> SignedTime:
    # sign the current time
    cur_time = datetime.datetime.utcnow()
    time_as_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
    hash_sig = _signature_from_time(time_as_str)
    return SignedTime(SERVER_ID, time_as_str, hash_sig)


def _signature_from_time(time_as_str: str) -> str:
    return signature_from_time(get_secret(), time_as_str)


def run_forever(server_class=HTTPServer, handler_class=MyRequestHandler) -> None:
    server_host = urlparse(SERVER_URL).hostname
    server_port = urlparse(SERVER_URL).port
    httpd = server_class((server_host, server_port), handler_class)
    httpd.serve_forever()


def generate_secret() -> None:
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
