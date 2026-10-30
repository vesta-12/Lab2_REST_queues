# Genuine screenshot checklist - captures still required
No images in this folder are fabricated. Native Terminal capture was denied by
the authoring environment. The original screenshots described the replaced
architecture, so they were removed from this revision (retained in Git history).

Use macOS Shift-Cmd-4 and save genuine captures with these names:
1. 01_rest_200_400_404.png: `curl -i` /time, successful /echo, invalid /echo,
   and GET /jobs/unknown, showing actual HTTP 200, 400 and 404.
2. 02_job_202_queued.png: with worker stopped, POST /jobs response (use curl -i
   and copy the UUID), then GET the same ID showing queued.
3. 03_worker_stopped_30s.png: repeat GET after `sleep 30`, with the same UUID
   and payload still queued. Submit more than one job to show accumulation.
4. 04_worker_restart_done.png: worker's processing/acknowledged output plus GET
   responses for those same jobs showing done and correct persisted results.
5. 05_tests.png: `python -m pytest -v` final summary from your machine.

README.md supplies exact commands. Do not edit response content or label logs
as screenshots. After capturing, attach the actual images to the report and
rebuild the ZIP; the supplied report explicitly states this is still pending.
