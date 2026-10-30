"""Local POSIX file queue. Terminal records are durable before acknowledgement."""
import fcntl
import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import tempfile
from uuid import UUID, uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


def valid_id(value):
    try:
        parsed = UUID(value)
        return parsed.version == 4 and str(parsed) == value
    except (ValueError, TypeError, AttributeError):
        return False


def valid_message(value):
    return isinstance(value, str) and 1 <= len(value) <= 4096 and bool(value.strip())


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


class QueueStorage:
    def __init__(self, root):
        self.root = Path(root).resolve()
        for name in ('queued', 'processing', 'results', 'quarantine'):
            (self.root / name).mkdir(parents=True, exist_ok=True)

    @contextmanager
    def locked(self):
        with (self.root / '.storage.lock').open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield

    @contextmanager
    def worker_lock(self):
        with (self.root / '.worker.lock').open('a') as stream:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise RuntimeError('another worker is active') from None
            yield

    def write(self, path, record):
        fd, temporary = tempfile.mkstemp(prefix='.tmp-', dir=path.parent)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as stream:
                json.dump(record, stream, ensure_ascii=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
            sync_dir(path.parent)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    @staticmethod
    def read(path):
        with path.open(encoding='utf-8') as stream:
            return json.load(stream)

    def submit(self, message):
        if not valid_message(message):
            raise ValueError('invalid message')
        record = dict(job_id=str(uuid4()), task_type='text_analysis',
                      payload={'message': message}, created_at=now(), status='queued')
        with self.locked():
            self.write(self.root / 'queued' / (record['job_id'] + '.json'), record)
        return record

    def get(self, job_id):
        if not valid_id(job_id):
            return None
        with self.locked():
            for directory in ('results', 'processing', 'queued'):
                path = self.root / directory / (job_id + '.json')
                if path.exists():
                    return self.read(path)
        return None

    def remove(self, path):
        if path.exists():
            path.unlink()
            sync_dir(path.parent)

    def quarantine(self, path):
        job_id = path.stem
        if valid_id(job_id):
            self.write(self.root / 'results' / path.name,
                       dict(job_id=job_id, status='failed', finished_at=now(),
                            error='stored queue record is invalid'))
        os.replace(path, self.root / 'quarantine' / (str(uuid4()) + '.bad'))
        sync_dir(path.parent)
        sync_dir(self.root / 'quarantine')

    def validated(self, path):
        record = self.read(path)
        if (not isinstance(record, dict) or record.get('job_id') != path.stem
                or not valid_id(path.stem) or record.get('task_type') != 'text_analysis'
                or not isinstance(record.get('payload'), dict)
                or not valid_message(record['payload'].get('message'))
                or record.get('status') not in ('queued', 'processing')
                or not isinstance(record.get('created_at'), str)):
            raise ValueError('invalid queue record')
        datetime.fromisoformat(record['created_at'])
        return record

    def recover(self):
        """Call only while holding the exclusive worker lock."""
        with self.locked():
            for directory in ('processing', 'queued'):
                for path in sorted((self.root / directory).glob('*.json')):
                    if (self.root / 'results' / path.name).exists():
                        self.remove(path)
                        continue
                    try:
                        record = self.validated(path)
                    except (ValueError, UnicodeError, TypeError):
                        self.quarantine(path)
                        continue
                    if directory == 'processing':
                        record['status'] = 'queued'
                        record.pop('started_at', None)
                        # Write the durable destination before removing the claim.
                        self.write(self.root / 'queued' / path.name, record)
                        self.remove(path)

    def claim(self):
        with self.locked():
            candidates = []
            for path in (self.root / 'queued').glob('*.json'):
                try:
                    record = self.validated(path)
                except (ValueError, UnicodeError, TypeError):
                    self.quarantine(path)
                    continue
                candidates.append((record['created_at'], record['job_id'], path, record))
            if not candidates:
                return None
            _, _, source, record = min(candidates)
            destination = self.root / 'processing' / source.name
            os.replace(source, destination)
            sync_dir(source.parent)
            sync_dir(destination.parent)
            record.update(status='processing', started_at=now())
            self.write(destination, record)
            return record

    def finish(self, record, result=None, error=None):
        terminal = dict(record, finished_at=now(), status='failed' if error else 'done')
        terminal.update({'error': error} if error else {'result': result})
        with self.locked():
            self.write(self.root / 'results' / (record['job_id'] + '.json'), terminal)
            self.ack(record['job_id'])
        return terminal

    def ack(self, job_id):
        """Only called after durable terminal write; separate for crash testing."""
        self.remove(self.root / 'processing' / (job_id + '.json'))
