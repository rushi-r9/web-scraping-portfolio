"""One-shot scheduled-collection entry point; scheduling is external and optional."""
from datetime import datetime, timezone
from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).parent
run_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out=ROOT/'runs'/run_id
cmd=[sys.executable, str(ROOT/'scraper.py'), '--dataset','all','--output-dir',str(out)]
subprocess.run(cmd,check=True)
print(f'Completed one local fixture collection run: {out}')
print('This script is not a deployed service; use cron or Windows Task Scheduler for recurrence.')
