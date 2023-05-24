import datetime
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid

SERVER_ID = str(uuid.uuid4())


class MyRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        # get the current time and sign the request
        cur_time = datetime.datetime.utcnow()
        signed_time = self.sign_time(cur_time)
        self.wfile.write(bytes(signed_time, "utf8"))
        return

    def sign_time(self, cur_time):
        # sign the current time
        time_as_str = cur_time.strftime("%Y-%m-%d %H:%M:%S")
        hash_sig = hashlib.md5(time_as_str.encode("ascii")).hexdigest()
        return json.dumps({"time": time_as_str, "sig": hash_sig})


def run(server_class=HTTPServer, handler_class=MyRequestHandler):
    server_address = ("", 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


run()
