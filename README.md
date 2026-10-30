# Laboratory Work 2 - REST API and Message Queues
Sofiya Serbina, Computing and Digital Technologies. Branch: `lab2-rest-queues`.

## Overview and architecture
Flask handles synchronous `/time` and `/echo` requests. `POST /jobs` accepts a
text-analysis task immediately; a separate worker computes uppercase text,
Unicode character count and whitespace-separated word count. No AWS or Docker.

`client -> app.py -> queue_storage.py -> data/queued -> worker.py -> data/results`

The worker atomically claims a file into `processing/`. A durable terminal result
is saved before the active file is removed (ACK). Startup recovers interrupted
claims. Delivery is at least once, with deterministic, side-effect-free processing.
An exclusive lock prevents two workers. FIFO uses creation timestamp then UUID.
See spec.md for the complete contract, limits, assumptions and traceability.

## Requirements and installation (macOS zsh)
Python 3.9+; local writable POSIX filesystem. Commands from the project root:
```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```
For running only, install `requirements.txt` instead. Tests use pytest. No secrets.

## Run the API and worker in separate terminals
```sh
source .venv/bin/activate
export LAB2_DATA_DIR="$PWD/data"
PORT=5001 python app.py
```
Port 5001 avoids macOS services that may occupy 5000. `PORT=5000` also works.
The server binds to loopback only. In a second terminal, from the same directory:
```sh
source .venv/bin/activate
export LAB2_DATA_DIR="$PWD/data"
python worker.py
```
Ctrl-C stops gracefully after the current task. `python worker.py --once` recovers
and processes at most one task. The API accepts jobs even when no worker runs.

## Endpoints and examples
| Request | Success | Invalid / unavailable |
|---|---|---|
| GET /time | 200, server_time ISO UTC string | JSON errors |
| POST /echo | 200, same message | 400 invalid message; 413 body too large |
| POST /jobs | 202, job_id UUID4 and queued | 400, 413, 503 storage unavailable |
| GET /jobs/<job_id> | 200, queued/processing/done/failed record | 404 unknown/invalid; 503 storage unavailable |

```sh
curl -i http://127.0.0.1:5001/time
curl -i -H 'Content-Type: application/json' -d '{"message":"Hello queue"}' http://127.0.0.1:5001/echo
curl -i -H 'Content-Type: application/json' -d '{"message":3}' http://127.0.0.1:5001/echo
curl -i http://127.0.0.1:5001/jobs/unknown
```
POST accepts only `message`, a non-blank string of 1..4096 Unicode characters.
Missing/malformed JSON, arrays, extra keys and wrong types are 400. Body limit
32768 bytes. Errors use `{"error":"safe explanation"}`. Results are stored,
not recomputed by GET. Invalid IDs cannot traverse paths.

## Asynchronous stop/restart demonstration
Stop the worker with Ctrl-C, leave the API running, then:
```sh
JOB_ID=$(curl -s -H 'Content-Type: application/json' -d '{"message":"Hello queue"}' http://127.0.0.1:5001/jobs | python -c 'import json,sys; print(json.load(sys.stdin)["job_id"])')
echo "$JOB_ID"
curl -i "http://127.0.0.1:5001/jobs/$JOB_ID"
sleep 30
curl -i "http://127.0.0.1:5001/jobs/$JOB_ID"
```
Both GET responses must show queued. Restart `python worker.py` in the other
terminal. Repeat GET: status becomes done, with result
`{"uppercase":"HELLO QUEUE","character_count":11,"word_count":2}`.
Processing is short, so HTTP polling may miss that transient status; the worker
log shows it and test_lifecycle verifies it while a claim is held.

## Reproduce tests and real HTTP experiment
```sh
python -m pytest -v
# These commands overwrite the supplied evidence with your actual rerun:
LAB2_METRICS=evidence/metrics.json python -m pytest -v > evidence/pytest.txt 2>&1
PYTHONPATH=. python tools/http_demo.py > evidence/http-demo.txt 2>&1
```
The first suite takes about 31 seconds because the persistence test actually
waits 30 seconds. All storage tests use temporary directories. The HTTP demo
uses a temporary loopback port and real independent worker process, waits 30
seconds, validates results and sends SIGTERM (exit 0). Nothing remains running.
`evidence/metrics.json` records measured NFR values; the API latency metric is a
Flask test-client measurement, not a network or production benchmark.

## Evidence and screenshots
Five student-supplied terminal screenshots from 30 October 2026 are included in
screenshots/ and in the two-page report.pdf. Images were copied without editing;
source names and hashes are recorded in evidence/screenshot-manifest.json.
They show REST success/errors, the same UUID queued and done, Flask request logs
(including POST /jobs 202), and 41 passed in 30.36s on the student's machine.

The final independent rerun in evidence/pytest.txt reports 41 passed in 30.34s,
0 failed. Current NFR values are in evidence/metrics.json. The earlier run remains
in evidence/pytest-initial.txt and evidence/metrics-initial.json. Actual network
experiment output remains in evidence/http-demo.txt.

The separate client screenshot of `202 Accepted` with a JSON job_id is not among
the supplied images; server logs are not a replacement for that response view.
screenshots/README.md provides the precise curl command for optional image 06.

To rebuild the PDF and matching editable DOCX (optional authoring dependencies):
```sh
python -m pip install -r requirements-report.txt
python tools/build_report.py
```
On macOS, the builder embeds Times New Roman from system Supplemental fonts.
On another platform, pass `--font-dir` with those font files. By default the DOCX
is written beside the repository, outside the submission ZIP. Both versions use
the same text and the five unchanged images. Main text is 14 pt, captions 10 pt;
full-resolution screenshots are supplied for closer inspection of long JSON.

## Limitations and provenance
One trusted local host, one worker, no TLS/authentication, no distributed queue,
no retention policy. Large directories require manual cleanup after the demo.
Do not deploy the Flask development server publicly. Disk errors preserve active
work or return 503; fix storage and restart. Corrupt active records move to
quarantine and become failed when their filename identifies a job. No guarantee
against arbitrary manual edits, hardware failure or every power-loss scenario.

This remediation was prepared with OpenAI Codex assistance. The student should
review and explain each component. The original code's authorship or similarity
cannot be inferred here; no claim of entirely manual authorship is made.
Original code and spec were in one commit (`c5837d7`). The new specification
commit precedes the new implementation; no original history was rewritten.

## Submission
The root contains app.py, worker.py, queue_storage.py, spec.md, dependency files,
README.md, report.pdf, tests/, screenshots/, evidence/, and tools/.
`Serbina_Sofiya_Lab2.zip` is delivered beside the repository, with one top-level
`Serbina_Sofiya_Lab2/` folder. No Git metadata, environment, runtime queues,
legacy architecture, credentials or Lab 3 files are included. The original Lab 2
and old report remain available in Git history. main and lab3-docker-kubernetes
are unchanged. See AUDIT.md for rubric evidence and remaining manual checks.

To rebuild the checked submission archive after committing materials:
```sh
python tools/package_submission.py
```
The packager takes tracked files only, validates the new archive, and atomically
replaces the previous ZIP after all checks succeed.
