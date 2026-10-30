"""Real loopback HTTP and worker-process demonstration; no screenshots fabricated."""
from contextlib import redirect_stdout
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from werkzeug.serving import make_server
from app import create_app


def main():
    with tempfile.TemporaryDirectory() as directory:
        server = make_server('127.0.0.1', 0, create_app(directory))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f'http://127.0.0.1:{server.server_port}'
        env = dict(os.environ, LAB2_DATA_DIR=directory)
        def request(method, path, body=None):
            data = None if body is None else json.dumps(body).encode()
            req = Request(base + path, data=data, method=method, headers={'Content-Type': 'application/json'})
            try:
                response = urlopen(req, timeout=5)
            except HTTPError as error:
                response = error
            value = json.load(response)
            print(method, path, '-> HTTP', response.status, json.dumps(value), flush=True)
            return response.status, value
        print('Actual loopback experiment', datetime.now(timezone.utc).isoformat(), flush=True)
        try:
            assert request('GET', '/time')[0] == 200
            assert request('POST', '/echo', {'message': 'Hello queue'})[0] == 200
            assert request('POST', '/echo', {'message': 3})[0] == 400
            assert request('GET', '/jobs/unknown')[0] == 404
            jobs = []
            for i in range(3):
                code, value = request('POST', '/jobs', {'message': f'Hello queue {i}'})
                assert code == 202
                jobs.append(value['job_id'])
                assert request('GET', '/jobs/' + jobs[-1])[1]['status'] == 'queued'
            print('Worker is not running; waiting 30 seconds', flush=True)
            time.sleep(30)
            for job in jobs:
                assert request('GET', '/jobs/' + job)[1]['status'] == 'queued'
            print('Starting an independent worker process', flush=True)
            worker = subprocess.Popen([sys.executable, 'worker.py'], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                deadline = time.monotonic() + 10
                for job in jobs:
                    while True:
                        _, record = request('GET', '/jobs/' + job)
                        if record['status'] == 'done':
                            assert record['result']['word_count'] == 3
                            break
                        assert time.monotonic() < deadline
                        time.sleep(.1)
            finally:
                worker.terminate()
                output, _ = worker.communicate(timeout=5)
                print('Worker log:\n' + output)
                assert worker.returncode == 0
            print('PASS: three tasks persisted for 30 seconds and completed after worker start; SIGTERM exit 0')
        finally:
            server.shutdown()
            thread.join()


if __name__ == '__main__':
    main()
