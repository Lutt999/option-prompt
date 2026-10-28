from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
from urllib.parse import urlparse

from config import SETTINGS


def reachable(host, port):
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except OSError:
        return False


def main():
    root = Path(__file__).resolve().parent
    url = urlparse(SETTINGS['whisper_url'])
    host, port = url.hostname, url.port or 80
    server = None
    app = None
    try:
        if not reachable(host, port):
            if host not in ('localhost', '127.0.0.1', '::1'):
                raise SystemExit('The configured speech server is unavailable.')
            executable = shutil.which('whisper-server')
            model = Path(SETTINGS['whisper_model']).expanduser()
            if not executable or not model.is_file():
                raise SystemExit('Install whisper-cpp and download the model first; see README.md.')
            command = [executable, '-m', str(model), '-l', SETTINGS['language'], '--host', host, '--port', str(port)]
            if SETTINGS['language'] == 'zh':
                command += ['--prompt', '以下是普通话的句子，使用简体中文。']
            server = subprocess.Popen(command)
            deadline = time.monotonic() + 90
            while not reachable(host, port):
                if server.poll() is not None or time.monotonic() > deadline:
                    raise SystemExit('Speech server did not become ready.')
                time.sleep(0.3)
        app = subprocess.Popen([sys.executable, '-u', str(root / 'dictate.py')])
        raise SystemExit(app.wait())
    except KeyboardInterrupt:
        pass
    finally:
        for process in [app, server]:
            if process is not None and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == '__main__':
    main()
