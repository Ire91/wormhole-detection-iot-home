"""
main.py – Entry point for the Wormhole Attack Detection Simulator.

Usage
-----
  python main.py                                     # run all 3 profiles, 1 run each
  python main.py --profile config/small_flat.json     # single profile
  python main.py --profile config/small_flat.json config/large_house.json --runs 5
  python main.py --runs 10 --output-dir results       # custom output directory

Customisation
-------------
  • --profile   : one or more JSON config files (default: all 3 bundled profiles).
  • --runs      : number of independent simulation runs per profile (default: 3).
  • --output-dir: where to write CSV results (default: output/).
  • --seed      : base random seed for reproducibility (default: 42).

Output
------
  output/<profile_name>/run_0/packet_metrics.csv   – per-packet data
  output/<profile_name>/run_0/node_metrics.csv     – per-node data
  output/<profile_name>/summary.csv                – aggregate per profile
"""

from __future__ import annotations
import argparse
import os
import sys

from simulation.profile import Profile
from metrics.experiment_runner import ExperimentRunner


# Default profile files shipped with the project
DEFAULT_PROFILES = [
    os.path.join("config", "small_flat.json"),
    os.path.join("config", "medium_apartment.json"),
    os.path.join("config", "large_house.json"),
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Profile-Aware Rule-Based Wormhole Attack Detection Simulator"
    )
    parser.add_argument(
        "--profile", nargs="+", default=None,
        help="Path(s) to profile JSON config file(s). "
             "Default: runs all bundled profiles."
    )
    parser.add_argument(
        "--runs", type=int, default=3,
        help="Number of simulation runs per profile (default: 3)."
    )
    parser.add_argument(
        "--output-dir", default="output",
        help="Directory for CSV output (default: output/)."
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Base random seed for reproducibility (default: 42)."
    )
    args = parser.parse_args()

    # Resolve profile paths
    profile_paths = args.profile if args.profile else DEFAULT_PROFILES

    print("=" * 60)
    print("  WORMHOLE ATTACK DETECTION SIMULATOR")
    print("  Profile-Aware Hybrid Detection in IoT Mesh Networks")
    print("=" * 60)
    print(f"  Profiles : {', '.join(profile_paths)}")
    print(f"  Runs     : {args.runs}")
    print(f"  Output   : {args.output_dir}")
    print(f"  Seed     : {args.seed}")

    all_summaries = []

    for ppath in profile_paths:
        if not os.path.isfile(ppath):
            print(f"\n  [ERROR] Profile not found: {ppath} — skipping.")
            continue

        profile = Profile.from_json(ppath)
        print(f"\n{'#'*60}")
        print(f"  Loading profile: {profile.name}")
        print(f"    Nodes={profile.num_nodes}, Area={profile.area_size}, "
              f"Range={profile.comm_range}")
        print(f"    Traffic={profile.traffic_rate}/s, Duration={profile.simulation_duration}s, "
              f"Warm-up={profile.warmup_duration}s")
        print(f"    Wormhole: node {profile.wormhole_node_a} <-> node {profile.wormhole_node_b}, "
              f"tunnel_delay={profile.tunnel_delay}ms")
        print(f"{'#'*60}")

        runner = ExperimentRunner(profile, output_dir=args.output_dir)
        summaries = runner.run(num_runs=args.runs, base_seed=args.seed)
        all_summaries.extend(summaries)

    # Final overall summary
    if all_summaries:
        print(f"\n{'='*60}")
        print("  OVERALL RESULTS")
        print(f"{'='*60}")
        print(f"  {'Profile':<20} {'Run':<5} {'DetRate':<10} {'FPR':<10} "
              f"{'Latency':<12} {'Overhead':<10}")
        print(f"  {'-'*20} {'-'*5} {'-'*10} {'-'*10} {'-'*12} {'-'*10}")
        for s in all_summaries:
            print(f"  {s['profile']:<20} {s['run']:<5} "
                  f"{s['detection_rate']:<10.4f} {s['false_positive_rate']:<10.4f} "
                  f"{s['avg_latency']:<12.2f} {s['overhead']:<10.4f}")

    print(f"\n  All CSVs written to: {os.path.abspath(args.output_dir)}")
    print("  Done.")


if __name__ == "__main__":
    main()
