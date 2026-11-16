"""
metrics_logger.py – Collects per-packet and per-node metrics and exports CSVs.

Output CSVs:
  • packet_metrics.csv  – one row per packet with all routing/detection fields.
  • node_metrics.csv    – one row per node with forwarding/attacker info.
  • summary.csv         – detection rate, FPR, avg latency, overhead per profile.

Customisation:
  • Add extra columns by extending the record dicts in log_packet / log_node.
"""

from __future__ import annotations
import csv
import os
from typing import Any, Dict, List


class MetricsLogger:
    """Collects simulation metrics and exports them as CSV files."""

    def __init__(self):
        self.packet_records: List[Dict[str, Any]] = []
        self.node_records: List[Dict[str, Any]] = []

    # ============================================================ logging
    def log_packet(self, packet_data: Dict[str, Any]) -> None:
        """Append a single packet record."""
        self.packet_records.append(packet_data)

    def log_node(self, node_data: Dict[str, Any]) -> None:
        """Append a single node record."""
        self.node_records.append(node_data)

    # ============================================================ CSV export
    def export_packet_csv(self, filepath: str) -> None:
        """Write per-packet metrics to a CSV file."""
        self._write_csv(filepath, self.packet_records)

    def export_node_csv(self, filepath: str) -> None:
        """Write per-node metrics to a CSV file."""
        self._write_csv(filepath, self.node_records)

    # ============================================================ summary
    def compute_summary(self) -> Dict[str, float]:
        """
        Compute aggregate detection metrics from logged packet records.

        Returns dict with:
          detection_rate   – fraction of attack packets correctly flagged
          false_positive_rate – fraction of normal packets incorrectly flagged
          avg_latency      – mean end-to-end delay (ms) across all packets
          overhead         – fraction of packets that triggered any alert
          total_packets    – total number of packets
          attack_packets   – number of attack-phase packets
          normal_packets   – number of warm-up (normal) packets
        """
        total = len(self.packet_records)
        if total == 0:
            return {"detection_rate": 0.0, "false_positive_rate": 0.0,
                    "avg_latency": 0.0, "overhead": 0.0,
                    "total_packets": 0, "attack_packets": 0, "normal_packets": 0}

        attack_pkts = [r for r in self.packet_records if r.get("is_attack")]
        normal_pkts = [r for r in self.packet_records if not r.get("is_attack")]

        # True positives: attack packets correctly flagged
        tp = sum(1 for r in attack_pkts if r.get("detected"))
        # False positives: normal packets incorrectly flagged
        fp = sum(1 for r in normal_pkts if r.get("detected"))

        # Wormhole specific metrics
        wh_traversed = sum(1 for r in attack_pkts if str(r.get("traversed_wormhole")).lower() == "true")
        wh_usage = wh_traversed / max(len(attack_pkts), 1)
        wh_tp = sum(1 for r in attack_pkts if str(r.get("traversed_wormhole")).lower() == "true" and r.get("detected"))
        wh_detection_rate = wh_tp / max(wh_traversed, 1)

        detection_rate = tp / max(len(attack_pkts), 1)
        fpr = fp / max(len(normal_pkts), 1)

        delays = [r["total_delay"] for r in self.packet_records
                  if r.get("total_delay") is not None]
        avg_latency = sum(delays) / max(len(delays), 1)

        total_detected = sum(1 for r in self.packet_records if r.get("detected"))
        overhead = total_detected / total

        return {
            "detection_rate": round(detection_rate, 4),
            "false_positive_rate": round(fpr, 4),
            "avg_latency": round(avg_latency, 4),
            "overhead": round(overhead, 4),
            "total_packets": total,
            "attack_packets": len(attack_pkts),
            "normal_packets": len(normal_pkts),
            "true_positives": tp,
            "false_positives": fp,
            "wormhole_usage": round(wh_usage, 4),
            "wormhole_detection_rate": round(wh_detection_rate, 4),
        }

    # ============================================================ reset
    def reset(self) -> None:
        """Clear all records for a new run."""
        self.packet_records.clear()
        self.node_records.clear()

    # ============================================================ internal
    @staticmethod
    def _write_csv(filepath: str, records: List[Dict[str, Any]]) -> None:
        """Write a list of dicts to a CSV file."""
        if not records:
            return
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        fieldnames = list(records[0].keys())
        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(records)
