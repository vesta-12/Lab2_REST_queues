"""One local worker, at-least-once delivery and deterministic computation."""
import argparse
import os
from pathlib import Path
import signal
import threading
from queue_storage import QueueStorage


def analyze(message):
    return dict(uppercase=message.upper(), character_count=len(message),
                word_count=len(message.split()))


class Worker:
    def __init__(self, storage):
        self.storage = storage
        self.stop = threading.Event()

    def process_one(self):
        """Caller must hold worker_lock. Storage failures propagate without ACK."""
        record = self.storage.claim()
        if record is None:
            return False
        print(f"{record['job_id']} processing", flush=True)
        try:
            result = analyze(record['payload']['message'])
        except Exception:
            self.storage.finish(record, error='text analysis failed')
        else:
            self.storage.finish(record, result=result)
        print(f"{record['job_id']} terminal result saved; acknowledged", flush=True)
        return True

    def run(self, once=False, poll=0.2):
        with self.storage.worker_lock():
            self.storage.recover()
            while not self.stop.is_set():
                handled = self.process_one()
                if once:
                    break
                if not handled:
                    self.stop.wait(poll)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--once', action='store_true', help='recover and process at most one job')
    args = parser.parse_args()
    root = os.environ.get('LAB2_DATA_DIR', str(Path(__file__).parent / 'data'))
    worker = Worker(QueueStorage(root))
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: worker.stop.set())
    try:
        worker.run(once=args.once)
    except (OSError, RuntimeError) as error:
        raise SystemExit(f'Worker stopped safely: {error}')


if __name__ == '__main__':
    main()
