

import csv
import os
from collections import Counter, defaultdict


OUTPUT_DIR = "output"
PROFILES = ["small_flat", "medium_apartment", "large_house"]


def load_packet_csv(filepath):
    """Load a packet_metrics CSV and return list of dicts."""
    rows = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse types
            row["hop_count"] = int(row["hop_count"])
            row["total_delay"] = float(row["total_delay"])
            row["rtt_estimate"] = float(row["rtt_estimate"])
            row["path_length"] = int(row["path_length"])
            row["is_attack"] = row["is_attack"] == "True"
            row["traversed_wormhole"] = row["traversed_wormhole"] == "True"
            row["detected"] = row["detected"] == "True"
            row["alerts_list"] = row["alerts"].split(";") if row["alerts"] else []
            rows.append(row)
    return rows


def analyse_profile(profile_name):
    """Analyse all runs for a profile."""
    profile_dir = os.path.join(OUTPUT_DIR, profile_name)
    if not os.path.exists(profile_dir):
        print(f"  [SKIP] {profile_name} — no output directory found.")
        return

    print(f"\n{'='*70}")
    print(f"  PROFILE: {profile_name.upper()}")
    print(f"{'='*70}")

    # Find all run directories
    run_dirs = sorted([
        d for d in os.listdir(profile_dir)
        if os.path.isdir(os.path.join(profile_dir, d)) and d.startswith("run_")
    ])

    all_packets = []
    run_data = {}

    for run_dir in run_dirs:
        pkt_file = os.path.join(profile_dir, run_dir, "packet_metrics.csv")
        if os.path.exists(pkt_file):
            packets = load_packet_csv(pkt_file)
            run_idx = run_dir.replace("run_", "")
            run_data[run_idx] = packets
            all_packets.extend(packets)

    if not all_packets:
        print("  No packet data found.")
        return

    # ================================================================
    # Q1: Which rules fired most?
    # ================================================================
    print(f"\n  --- Q1: RULE FIRE FREQUENCY ---")
    rule_counter = Counter()
    rule_on_attack = Counter()       # rule fired on attack packets
    rule_on_normal = Counter()       # rule fired on normal packets (false positives)
    rule_on_wormhole = Counter()     # rule fired on packets that traversed wormhole

    for pkt in all_packets:
        for alert in pkt["alerts_list"]:
            rule_counter[alert] += 1
            if pkt["is_attack"]:
                rule_on_attack[alert] += 1
            else:
                rule_on_normal[alert] += 1
            if pkt["traversed_wormhole"]:
                rule_on_wormhole[alert] += 1

    total_attack = sum(1 for p in all_packets if p["is_attack"])
    total_normal = sum(1 for p in all_packets if not p["is_attack"])
    total_wormhole = sum(1 for p in all_packets if p["traversed_wormhole"])

    print(f"  Total packets: {len(all_packets)} "
          f"(attack={total_attack}, normal={total_normal}, "
          f"traversed_wormhole={total_wormhole})")
    print()
    print(f"  {'Rule':<30} {'Total':>7} {'On Attack':>10} {'On Normal':>10} {'On WH pkts':>11}")
    print(f"  {'-'*30} {'-'*7} {'-'*10} {'-'*10} {'-'*11}")
    for rule, count in rule_counter.most_common():
        print(f"  {rule:<30} {count:>7} {rule_on_attack[rule]:>10} "
              f"{rule_on_normal[rule]:>10} {rule_on_wormhole[rule]:>11}")

    if not rule_counter:
        print("  (No rules fired at all)")

    # ================================================================
    # Q2: Per-run breakdown (explains run-to-run variance)
    # ================================================================
    print(f"\n  --- Q2: PER-RUN BREAKDOWN ---")
    for run_idx in sorted(run_data.keys()):
        packets = run_data[run_idx]
        attack_pkts = [p for p in packets if p["is_attack"]]
        normal_pkts = [p for p in packets if not p["is_attack"]]
        wh_pkts = [p for p in packets if p["traversed_wormhole"]]
        detected_attack = sum(1 for p in attack_pkts if p["detected"])
        detected_normal = sum(1 for p in normal_pkts if p["detected"])

        run_rules = Counter()
        for p in packets:
            for a in p["alerts_list"]:
                run_rules[a] += 1

        dr = detected_attack / max(len(attack_pkts), 1)
        fpr = detected_normal / max(len(normal_pkts), 1)

        print(f"\n  Run {run_idx}:")
        print(f"    Packets: {len(packets)} (attack={len(attack_pkts)}, "
              f"normal={len(normal_pkts)})")
        print(f"    Traversed wormhole: {len(wh_pkts)} "
              f"({len(wh_pkts)/max(len(packets),1)*100:.1f}%)")
        print(f"    Detection Rate: {dr:.2%} ({detected_attack}/{len(attack_pkts)})")
        print(f"    FPR: {fpr:.2%} ({detected_normal}/{len(normal_pkts)})")
        print(f"    Rules fired: {dict(run_rules) if run_rules else 'NONE'}")

        # Show wormhole usage detail
        wh_attack = sum(1 for p in attack_pkts if p["traversed_wormhole"])
        wh_normal = sum(1 for p in normal_pkts if p["traversed_wormhole"])
        print(f"    Wormhole usage: attack_phase={wh_attack}, warm-up_phase={wh_normal}")

    # ================================================================
    # Q3: Latency breakdown
    # ================================================================
    print(f"\n  --- Q3: LATENCY ANALYSIS ---")
    delays = [p["total_delay"] for p in all_packets]
    wh_delays = [p["total_delay"] for p in all_packets if p["traversed_wormhole"]]
    non_wh_delays = [p["total_delay"] for p in all_packets if not p["traversed_wormhole"]]

    print(f"  Overall:      mean={sum(delays)/len(delays):.2f}ms, "
          f"min={min(delays):.2f}ms, max={max(delays):.2f}ms")
    if wh_delays:
        print(f"  Via wormhole: mean={sum(wh_delays)/len(wh_delays):.2f}ms, "
              f"min={min(wh_delays):.2f}ms, max={max(wh_delays):.2f}ms")
    if non_wh_delays:
        print(f"  Normal path:  mean={sum(non_wh_delays)/len(non_wh_delays):.2f}ms, "
              f"min={min(non_wh_delays):.2f}ms, max={max(non_wh_delays):.2f}ms")

    # ================================================================
    # Q4: Hop count comparison (wormhole vs clean)
    # ================================================================
    print(f"\n  --- Q4: HOP COUNT ANALYSIS ---")
    wh_hops = [p["hop_count"] for p in all_packets if p["traversed_wormhole"]]
    non_wh_hops = [p["hop_count"] for p in all_packets if not p["traversed_wormhole"]]
    if wh_hops:
        print(f"  Via wormhole: mean={sum(wh_hops)/len(wh_hops):.2f} hops, "
              f"min={min(wh_hops)}, max={max(wh_hops)}")
    if non_wh_hops:
        print(f"  Normal path:  mean={sum(non_wh_hops)/len(non_wh_hops):.2f} hops, "
              f"min={min(non_wh_hops)}, max={max(non_wh_hops)}")

    # ================================================================
    # Q5: False positive analysis — which rule caused most FPs?
    # ================================================================
    print(f"\n  --- Q5: FALSE POSITIVE BREAKDOWN (by rule) ---")
    fp_rules = Counter()
    for p in all_packets:
        if not p["is_attack"] and p["detected"]:
            for a in p["alerts_list"]:
                fp_rules[a] += 1

    if fp_rules:
        for rule, count in fp_rules.most_common():
            pct = count / max(total_normal, 1) * 100
            print(f"  {rule:<30} {count:>5} FPs ({pct:.1f}% of normal packets)")
    else:
        print("  No false positives generated.")


def export_analysis_csv():
    """Export a combined analysis CSV across all profiles for Excel/plotting."""
    filepath = os.path.join(OUTPUT_DIR, "detailed_analysis.csv")
    rows = []

    for profile in PROFILES:
        profile_dir = os.path.join(OUTPUT_DIR, profile)
        if not os.path.exists(profile_dir):
            continue
        run_dirs = sorted([
            d for d in os.listdir(profile_dir)
            if os.path.isdir(os.path.join(profile_dir, d)) and d.startswith("run_")
        ])
        for run_dir in run_dirs:
            pkt_file = os.path.join(profile_dir, run_dir, "packet_metrics.csv")
            if not os.path.exists(pkt_file):
                continue
            packets = load_packet_csv(pkt_file)
            run_idx = run_dir.replace("run_", "")

            attack_pkts = [p for p in packets if p["is_attack"]]
            normal_pkts = [p for p in packets if not p["is_attack"]]

            # Per-rule counts
            rule_names = ["HOP_COUNT_DROP", "RTT_ANOMALY", "NEIGHBOUR_INCONSISTENCY",
                          "PATH_STRETCH_ANOMALY", "FORWARDED_SPIKE"]
            rule_tp = {r: 0 for r in rule_names}
            rule_fp = {r: 0 for r in rule_names}
            for p in packets:
                for a in p["alerts_list"]:
                    if p["is_attack"]:
                        rule_tp[a] = rule_tp.get(a, 0) + 1
                    else:
                        rule_fp[a] = rule_fp.get(a, 0) + 1

            wh_count = sum(1 for p in packets if p["traversed_wormhole"])
            delays = [p["total_delay"] for p in packets]

            row = {
                "profile": profile,
                "run": run_idx,
                "total_packets": len(packets),
                "attack_packets": len(attack_pkts),
                "normal_packets": len(normal_pkts),
                "wormhole_traversals": wh_count,
                "detection_rate": round(sum(1 for p in attack_pkts if p["detected"]) / max(len(attack_pkts), 1), 4),
                "false_positive_rate": round(sum(1 for p in normal_pkts if p["detected"]) / max(len(normal_pkts), 1), 4),
                "avg_latency_ms": round(sum(delays) / max(len(delays), 1), 2),
                "min_latency_ms": round(min(delays), 2),
                "max_latency_ms": round(max(delays), 2),
            }
            for r in rule_names:
                row[f"{r}_TP"] = rule_tp.get(r, 0)
                row[f"{r}_FP"] = rule_fp.get(r, 0)
            rows.append(row)

    if rows:
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        print(f"\n  Detailed analysis CSV: {os.path.abspath(filepath)}")


def main():
    print("=" * 70)
    print("  WORMHOLE DETECTION — DETAILED ANALYSIS FOR CHAPTER 4")
    print("=" * 70)

    for profile in PROFILES:
        analyse_profile(profile)

    export_analysis_csv()

    print(f"\n{'='*70}")
    print("  ANALYSIS COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
