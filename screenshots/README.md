# Terminal screenshots supplied by Sofiya Serbina

Five user-supplied captures from 30 October 2026 are included at their original
resolution and aspect ratio. They were copied byte-for-byte and renamed only.
Original names and SHA-256 hashes are in evidence/screenshot-manifest.json.

| File | Visible evidence |
|---|---|
| 01_rest_api_200_400_404.png | server_time and echo JSON with HTTP 200; invalid message HTTP 400; unknown job HTTP 404 |
| 02_job_queued.png | HTTP 200; UUID 5d445131-c6c0-4d87-9cc8-ec022e2921a1; Hello queue; queued |
| 03_api_logs.png | Flask access log for /time, /echo, /jobs, including POST /jobs status 202 |
| 04_job_completed.png | Same UUID; HTTP 200; done; HELLO QUEUE; character_count 11; word_count 2; created/started/finished timestamps |
| 05_pytest_41_passed.png | Student run: 41 passed in 30.36s; recovery, result-before-ACK, FIFO, lock and validation checks |

All five images appear in the two-page report. Full-size files here provide the
best view of long JSON lines; PDF images retain source detail for zooming.
The rerun in evidence/pytest.txt is a separate experiment, so its duration may
differ from the student's screenshot. Neither file was edited to match the other.

## Optional additional client response capture
The supplied images do NOT show a direct client response containing both
`HTTP/1.1 202 ACCEPTED` and JSON job_id. Image 03 shows only the server access-log
status 202. The automated HTTP log and tests verify acceptance separately.
Native Terminal access was denied in the authoring environment, so no extra
screenshot was fabricated or substituted. For stronger rubric evidence, leave
app.py running on port 5001, stop worker.py, and execute this in macOS Terminal:

```sh
curl -i -H 'Content-Type: application/json' \
  -d '{"message":"Hello queue"}' \
  http://127.0.0.1:5001/jobs
```

Capture the actual response as `06_job_202_accepted.png`. It should show 202,
a fresh UUID4 and status queued. Do not reuse the old job ID: a new POST creates
a new task. This additional image is not claimed to be included in this package.
