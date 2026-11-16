"""
run_heterogeneity_experiment.py
--------------------------------
Runs the 3 profiles × 3 attack modes heterogeneity experiment (9 cells),
5 runs each, and prints the summary table for Chapter 4.

Usage (from project root):
    python run_heterogeneity_experiment.py

Output:
    output_hetero/<profile>_<attack_mode>/run_N/  — raw CSVs
    heterogeneity_results.csv                     — full 9-cell summary
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import csv
import statistics
from simulation.profile import Profile
from metrics.experiment_runner import ExperimentRunner

PROFILES     = ["config/small_flat.json",
                "config/medium_apartment.json",
                "config/large_house.json"]
ATTACK_MODES = ["out-of-band", "encapsulation", "intermittent"]
NUM_RUNS     = 5
BASE_SEED    = 42
OUTPUT_DIR   = "output_hetero"

results = []

print("=" * 70)
print("  HETEROGENEITY EXPERIMENT  (3 profiles × 3 attack modes, 5 runs each)")
print("=" * 70)

for ppath in PROFILES:
    for mode in ATTACK_MODES:
        profile = Profile.from_json(ppath)
        profile.attack_mode = mode
        # Use a distinct sub-directory per cell so CSVs don't overwrite each other
        cell_name = f"{profile.name}_{mode.replace('-','_')}"
        cell_dir  = os.path.join(OUTPUT_DIR, cell_name)

        print(f"\n  ▶  {profile.name}  ×  {mode}")
        runner = ExperimentRunner(profile, output_dir=cell_dir)
        summaries = runner.run(num_runs=NUM_RUNS, base_seed=BASE_SEED)

        # Aggregate across runs
        wdr  = [s["wormhole_detection_rate"] for s in summaries]
        fpr  = [s["false_positive_rate"]     for s in summaries]
        lat  = [s["avg_latency"]             for s in summaries]
        wuse = [s["wormhole_usage"]          for s in summaries]

        row = {
            "profile"   : profile.name,
            "attack_mode": mode,
            "wdr_mean"  : round(statistics.mean(wdr),  4),
            "wdr_stdev" : round(statistics.stdev(wdr) if len(wdr)>1 else 0, 4),
            "fpr_mean"  : round(statistics.mean(fpr),  4),
            "fpr_stdev" : round(statistics.stdev(fpr) if len(fpr)>1 else 0, 4),
            "latency_mean": round(statistics.mean(lat), 2),
            "wormhole_usage_mean": round(statistics.mean(wuse), 4),
            "num_runs"  : NUM_RUNS,
        }
        results.append(row)
        print(f"      WDR={row['wdr_mean']:.2%} ± {row['wdr_stdev']:.2%}  "
              f"FPR={row['fpr_mean']:.2%} ± {row['fpr_stdev']:.2%}  "
              f"Latency={row['latency_mean']:.1f}ms")

# --- Save full results CSV
csv_path = "heterogeneity_results.csv"
with open(csv_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    writer.writeheader()
    writer.writerows(results)
print(f"\n  Full results saved → {csv_path}")

# --- Print formatted table (copy this into your dissertation)
print("\n" + "=" * 70)
print("  RESULTS TABLE (Wormhole Detection Rate / False Positive Rate)")
print("=" * 70)
profiles_order = ["small_flat", "medium_apartment", "large_house"]
header = f"  {'Attack Mode':<18}" + "".join(f"  {p:<22}" for p in profiles_order)
print(header)
print("  " + "-" * 66)
for mode in ATTACK_MODES:
    row_str = f"  {mode:<18}"
    for pname in profiles_order:
        cell = next((r for r in results if r["profile"]==pname and r["attack_mode"]==mode), None)
        if cell:
            row_str += f"  {cell['wdr_mean']:.0%} WDR / {cell['fpr_mean']:.0%} FPR  "
        else:
            row_str += f"  {'N/A':<22}"
    print(row_str)
print("=" * 70)
