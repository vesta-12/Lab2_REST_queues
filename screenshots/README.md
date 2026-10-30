# Terminal screenshots supplied by Sofiya Serbina

Six user-supplied captures from 30 October 2026 are included at their original
resolution and aspect ratio. They were copied byte-for-byte and renamed only.
Original names and SHA-256 hashes are in evidence/screenshot-manifest.json.

| File | Visible evidence |
|---|---|
| 01_rest_api_200_400_404.png | server_time and echo JSON with HTTP 200; invalid message HTTP 400; unknown job HTTP 404 |
| 02_job_queued.png | HTTP 200; UUID 5d445131-c6c0-4d87-9cc8-ec022e2921a1; Hello queue; queued |
| 03_api_logs.png | Flask access log for /time, /echo, /jobs, including POST /jobs status 202 |
| 04_job_completed.png | Same UUID; HTTP 200; done; HELLO QUEUE; character_count 11; word_count 2; created/started/finished timestamps |
| 05_pytest_41_passed.png | Student run: 41 passed in 30.36s; recovery, result-before-ACK, FIFO, lock and validation checks |
| 06_job_202_accepted.png | Direct POST /jobs response: HTTP/1.1 202 ACCEPTED; job_id b7f05fec-004f-47d5-8607-9be4a7df6318; status queued |

Images 01-05 appear in the unchanged two-page report. Image 06 is additional
client-response evidence supplied in the screenshots folder and submission ZIP. Full-size files here provide the
best view of long JSON lines; PDF images retain source detail for zooming.
The rerun in evidence/pytest.txt is a separate experiment, so its duration may
differ from the student's screenshot. Neither file was edited to match the other.

## Direct client response verified
Image 06 shows the actual curl POST /jobs command, HTTP/1.1 202 ACCEPTED,
JSON job_id b7f05fec-004f-47d5-8607-9be4a7df6318 and status queued.
This is a new task; its UUID intentionally differs from the queued/done task
in images 02 and 04. The capture was copied unchanged, not reconstructed from
server logs. No additional screenshot is required for the previously identified
202 client-response evidence gap. report.pdf is retained byte-for-byte.
