"""
Plotting script for the fuzzing campaign results.
Produces three figures, saved to plots/.
Run after collecting repetitions: python3 plot_results.py
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from analysis import load_trials, trials_to_first_crash

REPS = range(1, 4)        # rep1 .. rep3
LOG_ROOT = "logs"
PLOT_DIR = "plots"


def load_all(target, strategy):
    all_trials = []
    for rep in REPS:
        path = os.path.join(LOG_ROOT, f"rep{rep}", f"{target}_{strategy}.csv")
        if os.path.exists(path):
            all_trials.extend(load_trials(path))
        else:
            print(f"[warning] missing file: {path}")
    return all_trials


def classify_4a_outcome(trial):
    if trial.get("hijacked"):
        return "Hijacked"
    if trial["crashed"]:
        return "Crashed"
    return "Normal"


def plot_outcome_vs_offset_4a():
    strategies = {
        "random":   {"trials": load_all("4a", "random"),   "marker": "o", "alpha": 0.4},
        "boundary": {"trials": load_all("4a", "boundary"), "marker": "^", "alpha": 0.6},
    }

    categories = ["Normal", "Crashed", "Hijacked"]
    colors = {"Normal": "tab:blue", "Crashed": "tab:red", "Hijacked": "tab:green"}
    y_pos = {cat: i for i, cat in enumerate(categories)}

    fig, ax = plt.subplots(figsize=(10, 4))

    for strategy, props in strategies.items():
        for cat in categories:
            xs = [t["offset"] for t in props["trials"]
                  if classify_4a_outcome(t) == cat]
            ys = [y_pos[cat]] * len(xs)
            # small vertical jitter to reveal density
            jitter = np.random.uniform(-0.08, 0.08, size=len(ys))
            ax.scatter(xs, np.array(ys, dtype=float) + jitter,
                       color=colors[cat],
                       marker=props["marker"],
                       alpha=props["alpha"],
                       label=f"{strategy} / {cat}" if cat == "Crashed" or cat == "Hijacked" else f"{strategy} / {cat}")

    ax.axvline(24, color="black", linestyle="--", label="Offset 24 (Exercise 4)")
    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels(categories)
    ax.set_xlabel("Offset")
    ax.set_title("4A: Outcome vs Offset — Random (circles) vs Boundary (triangles)")
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOT_DIR, "outcome_vs_offset_4a.png"), bbox_inches="tight")
    plt.close(fig)


def plot_crash_threshold_4b(expected_threshold=264):
    strategies = {
        "random":   {"trials": load_all("4b", "random"),   "marker": "o", "alpha": 0.4},
        "boundary": {"trials": load_all("4b", "boundary"), "marker": "^", "alpha": 0.6},
    }

    categories = ["Normal", "Crashed"]
    colors = {"Normal": "tab:blue", "Crashed": "tab:red"}
    y_pos = {cat: i for i, cat in enumerate(categories)}

    fig, ax = plt.subplots(figsize=(10, 4))

    for strategy, props in strategies.items():
        for cat in categories:
            is_crashed = (cat == "Crashed")
            xs = [t["payload_length"] for t in props["trials"]
                  if t["crashed"] == is_crashed]
            ys = [y_pos[cat]] * len(xs)
            jitter = np.random.uniform(-0.08, 0.08, size=len(ys))
            ax.scatter(xs, np.array(ys, dtype=float) + jitter,
                       color=colors[cat],
                       marker=props["marker"],
                       alpha=props["alpha"],
                       label=f"{strategy} / {cat}")

    ax.axvline(expected_threshold, color="black", linestyle="--",
               label=f"Expected threshold ({expected_threshold})")
    ax.set_yticks(list(y_pos.values()))
    ax.set_yticklabels(categories)
    ax.set_xlabel("Payload length")
    ax.set_title("4B: Outcome vs Payload Length — Random (circles) vs Boundary (triangles)")
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(PLOT_DIR, "crash_threshold_4b.png"), bbox_inches="tight")
    plt.close(fig)


def collect_ttc(target, strategy):
    values = []
    for rep in REPS:
        path = os.path.join(LOG_ROOT, f"rep{rep}", f"{target}_{strategy}.csv")
        if not os.path.exists(path):
            continue
        ttc = trials_to_first_crash(load_trials(path))
        if ttc is not None:
            values.append(ttc)
        else:
            print(f"[warning] no crash found in {path}")
    return values


def plot_strategy_comparison():
    from analysis import crash_rate, hijack_rate

    targets = ["4a", "4b"]
    strategies = ["random", "boundary"]

    # For 4A use hijack_rate, for 4B use crash_rate
    rate_fn = {"4a": hijack_rate, "4b": crash_rate}

    means = {s: [] for s in strategies}
    stds  = {s: [] for s in strategies}

    for target in targets:
        fn = rate_fn[target]
        for strategy in strategies:
            values = []
            for rep in REPS:
                path = os.path.join(LOG_ROOT, f"rep{rep}",
                                    f"{target}_{strategy}.csv")
                if not os.path.exists(path):
                    print(f"[warning] missing: {path}")
                    continue
                values.append(fn(load_trials(path)))
            means[strategy].append(np.mean(values) if values else 0)
            stds[strategy].append(np.std(values)  if values else 0)

    x = np.arange(len(targets))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(x - width/2, means["random"],   width, yerr=stds["random"],
           label="Random",   color="tab:blue",   capsize=4)
    ax.bar(x + width/2, means["boundary"], width, yerr=stds["boundary"],
           label="Boundary", color="tab:orange", capsize=4)

    ax.set_xticks(x)
    ax.set_xticklabels(["4A (hijack rate)", "4B (crash rate)"])
    ax.set_ylabel("Rate (fraction of trials)")
    ax.set_ylim(0, 1)
    ax.set_title("Strategy Efficiency: Hijack Rate (4A) vs Crash Rate (4B)")
    ax.legend()

    # add value labels on top of each bar for clarity
    for rect in ax.patches:
        height = rect.get_height()
        if height > 0:
            ax.annotate(f"{height:.2f}",
                        xy=(rect.get_x() + rect.get_width() / 2, height),
                        xytext=(0, 3), textcoords="offset points",
                        ha="center", va="bottom", fontsize=9)

    fig.tight_layout()
    fig.savefig(os.path.join(PLOT_DIR, "strategy_comparison.png"))
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(PLOT_DIR, exist_ok=True)
    plot_outcome_vs_offset_4a()
    plot_crash_threshold_4b()
    plot_strategy_comparison()
    print(f"Plots saved to {PLOT_DIR}/")
