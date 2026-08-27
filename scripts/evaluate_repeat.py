#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
import subprocess

RUNS = 4

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
report_file = f"dontgitit_evaluate_{timestamp}_answers-only.md"

with open(report_file, "w", encoding="utf-8") as report:

    report.write(f"# Evaluate Answers Only ({RUNS} Runs)\n\n")

    for run in range(1, RUNS + 1):

        report.write(f"## Run {run}\n\n")

        result = subprocess.run(
            ["python", "scripts/evaluate.py", "--answers-only"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

        report.write("```text\n")
        report.write(result.stdout)
        report.write("\n```\n\n")

print(f"Report written to {report_file}")
