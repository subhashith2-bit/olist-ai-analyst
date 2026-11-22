
import subprocess
import sys
import time
from pathlib import Path


# Find the project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Pipeline stages in execution order
stages = [
    "src/load_raw.py",
    "src/clean.py",
    "src/build_analytics.py",
    "src/checks.py",
    "src/export_serving_db.py"
]

total_start = time.perf_counter()

print("\n===== OLIST DATA PIPELINE =====\n")

for stage in stages:
    script_path = PROJECT_ROOT / stage

    print(f"\nStarting: {stage}")

    start_time = time.perf_counter()

    try:
        subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            cwd=PROJECT_ROOT
        )

        duration = time.perf_counter() - start_time
        print(f"Completed: {stage} | Time: {duration:.2f} seconds")

    except subprocess.CalledProcessError:
        print(f"\nPIPELINE FAILED at: {stage}")
        sys.exit(1)

total_duration = time.perf_counter() - total_start

print("\n===== PIPELINE COMPLETED SUCCESSFULLY =====")
print(f"Total runtime: {total_duration:.2f} seconds")
