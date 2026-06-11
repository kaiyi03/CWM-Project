"""
CSV logging for fuzzing campaigns.

Each campaign (one target + one strategy) writes its own CSV file.
Every trial's result is written as one row, flushed immediately so
the log survives if a later trial hangs or the script is interrupted.
"""

import csv
import os

# Standard column sets for each target. "trial", "strategy" and
# "backtrace_path" are added by the runner; the rest come from
# run_4a()/run_4b()'s result dicts.
FIELDNAMES_4A = [
    "trial", "strategy", "offset",
    "returncode", "signal", "crashed", "hijacked",
    "backtrace_path",
]

FIELDNAMES_4B = [
    "trial", "strategy", "payload_length",
    "returncode", "signal", "crashed",
    "backtrace_path",
]


class TrialLogger:
    """
    Writes one row per fuzzing trial to a CSV file.

    Usage:
        with TrialLogger("logs/4a_random.csv", FIELDNAMES_4A) as log:
            log.log(trial=0, strategy="random", **result_dict)
    """

    def __init__(self, path, fieldnames):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._file = open(path, "w", newline="")
        self._writer = csv.DictWriter(self._file, fieldnames=fieldnames)
        self._writer.writeheader()

    def log(self, **row):
        """
        Write one row. Keys not in fieldnames are ignored; missing
        keys are written as empty cells.
        """
        filtered = {k: row.get(k, "") for k in self._writer.fieldnames}
        self._writer.writerow(filtered)
        self._file.flush()

    def close(self):
        self._file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
