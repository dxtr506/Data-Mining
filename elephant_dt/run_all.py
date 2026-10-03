"""Chạy lại toàn bộ pipeline: 01 → 04. Dùng: python run_all.py"""
import runpy
import time
from pathlib import Path

import config as C

C.utf8_stdout()
HERE = Path(__file__).resolve().parent
STEPS = ["00_get_treecover.py", "00_get_osm_water.py", "01_prepare.py", "02_segments_states.py", "06_movement_eda.py",
         "07_tasks_tree.py", "04_export_tracks.py", "08_tasks_export.py", "09_behavior_stats.py"]

for step in STEPS:
    t = time.time()
    print(f"\n######## {step} ########")
    runpy.run_path(str(HERE / step), run_name="__main__")
    print(f"-- xong {step} trong {time.time() - t:.0f} s")

print(f"\nMở web: {HERE / 'web' / 'index.html'}")
