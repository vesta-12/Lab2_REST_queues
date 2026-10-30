# Service Requirements Specification - Laboratory Work 2
Student: Sofiya Serbina | Programme: Computing and Digital Technologies

## 1. Scope and development history
Local HTTP/JSON service and independent file-queue worker (variant C-2).
The original commit c5837d7 saved code and specification together; it cannot prove
specification-first development. This revision starts a new cycle: commit this
specification before implementing it. No claim about earlier chronology is made.

## 2. Functional requirements
- R1: GET /time returns the current UTC server time as an ISO 8601 string.
- R2: POST /echo returns the supplied message unchanged.
- R3: POST /jobs validates and durably queues a text-analysis task without a worker.
- R4: Acceptance returns HTTP 202, a UUID4 job_id and status queued.
- R5: GET /jobs/<job_id> returns the persisted lifecycle state.
- R6: A worker computes uppercase text, Unicode character count, and whitespace-split word count; done exposes the saved result.
- R7: Invalid inputs receive JSON errors; unknown or malformed IDs return 404.
- R8: Queued tasks survive worker absence; interrupted work is replayed on restart.
- R9: Acknowledgement removes the active queue record only after the terminal result is saved; corrupt records are quarantined without stopping other jobs.

## 3. Public API contract
Base URL http://127.0.0.1:5001. JSON objects, UTF-8; no authentication.

| Method | Endpoint | Request fields and types | Response fields and types | Codes | Meaning / requirement |
|---|---|---|---|---|---|
| GET | /time | none | server_time: string (UTC ISO 8601) | 200, 503 | Current time, R1 |
| POST | /echo | message: string | message: string | 200, 400, 413 | Echo, R2/R7 |
| POST | /jobs | message: string | job_id: UUID string, status: string literal queued | 202, 400, 413, 503 | Durable acceptance, R3/R4/R7 |
| GET | /jobs/<job_id> | canonical lowercase UUID4 in path | job record (below) | 200, 404, 503 | Status/result, R5/R6/R7 |

Only the message field is accepted on POST. The JSON root must be an object;
arrays, null, malformed JSON, wrong content type, missing or extra fields are 400.
message must contain non-whitespace text, length 1..4096 Unicode code points;
spaces surrounding valid text are preserved. Body limit 32768 bytes (413).
All errors are {"error": "safe explanation"}. Unsupported methods return JSON 405;
unmatched paths return JSON 404. Storage failure returns 503, never false 202.
/time retains server_time and /echo retains message from the original API.

Example (IDs and timestamps illustrative, not experimental evidence):
```http
POST /jobs
Content-Type: application/json

{"message":"Hello queue"}
```
```json
{"job_id":"123e4567-e89b-42d3-a456-426614174000","status":"queued"}
```
HTTP 202. A GET returns HTTP 200 with the complete record:
```json
{"job_id":"123e4567-e89b-42d3-a456-426614174000","task_type":"text_analysis","payload":{"message":"Hello queue"},"created_at":"2026-10-30T07:00:00+00:00","status":"queued"}
```
After completion HTTP 200 contains the same fields plus:
```json
{"status":"done","started_at":"2026-10-30T07:00:01+00:00","finished_at":"2026-10-30T07:00:01+00:00","result":{"uppercase":"HELLO QUEUE","character_count":11,"word_count":2}}
```
The last snippet shows additional/changed fields, not a separate response schema.
POST /echo with {"message":3} returns HTTP 400
{"error":"message must be a non-blank string of 1..4096 characters"}.
GET /jobs/unknown returns HTTP 404 {"error":"job not found"}.

## 4. Internal queue and lifecycle
Data root from LAB2_DATA_DIR (default project data/). Directories queued/,
processing/, results/, quarantine/. Filename is canonical UUID4 + .json;
client-supplied paths never become filenames without UUID validation.
Each active JSON message contains job_id (UUID4 string), task_type (literal
text_analysis), payload (object with message string), created_at (UTC string),
status (queued or processing), and started_at (UTC string when processing).
Terminal records additionally contain finished_at (UTC string) and either
result (object: uppercase string, character_count integer, word_count integer)
or error (safe string) with status failed. A quarantined corrupt message has a
failed result if its filename identifies a valid job; raw bytes are kept locally.
Public GET returns the record, never filesystem paths or exception details.

queued -> processing -> done or failed. A short filesystem lock serializes API
and worker storage operations. Claim atomically renames queued into processing,
then saves processing state. A separate worker lock forbids simultaneous workers.
FIFO selection uses (created_at, job_id); timestamp ties are ordered by UUID,
not strict real-time arrival. No distributed ordering is promised.
Writes use same-directory temporary files, flush, fsync, os.replace and directory
fsync. Terminal result is written first; only then is processing unlinked (ACK).
On startup, terminal records win over leftover active records; unfinished claims
return to queued. Re-execution is at least once; text analysis is deterministic
and has no external side effects, making replay safe. Invalid active data is
quarantined and the worker continues. Disk errors stop the worker safely for
operator retry, rather than silently acknowledging a lost result. SIGINT/SIGTERM
finish the current short task and stop polling. SIGKILL is handled by recovery.
Atomic rename/locking assumes one local POSIX filesystem. Power-loss durability
depends on filesystem/hardware fsync guarantees; no universal power-loss claim.

## 5. Measurable non-functional requirements
| ID | Criterion and conditions | Verification | Threshold |
|---|---|---|---|
| NFR1 | On an otherwise idle local machine, 100 sequential Flask test-client POST /jobs calls, 32-character messages, worker absent, fresh temp filesystem | test_api_latency; record perf_counter durations | p95 < 1 second; not a network benchmark |
| NFR2 | 10 accepted jobs, worker absent for at least 30 seconds, storage reopened | test_stopped_worker_persistence | 10/10 remain queued with identical IDs and payloads |
| NFR3 | Resume worker on those 10 messages (under 4096 chars) | same test, measured worker drain | 10/10 done with correct results in < 10 seconds |
| NFR4 | Crash after claim and after terminal save before ACK; restart | test_recovery and test_result_before_ack | 0 lost jobs and exactly one saved terminal result per job |

These are acceptance targets, not unmeasured performance claims.

## 6. Assumptions, decisions and risks
| Assumption / constraint | Decision | Related risk | Mitigation |
|---|---|---|---|
| One local POSIX host, writable local disk | flock and same-filesystem rename | Network filesystems may violate guarantees | Reject distributed deployment; use local directory |
| One worker, small educational workload | Exclusive worker lock, directory scan FIFO | Multiple workers or large queues | Fail second worker; limit scope; no throughput scaling claim |
| Sufficient disk and trusted local user | No external database, no retention deletion | Disk full, edits, exposed messages | 503 on storage failure, quarantine, manual cleanup after demo |
| Deterministic text operation | At-least-once recovery | Future non-idempotent task duplicates effects | Do not add side effects without idempotency keys |
| Local loopback-only access | No authentication/TLS | Not safe for internet exposure | Bind 127.0.0.1; production security outside scope |

Python 3.9+ on macOS/Linux, Flask (requirements.txt), pytest for tests
(requirements-dev.txt). HTTP JSON, configurable PORT (default 5001; 5000 allowed).
No AWS credentials, Docker, Kubernetes or external services required.
No cancellation, priority, retries for deterministic task errors, multi-host queue,
TLS, authorization, storage quotas, automatic retention, or exactly-once effects.

## 7. Traceability and evidence plan
| Requirement | Implementation (planned) | Test | Evidence |
|---|---|---|---|
| R1 | app.create_app /time | test_time | evidence/http-demo.txt |
| R2 | app.create_app /echo | test_echo, test_invalid_body | evidence/http-demo.txt |
| R3/R4 | app /jobs; QueueStorage.submit | test_submit, test_invalid_body, test_limits | evidence/http-demo.txt |
| R5/R6 | QueueStorage.get; worker.analyze | test_lifecycle | evidence/http-demo.txt |
| R7 | app validation and error handlers | test_invalid_body, test_unknown, test_storage_error | evidence/pytest.txt |
| R8 | QueueStorage.recover; Worker | test_stopped_worker_persistence, test_recovery | evidence/pytest.txt, evidence/http-demo.txt |
| R9 | QueueStorage.finish/quarantine | test_result_before_ack, test_corrupt, test_worker_lock | evidence/pytest.txt |
| NFR1 | API and durable submit | test_api_latency | evidence/metrics.json |
| NFR2/NFR3 | persistence and worker restart | test_stopped_worker_persistence | evidence/metrics.json |
| NFR4 | result-before-ACK, recovery | test_recovery, test_result_before_ack | evidence/pytest.txt |

Screenshots, if available, must be genuine captures. Logs are evidence, not
screenshots. Any unavailable GUI captures must be listed honestly in the README
and report. Tests and final audit will report actual outcomes after execution.
