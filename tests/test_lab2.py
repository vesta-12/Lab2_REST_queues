import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from uuid import uuid4, UUID

import pytest

from app import create_app
from queue_storage import QueueStorage
from worker import Worker, analyze

METRICS = {}


@pytest.fixture
def store(tmp_path):
    return QueueStorage(tmp_path / 'queue')


@pytest.fixture
def client(store):
    return create_app(store.root).test_client()


def drain(store):
    worker = Worker(store)
    with store.worker_lock():
        store.recover()
        while worker.process_one():
            pass


def test_time(client):
    from datetime import datetime, timezone
    response = client.get('/time')
    assert response.status_code == 200
    timestamp = datetime.fromisoformat(response.json['server_time'])
    assert abs((datetime.now(timezone.utc) - timestamp).total_seconds()) < 2


def test_echo(client):
    assert client.post('/echo', json={'message': ' Hello мир '}).json == {'message': ' Hello мир '}


@pytest.mark.parametrize('endpoint', ['/echo', '/jobs'])
@pytest.mark.parametrize('body', [{}, {'message': 3}, {'message': None}, {'message': True},
                                   {'message': ''}, {'message': '   '}, [], None,
                                   {'message': 'ok', 'extra': 1}])
def test_invalid_body(client, endpoint, body):
    response = client.post(endpoint, data=json.dumps(body), content_type='application/json')
    assert response.status_code == 400
    assert isinstance(response.json['error'], str)


@pytest.mark.parametrize('endpoint', ['/echo', '/jobs'])
def test_invalid_json(client, endpoint):
    for kwargs in ({}, {'data': '{', 'content_type': 'application/json'},
                   {'data': '{"message":"ok"}', 'content_type': 'text/plain'}):
        assert client.post(endpoint, **kwargs).status_code == 400


def test_submit(client):
    response = client.post('/jobs', json={'message': 'hello'})
    assert response.status_code == 202
    assert UUID(response.json['job_id']).version == 4
    assert response.json['status'] == 'queued'


def test_lifecycle(client, store):
    job = client.post('/jobs', json={'message': 'Hello queue'}).json['job_id']
    assert client.get('/jobs/' + job).json['status'] == 'queued'
    with store.worker_lock():
        record = store.claim()
        assert client.get('/jobs/' + job).json['status'] == 'processing'
        store.finish(record, result=analyze(record['payload']['message']))
    result = client.get('/jobs/' + job).json
    assert result['status'] == 'done'
    assert result['result'] == {'uppercase': 'HELLO QUEUE', 'character_count': 11, 'word_count': 2}
    assert not list((store.root / 'processing').glob('*.json'))


def test_unknown(client, tmp_path):
    for job in (str(uuid4()), 'unknown', '..', 'A' * 36):
        response = client.get('/jobs/' + job)
        assert response.status_code == 404
        assert 'error' in response.json
    assert client.get('/jobs/../../etc/passwd').status_code == 404


def test_limits(client):
    for message, code in [('a', 202), ('Я' * 4096, 202), ('x' * 4097, 400)]:
        assert client.post('/jobs', json={'message': message}).status_code == code
    assert client.post('/echo', json={'message': 'x' * 4096}).status_code == 200
    assert client.post('/jobs', data='x' * 32769, content_type='application/json').status_code == 413


def test_storage_error(client, monkeypatch):
    def fail(*_):
        raise OSError('private path should not leak')
    monkeypatch.setattr(QueueStorage, 'submit', fail)
    response = client.post('/jobs', json={'message': 'test'})
    assert response.status_code == 503
    assert 'private' not in response.get_data(as_text=True)


def test_stopped_worker_persistence(client, store):
    jobs = [client.post('/jobs', json={'message': f'Job {i}'}).json['job_id'] for i in range(10)]
    started = time.perf_counter()
    time.sleep(30)
    reopened = QueueStorage(store.root)
    for i, job in enumerate(jobs):
        assert reopened.get(job)['status'] == 'queued'
        assert reopened.get(job)['payload']['message'] == f'Job {i}'
    METRICS['worker_absent_seconds'] = time.perf_counter() - started
    started = time.perf_counter()
    drain(reopened)
    elapsed = time.perf_counter() - started
    assert elapsed < 10
    for i, job in enumerate(jobs):
        assert reopened.get(job)['result'] == analyze(f'Job {i}')
        assert reopened.get(job)['status'] == 'done'
    METRICS.update(resumed_jobs=10, resumed_seconds=elapsed)


def test_recovery(store):
    job = store.submit('Recover me')['job_id']
    # A real child process is killed after claiming; OS releases both locks.
    code = """
import sys,time
from queue_storage import QueueStorage
s=QueueStorage(sys.argv[1])
with s.worker_lock():
 s.claim()
 print('claimed',flush=True)
 time.sleep(60)
"""
    child = subprocess.Popen([sys.executable, '-c', code, str(store.root)], stdout=subprocess.PIPE, text=True)
    try:
        assert child.stdout.readline().strip() == 'claimed'
        child.kill()
        child.wait(timeout=5)
    finally:
        if child.poll() is None:
            child.kill()
            child.wait()
    assert store.get(job)['status'] == 'processing'
    drain(QueueStorage(store.root))
    assert store.get(job)['status'] == 'done'


def test_result_before_ack(store, monkeypatch):
    job = store.submit('Once')['job_id']
    def crash(*_):
        raise OSError('simulated failure before ACK')
    monkeypatch.setattr(store, 'ack', crash)
    with pytest.raises(OSError):
        Worker(store).run(once=True)
    assert store.get(job)['status'] == 'done'
    saved = (store.root / 'results' / (job + '.json')).read_bytes()
    reopened = QueueStorage(store.root)
    drain(reopened)
    assert (store.root / 'results' / (job + '.json')).read_bytes() == saved
    assert not list((store.root / 'processing').glob('*.json'))


@pytest.mark.parametrize('raw', ['{broken', '[]', '{}', '{"payload":null}'])
def test_corrupt(store, raw):
    bad = str(uuid4())
    (store.root / 'queued' / (bad + '.json')).write_text(raw)
    good = store.submit('Good')['job_id']
    drain(store)
    assert store.get(bad)['status'] == 'failed'
    assert store.get(good)['status'] == 'done'
    assert len(list((store.root / 'quarantine').glob('*.bad'))) == 1


def test_worker_lock(store):
    with store.worker_lock():
        with pytest.raises(RuntimeError, match='another worker'):
            Worker(QueueStorage(store.root)).run(once=True)


def test_failed_task(store, monkeypatch):
    job = store.submit('text')['job_id']
    def fail(*_):
        raise RuntimeError('sensitive internal detail')
    monkeypatch.setattr('worker.analyze', fail)
    Worker(store).run(once=True)
    assert store.get(job)['status'] == 'failed'
    assert store.get(job)['error'] == 'text analysis failed'


def test_fifo(store):
    jobs = [store.submit(str(i))['job_id'] for i in range(5)]
    with store.worker_lock():
        for job in jobs:
            record = store.claim()
            assert record['job_id'] == job
            store.finish(record, result=analyze(record['payload']['message']))


def test_atomic_failure(store, monkeypatch):
    job = store.submit('persist')['job_id']
    original = os.replace
    def fail(source, destination):
        if Path(destination).parent.name == 'results':
            raise OSError('disk full')
        return original(source, destination)
    monkeypatch.setattr(os, 'replace', fail)
    with pytest.raises(OSError):
        Worker(store).run(once=True)
    assert store.get(job)['status'] == 'processing'
    monkeypatch.setattr(os, 'replace', original)
    drain(store)
    assert store.get(job)['status'] == 'done'


def test_api_latency(client):
    durations = []
    ids = set()
    for _ in range(100):
        started = time.perf_counter()
        response = client.post('/jobs', json={'message': 'a' * 32})
        durations.append(time.perf_counter() - started)
        assert response.status_code == 202
        ids.add(response.json['job_id'])
    p95 = sorted(durations)[94]
    assert p95 < 1
    assert len(ids) == 100
    METRICS.update(api_requests=100, api_p95_seconds=p95)


def test_json_method_error(client):
    assert client.put('/jobs').status_code == 405
    assert client.put('/jobs').is_json


def test_write_metrics():
    destination = os.environ.get('LAB2_METRICS')
    if destination:
        Path(destination).write_text(json.dumps(METRICS, indent=2) + '\n')
