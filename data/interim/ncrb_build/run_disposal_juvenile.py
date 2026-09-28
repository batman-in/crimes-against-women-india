"""Rebuild the NCRB disposal / juvenile outputs for crimes against women.

  python run_disposal_juvenile.py            # parse the raw files already in data/raw/ncrb_cii_tables
  python run_disposal_juvenile.py --fetch    # first refresh the NCRB catalogues and download missing files

Outputs: data/interim/ncrb_disposal_*.csv, ncrb_juvenile_*.csv (see README_ncrb_disposal_juvenile.md).
"""
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
steps = ['build_disposal.py', 'build_juvenile.py']
if '--fetch' in sys.argv:
    steps = ['fetch_ncrb_catalog.py', 'fetch_disposal_juvenile.py', 'fetch_volume_pages.py'] + steps
for s in steps:
    print('==', s, flush=True)
    r = subprocess.run([sys.executable, str(HERE / s)], cwd=HERE)
    if r.returncode:
        raise SystemExit(f'{s} failed')
