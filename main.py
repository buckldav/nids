from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import unquote
import pathlib
import os
import subprocess
import smtplib
from email.message import EmailMessage
from concurrent.futures import ThreadPoolExecutor
import logging
import ssl

email_pool = ThreadPoolExecutor(max_workers=2)


# Deliberately simple teaching rules—not a production detection system.
SUSPICIOUS_MARKERS = ["bad"]  # ("../", "<script", "union select")

PUBLIC_DIR = "./public"


def email_alert(msg: str) -> None:
    sender = os.environ["FROM"]  # full Gmail address
    recipient = os.environ["TO"]
    password = os.environ["PASSWORD"]  # Google App Password

    email = EmailMessage()
    email["Subject"] = "Alert"
    email["From"] = sender
    email["To"] = recipient
    email.set_content(msg)

    context = ssl.create_default_context()

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()
        server.login(sender, password)
        server.send_message(email)


def send_alert_safely(msg: str) -> None:
    try:
        email_alert(msg)
    except Exception:
        logging.exception("Failed to send alert email")


class MonitorHandler(BaseHTTPRequestHandler):
    def _res_file(self, full_path: str):
        self.send_response(200)
        self.end_headers()
        # cat the file and write to the response stream
        res = subprocess.run(["sudo", "cat", full_path], capture_output=True, text=True)
        self.wfile.write(res.stdout.encode())

    def _res_dir(self, full_path: str):
        self.send_response(200)
        self.end_headers()
        # TODO: ls the directory write to the response stream

    def _get_file_or_dir(self, path: str):
        """
        A very insecure way to get and serve a file or directory.
        """

        path = path if not path.startswith("/") or len(path) == 0 else path[1:]
        abs_path = str(pathlib.Path(os.getcwd()).joinpath(PUBLIC_DIR).joinpath(path))
        print(abs_path)
        if os.path.isfile(abs_path):
            self._res_file(abs_path)
        elif os.path.isdir(abs_path):
            # check if there is an index.html in the directory
            index_paths = ["index.html", "index.htm"]
            is_index = False
            for p in index_paths:
                p2 = str(pathlib.Path(abs_path, p))
                if os.path.isfile(p2):
                    self._res_file(p2)
                    is_index = True
                    break
            # otherwise print the directory
            if not is_index:
                self._res_dir(abs_path)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Path does not exist.")

    def do_GET(self):
        path = unquote(self.path)
        print(f"GET  {self.client_address[0]} {self.command} {path}")

        matches = [marker for marker in SUSPICIOUS_MARKERS if marker in path.lower()]
        if matches:
            print(f"ALERT: matched demo rule(s): {', '.join(matches)}")
            email_pool.submit(send_alert_safely, "oof")

        self._get_file_or_dir(path)

    def do_POST(self):
        path = unquote(self.path)
        print(f"POST {self.client_address[0]} {self.command} {path}")

        matches = [marker for marker in SUSPICIOUS_MARKERS if marker in path.lower()]
        if matches:
            print(f"ALERT: matched demo rule(s): {', '.join(matches)}")

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Demo server OK\n")

    def log_message(self, format, *args):
        pass  # Keep the output focused on the monitor


try:
    print("Monitoring HTTP requests at http://127.0.0.1:8000")
    HTTPServer(("127.0.0.1", 8000), MonitorHandler).serve_forever()
except KeyboardInterrupt:
    print("\nStopped.")
