"""
Analysis functions for fuzzing campaign logs.

These operate on the CSV files produced by runner.py
(logs/<target>_<strategy>.csv). They compute summary statistics for
a single campaign and comparisons between strategies. No plotting -
that's left for you to do separately on your real data.
"""

import csv


def load_trials(csv_path):
    """
    Load a campaign CSV into a list of dicts, with values converted
    to appropriate types (int for numeric columns, bool for
    crashed/hijacked).
    """
    trials = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trials.append(_convert_row(row))
    return trials


def _convert_row(row):
    converted = dict(row)
    for key in ("trial", "offset", "payload_length", "returncode", "signal"):
        if key in converted:
            converted[key] = _to_int_or_none(converted[key])
    for key in ("crashed", "hijacked"):
        if key in converted:
            converted[key] = converted[key] == "True"
    return converted


def _to_int_or_none(value):
    if value in ("", None):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def trials_to_first_crash(trials):
    """
    Return the trial index of the first crash, or None if no trial
    in this campaign crashed.
    """
    for t in trials:
        if t["crashed"]:
            return t["trial"]
    return None


def trials_to_first_hijack(trials):
    """
    For 4A campaigns: return the trial index of the first successful
    control-flow hijack (steal_password() called), or None if it
    never occurred. Always None for 4B campaigns (no 'hijacked'
    column).
    """
    for t in trials:
        if t.get("hijacked"):
            return t["trial"]
    return None


def crash_rate(trials):
    """Fraction of trials that crashed (0.0-1.0)."""
    if not trials:
        return 0.0
    return sum(1 for t in trials if t["crashed"]) / len(trials)


def hijack_rate(trials):
    """Fraction of trials that achieved a hijack (4A only)."""
    if not trials:
        return 0.0
    return sum(1 for t in trials if t.get("hijacked")) / len(trials)


def crash_inputs(trials):
    """
    Return the input values (offset or payload_length) for every
    trial that crashed - useful later for plotting where crashes
    occurred relative to the known boundary.
    """
    if not trials:
        return []
    key = "offset" if "offset" in trials[0] else "payload_length"
    return [t[key] for t in trials if t["crashed"]]


def summary_stats(trials):
    """Return a dict of summary statistics for a single campaign."""
    n = len(trials)
    return {
        "n_trials": n,
        "n_crashed": sum(1 for t in trials if t["crashed"]),
        "crash_rate": crash_rate(trials),
        "trials_to_first_crash": trials_to_first_crash(trials),
        "n_hijacked": sum(1 for t in trials if t.get("hijacked")),
        "hijack_rate": hijack_rate(trials),
        "trials_to_first_hijack": trials_to_first_hijack(trials),
    }


def compare_strategies(random_csv, boundary_csv):
    """
    Load two campaign CSVs (same target, different strategies) and
    return a dict comparing them, including a 'speedup' factor: how
    many times fewer trials the boundary strategy needed to find its
    first crash, relative to random.
    """
    random_trials = load_trials(random_csv)
    boundary_trials = load_trials(boundary_csv)

    random_stats = summary_stats(random_trials)
    boundary_stats = summary_stats(boundary_trials)

    comparison = {
        "random": random_stats,
        "boundary": boundary_stats,
    }

    r_ttc = random_stats["trials_to_first_crash"]
    b_ttc = boundary_stats["trials_to_first_crash"]
    if r_ttc is not None and b_ttc is not None and b_ttc > 0:
        comparison["speedup"] = r_ttc / b_ttc
    else:
        comparison["speedup"] = None

    return comparison


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        result = compare_strategies(sys.argv[1], sys.argv[2])
        for key, value in result.items():
            print(key, ":", value)
    else:
        print("Usage: python3 analysis.py <random_csv> <boundary_csv>")
