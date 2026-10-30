# Final Lab 2 submission audit

| Criterion | Maximum | Confirmed evidence | Limits / remaining action |
|---|---:|---|---|
| ABET PI 1.2 Specification | 10 | spec.md: R1-R9, typed contracts, internal format, limits, four measurable NFRs, risks, traceability; specification commit before remediation implementation | Original c5837d7 saved spec/code together; no retroactive chronology claim |
| REST API | 6 | Four endpoints; 202 + UUID; status/result; 200/400/404 captured; boundary and error tests pass | Direct client screenshot of 202 with JSON is not supplied; Flask log 202 is labelled accurately |
| Queue and Worker | 6 | Persistence, processing/done/failed, FIFO, lock, atomic write, result-before-ACK, killed-process recovery, corruption handling | One local POSIX host and one worker; not a distributed or hardware-failure guarantee |
| Report and Evidence | 3 | Two-page Times New Roman report; 14 pt body; five unchanged user-supplied screenshots with captions; real logs, metrics, reflection and Codex disclosure | Optional sixth capture of client-side 202 + job_id would strengthen evidence; no full-credit guarantee |
| TOTAL | 25 | Complete runnable package with measured evidence; assessment remains the teacher's decision | No automatic 25/25 claim |

## Final executed checks
- Final rerun: **41 passed in 30.34s, 0 failed**, evidence/pytest.txt.
- 10/10 jobs retained without worker for 30.016 seconds.
- 10/10 resumed with correct results in 0.0228 seconds (<10 s target).
- 100 sequential 32-character test-client submissions: p95 0.606 ms (<1 s target).
- Current unrounded values: evidence/metrics.json; prior run preserved separately.
- Student screenshot: **41 passed in 30.36s**; a separate run, not edited to match.
- Original actual network experiment: 3 jobs retained for 30 seconds, processed
  by independent worker, graceful SIGTERM exit 0 (evidence/http-demo.txt).
- Tests cover a killed process after claim, failure before ACK, storage-write
  failure, corrupt records, FIFO, worker exclusion and input boundaries.

## Screenshot verification
Five supplied images copied without content edits. SHA-256 checks against source
files passed. Queued/done images show the same UUID
5d445131-c6c0-4d87-9cc8-ec022e2921a1 and correct result. Flask image shows POST
/jobs 202; it is not described as a client response or proof of its JSON body.
No image 06 exists. Exact command for that optional capture is in screenshots/README.md.

## Report and package verification
PDF and editable DOCX use the same text and images. Both have two visually
inspected pages, without synthetic diagrams, clipped captions or title rules.
Images retain their full pixel detail; full-size originals are also in the ZIP.
The editable DOCX is beside the ZIP, excluded from the submission archive.
Archive validation checks CRC, duplicate paths, required files, source equality,
and absence of Git metadata, environments, secrets, caches, runtime queues and
Lab 3/5 content. tools/package_submission.py reproduces these checks.

## History and scope
c4772f7: specification only; 8652cab: implementation; 7be01cd: tests, documentation,
evidence and first report. Final documentation/evidence commit follows them.
No application, worker, storage, test or dependency-runtime code was changed for
final packaging. main and lab3-docker-kubernetes remain at
 dcb4740ad6f6a310008d73a1f23be98b7cc7e04c.

## Defence
Explain acceptance versus completion, the queued/done UUID, worker stop/restart,
ACK ordering, persistence, FIFO ties and at-least-once idempotent replay. If the
teacher requires a direct response screenshot, capture 06 using the supplied
command; five real screenshots and all executable evidence are already supplied.
