"""
experiment_runner.py – Orchestrates full simulation runs.

Workflow per run:
  1. Build topology (clean, no wormhole).
  2. Generate warm-up traffic → forward through clean topology → learn baseline.
  3. Inject wormhole.
  4. Generate full traffic → forward through compromised topology.
  5. Run detection engine on each post-warm-up packet.
  6. Check forwarding spikes.
  7. Log metrics → export CSVs.

Customisation:
  • num_runs – how many independent runs (with different random seeds).
  • Pass different Profile JSON paths to test multiple scenarios.
"""

from __future__ import annotations
import os
import csv
from typing import Dict, List, Optional

from core.packet import Packet
from core.topology import Topology
from simulation.profile import Profile
from simulation.traffic_generator import TrafficGenerator
from detection.rule_engine import RuleEngine
from metrics.metrics_logger import MetricsLogger


class ExperimentRunner:
    """Runs one or more simulation experiments for a given profile."""

    def __init__(self, profile: Profile, output_dir: str = "output"):
        self.profile = profile
        self.output_dir = output_dir
        self.run_summaries: List[Dict] = []

    # ============================================================ main API
    def run(self, num_runs: int = 1, base_seed: int = 42) -> List[Dict]:
        """
        Execute *num_runs* independent simulations.

        Each run uses a different seed so topology layout and traffic
        patterns vary.  Returns a list of per-run summary dicts.
        """
        self.run_summaries.clear()

        for run_idx in range(num_runs):
            seed = base_seed + run_idx
            print(f"\n{'='*60}")
            print(f"  Profile: {self.profile.name}  |  Run {run_idx + 1}/{num_runs}  |  Seed: {seed}")
            print(f"{'='*60}")

            summary = self._single_run(run_idx, seed)
            self.run_summaries.append(summary)

            # Print quick summary
            print(f"  Detection Rate : {summary['detection_rate']:.2%}")
            print(f"  False Pos Rate : {summary['false_positive_rate']:.2%}")
            print(f"  Avg Latency    : {summary['avg_latency']:.2f} ms")
            print(f"  Overhead       : {summary['overhead']:.2%}")

        # Export aggregate summary CSV
        self._export_summary_csv()
        return self.run_summaries

    # ============================================================ single run
    def _single_run(self, run_idx: int, seed: int) -> Dict:
        """Execute a single simulation run."""
        Packet.reset_counter()

        # ---- 1. Build clean topology
        topo = Topology(seed=seed)
        topo.generate_mesh(
            num_nodes=self.profile.num_nodes,
            area_size=self.profile.area_size,
            comm_range=self.profile.comm_range,
        )
        print(f"  Topology: {topo}")

        # ---- 2. Warm-up phase (clean topology, no wormhole)
        warmup_gen = TrafficGenerator(topo, self.profile, seed=seed)
        warmup_packets = warmup_gen.generate_warmup_only()
        for pkt in warmup_packets:
            topo.forward_packet(pkt)
        print(f"  Warm-up packets forwarded: {len(warmup_packets)}")

        # ---- 3. Learn baseline
        engine = RuleEngine(self.profile, topo)
        engine.learn_baseline(warmup_packets)

        # Snapshot baseline forwarding counts before resetting
        baseline_fwd_snapshot = {n.id: n.forwarded_count for n in topo.nodes.values()}
        topo.reset_node_metrics()

        # ---- 4. Inject wormhole
        wa = self.profile.wormhole_node_a
        wb = self.profile.wormhole_node_b
        if self.profile.scenario != "baseline":
            # Clamp attacker IDs to valid node range
            node_ids = list(topo.nodes.keys())
            wa = wa if wa in node_ids else node_ids[0]
            wb = wb if wb in node_ids else node_ids[-1]
            if wa == wb:
                wb = node_ids[1] if len(node_ids) > 1 else node_ids[0]

            wh = topo.inject_wormhole(wa, wb, self.profile.tunnel_delay, self.profile.attack_mode)
            print(f"  Wormhole injected (Mode: {self.profile.attack_mode}): {wh}")

        # ---- 5. Generate full traffic and forward through compromised topology
        traffic_gen = TrafficGenerator(topo, self.profile, seed=seed + 1000)
        all_packets = traffic_gen.generate()
        for pkt in all_packets:
            topo.forward_packet(pkt)
        print(f"  Total packets forwarded: {len(all_packets)}")

        # ---- 6. Run detection on post-warm-up packets
        fwd_spike_alerts = []
        if self.profile.scenario == "defence":
            for pkt in all_packets:
                engine.analyse_packet(pkt)

            # Check forwarding spikes
            fwd_spike_alerts = engine.check_forwarding_spikes()
            if fwd_spike_alerts:
                print(f"  Forwarding spike alerts: {fwd_spike_alerts}")

        # ---- 7. Log metrics
        logger = MetricsLogger()
        for pkt in all_packets:
            logger.log_packet({
                "run": run_idx,
                "packet_id": pkt.id,
                "src": pkt.src,
                "dst": pkt.dst,
                "hop_count": pkt.hop_count,
                "total_delay": pkt.total_delay,
                "rtt_estimate": pkt.rtt_estimate,
                "path": "->".join(str(n) for n in pkt.path),
                "path_length": len(pkt.path),
                "is_attack": pkt.is_attack_traffic,
                "traversed_wormhole": pkt.traversed_wormhole,
                "alerts": ";".join(pkt.alerts) if pkt.alerts else "",
                "detected": pkt.detected,
                "confidence_score": pkt.confidence_score,
                "confidence_tier": pkt.confidence_tier,
            })

        for node in topo.nodes.values():
            logger.log_node({
                "run": run_idx,
                "node_id": node.id,
                "x": round(node.x, 2),
                "y": round(node.y, 2),
                "is_attacker": node.is_attacker,
                "neighbour_count": len(node.neighbours),
                "neighbours": ";".join(str(n) for n in node.neighbours),
                "forwarded_count": node.forwarded_count,
            })

        # Export CSVs for this run
        run_dir = os.path.join(self.output_dir, self.profile.name, f"run_{run_idx}")
        logger.export_packet_csv(os.path.join(run_dir, "packet_metrics.csv"))
        logger.export_node_csv(os.path.join(run_dir, "node_metrics.csv"))
        print(f"  CSVs exported to: {run_dir}")

        summary = logger.compute_summary()
        summary["run"] = run_idx
        summary["seed"] = seed
        summary["profile"] = self.profile.name
        summary["num_nodes"] = self.profile.num_nodes
        summary["wormhole"] = f"{wa}->{wb}"
        summary["fwd_spike_nodes"] = len(fwd_spike_alerts)

        return summary

    # ============================================================ aggregate
    def _export_summary_csv(self) -> None:
        """Write a summary CSV combining all runs for this profile."""
        if not self.run_summaries:
            return
        filepath = os.path.join(self.output_dir, self.profile.name, "summary.csv")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        fieldnames = list(self.run_summaries[0].keys())
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.run_summaries)
        print(f"\n  Summary CSV: {filepath}")
