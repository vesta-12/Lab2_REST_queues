# Lab 2 remediation audit

| Criterion | Weight | Verified evidence | Remaining limits |
|---|---:|---|---|
| ABET PI 1.2 specification | 10 | spec.md: R1-R9, typed API/internal schemas, examples, four measured NFRs, assumptions/risks, traceability; c4772f7 precedes implementation | Original c5837d7 did not demonstrate spec-first; no retroactive claim |
| REST API | 6 | Four endpoints; real HTTP 200/202/400/404; tests validate types, UUID, limits, storage errors | Local educational service, no production claim |
| Queue and worker | 6 | File persistence; deterministic result; processing/done; atomic writes; result-before-ACK; crash recovery; worker lock; corrupt records; SIGTERM | Local POSIX and single worker only; arbitrary power loss not tested |
| Report | 3 | Two-page report.pdf; actual outcomes, metrics, labelled architecture illustration, reflection | Genuine terminal screenshots still require manual capture; logs are supplied instead |
| Reproducibility | supporting | Fresh venv dependency installation; 41 passed, 0 failed; actual HTTP experiment; ZIP inspected | Student should repeat on their own machine and perform oral defence |

## Actual measurements
See evidence/metrics.json for unrounded values. In this run:
- 100 sequential 32-character submissions: test-client p95 0.553 ms (target <1 s).
- 10 queued jobs persisted for 30.012 s without worker (target >=30 s).
- 10/10 resumed correctly in 0.0172 s (target <10 s).
- 41 tests passed, 0 failed; actual output in evidence/pytest.txt.
- Independent HTTP demo: 3/3 jobs queued for 30 s, then completed; worker SIGTERM exit 0.

## Honest Git sequence
1. c4772f7: updated specification only.
2. 8652cab: API, durable file queue and worker implementation.
3. Subsequent commit: reproducible tests, documentation, evidence and report.
Original c5837d7 and Lab 3 commits remain reachable; main and Lab 3 still point
to dcb4740ad6f6a310008d73a1f23be98b7cc7e04c.

## Defence checklist
Explain HTTP 202 versus completed work; poll the UUID; distinguish public API
from internal messages; stop/restart worker; show persisted result and recovery;
explain FIFO ties, at-least-once execution, idempotency and ACK ordering. Review
Codex-assisted code before submission. Capture the five images listed in
screenshots/README.md and add genuine evidence to the report if required.
The work targets the full rubric; 25/25 is not guaranteed and screenshot-related
credit is not asserted as complete.
