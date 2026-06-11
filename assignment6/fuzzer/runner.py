"""
Campaign runner: ties generators, target wrappers, the debug hook,
and the CSV logger together into a full fuzzing campaign.

A "campaign" = one target (4a or 4b) + one strategy (random or
boundary), run for N trials, producing one CSV log file (and
backtrace files for any crashes).

Usage:
    python3 runner.py 4a random -n 200
    python3 runner.py all all -n 200 --seed 42
"""

import argparse
import random

from targets.target_4a import run_4a, BINARY as BINARY_4A
from targets.target_4b import run_4b, BINARY as BINARY_4B
from generators import (
    random_offset_4a, boundary_offset_4a,
    random_length_4b, boundary_length_4b,
)
from debug_hook import capture_backtrace_4a, capture_backtrace_4b
from logger import TrialLogger, FIELDNAMES_4A, FIELDNAMES_4B


# Maps (target, strategy) -> (generator, target_fn, fieldnames, binary, debug_hook)
CAMPAIGNS = {
    ("4a", "random"):   (random_offset_4a,   run_4a, FIELDNAMES_4A, BINARY_4A, capture_backtrace_4a),
    ("4a", "boundary"): (boundary_offset_4a, run_4a, FIELDNAMES_4A, BINARY_4A, capture_backtrace_4a),
    ("4b", "random"):   (random_length_4b,   run_4b, FIELDNAMES_4B, BINARY_4B, capture_backtrace_4b),
    ("4b", "boundary"): (boundary_length_4b, run_4b, FIELDNAMES_4B, BINARY_4B, capture_backtrace_4b),
}

VALUE_KEY = {"4a": "offset", "4b": "payload_length"}


def run_campaign(target, strategy, n_trials, log_dir="logs"):
    """
    Run one campaign: `n_trials` trials of `strategy` against `target`,
    logging each trial to <log_dir>/<target>_<strategy>.csv.
    """
    generator, target_fn, fieldnames, binary, debug_hook = CAMPAIGNS[(target, strategy)]
    value_key = VALUE_KEY[target]

    log_path = f"{log_dir}/{target}_{strategy}.csv"

    with TrialLogger(log_path, fieldnames) as log:
        for trial in range(n_trials):
            value = generator()
            result = target_fn(value)

            backtrace_path = ""
            if result["crashed"]:
                # Include strategy in the trial tag so backtrace filenames
                # don't collide between e.g. 4a_random trial 5 and
                # 4a_boundary trial 5.
                tag = f"{strategy}_{trial}"
                backtrace_path = debug_hook(binary, value, tag)
                print(f"[{target}/{strategy}] trial {trial}: CRASH at "
                      f"{value_key}={value} (signal {result['signal']}) "
                      f"-> {backtrace_path}")

            row = dict(result)
            row.pop("output", None)  # not logged to CSV
            row["trial"] = trial
            row["strategy"] = strategy
            row["backtrace_path"] = backtrace_path

            log.log(**row)

            if (trial + 1) % 50 == 0:
                print(f"[{target}/{strategy}] {trial + 1}/{n_trials} trials complete")

    print(f"[{target}/{strategy}] done: {n_trials} trials logged to {log_path}")


def main():
    parser = argparse.ArgumentParser(description="Run a fuzzing campaign.")
    parser.add_argument("target", choices=["4a", "4b", "all"],
                         help="Which target to fuzz")
    parser.add_argument("strategy", choices=["random", "boundary", "all"],
                         help="Which input generation strategy to use")
    parser.add_argument("-n", "--trials", type=int, default=200,
                         help="Number of trials per campaign (default: 200)")
    parser.add_argument("--log-dir", default="logs",
                         help="Directory to write CSV logs to (default: logs)")
    parser.add_argument("--seed", type=int, default=None,
                         help="Random seed, for reproducible campaigns")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    targets = ["4a", "4b"] if args.target == "all" else [args.target]
    strategies = ["random", "boundary"] if args.strategy == "all" else [args.strategy]

    for target in targets:
        for strategy in strategies:
            run_campaign(target, strategy, args.trials, args.log_dir)


if __name__ == "__main__":
    main()
