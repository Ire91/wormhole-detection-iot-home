"""
rule_engine.py – Profile-aware rule-based wormhole detection engine.

Detection Rules
---------------
1. Hop-Count Drop       – packet hop count much lower than baseline.
2. RTT Anomaly          – round-trip estimate suspiciously fast.
3. Neighbour Inconsist. – node has a "neighbour" beyond radio range.
4. Path Stretch Anomaly – actual path length vs expected ratio too high.
5. Forwarded-Pkt Spike  – node forwards far more packets than usual.

Warm-up Phase
-------------
During the first *warmup_duration* seconds the engine only learns
baseline statistics.  Detection rules are applied only AFTER warm-up.

Customisation:
  • All thresholds are loaded from the Profile (JSON config).
  • Add/remove rules by editing the analyse_packet() method.
"""

from __future__ import annotations
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from core.node import Node
from core.packet import Packet
from core.topology import Topology
from simulation.profile import Profile


class RuleEngine:
    """Profile-aware wormhole detection with a warm-up baseline phase."""

    def __init__(self, profile: Profile, topology: Topology):
        self.profile = profile
        self.topology = topology

        # ---- baseline statistics (populated during warm-up) ----
        # key = (src, dst) → list of hop counts seen during warm-up
        self._baseline_hops: Dict[Tuple[int, int], List[int]] = defaultdict(list)
        # key = (src, dst) → list of RTT estimates during warm-up
        self._baseline_rtt: Dict[Tuple[int, int], List[float]] = defaultdict(list)
        # key = node_id → forwarded_count snapshot at end of warm-up
        self._baseline_fwd: Dict[int, float] = {}
        # Snapshot of neighbour lists at end of warm-up
        self._baseline_neighbours: Dict[int, List[int]] = {}

        self._warmup_complete: bool = False
        self._warmup_packet_count: int = 0

    # ============================================================ warm-up
    def learn_baseline(self, packets: List[Packet]) -> None:
        """
        Feed warm-up packets (already forwarded through a CLEAN topology,
        i.e. no wormhole) to build baseline statistics.
        """
        for pkt in packets:
            pair = (pkt.src, pkt.dst)
            self._baseline_hops[pair].append(pkt.hop_count)
            self._baseline_rtt[pair].append(pkt.rtt_estimate)
            self._warmup_packet_count += 1

        # Snapshot forwarding counts & neighbour lists
        for node in self.topology.nodes.values():
            self._baseline_fwd[node.id] = max(node.forwarded_count, 1)  # avoid /0
            self._baseline_neighbours[node.id] = list(node.neighbours)

        self._warmup_complete = True

    # ============================================================ detection
    def analyse_packet(self, packet: Packet) -> List[str]:
        """
        Run all detection rules on a single packet.
        Returns a list of alert names (empty = no anomaly detected).
        Only applies rules if the warm-up phase is complete.
        """
        if not self._warmup_complete:
            return []

        alerts: List[str] = []

        # Rule 1: Hop-Count Drop
        alert = self._rule_hop_count_drop(packet)
        if alert:
            alerts.append(alert)

        # Rule 2: RTT Anomaly
        alert = self._rule_rtt_anomaly(packet)
        if alert:
            alerts.append(alert)

        # Rule 3: Neighbour Inconsistency (checked once per packet src)
        alert = self._rule_neighbour_inconsistency(packet)
        if alert:
            alerts.append(alert)

        # Rule 4: Path Stretch Anomaly
        alert = self._rule_path_stretch(packet)
        if alert:
            alerts.append(alert)

        # Apply alerts to the packet
        packet.alerts = alerts
        packet.detected = len(alerts) > 0
        packet.confidence_score = len(alerts)
        
        if packet.confidence_score >= 3:
            packet.confidence_tier = "High"
        elif packet.confidence_score == 2:
            packet.confidence_tier = "Medium"
        elif packet.confidence_score == 1:
            packet.confidence_tier = "Low"
        else:
            packet.confidence_tier = "None"
            
        return alerts

    def check_forwarding_spikes(self) -> List[Tuple[int, str]]:
        """
        Rule 5: Forwarded-Packet Spike.
        Called AFTER all packets have been forwarded in a run.
        Returns list of (node_id, alert_name) for flagged nodes.
        """
        if not self._warmup_complete:
            return []

        alerts: List[Tuple[int, str]] = []
        for node in self.topology.nodes.values():
            baseline = self._baseline_fwd.get(node.id, 1)
            if node.forwarded_count > baseline * self.profile.forwarded_spike_factor:
                alerts.append((node.id, "FORWARDED_SPIKE"))
        return alerts

    # ============================================================ individual rules
    def _rule_hop_count_drop(self, pkt: Packet) -> Optional[str]:
        """Flag if hop count is significantly lower than the warm-up mean."""
        pair = (pkt.src, pkt.dst)
        baseline = self._baseline_hops.get(pair)
        if not baseline:
            return None
        mean_hops = sum(baseline) / len(baseline)
        if pkt.hop_count <= mean_hops - self.profile.hop_count_drop_threshold:
            return "HOP_COUNT_DROP"
        return None

    def _rule_rtt_anomaly(self, pkt: Packet) -> Optional[str]:
        """Flag if RTT is suspiciously low compared to baseline."""
        pair = (pkt.src, pkt.dst)
        baseline = self._baseline_rtt.get(pair)
        if not baseline:
            return None
        mean_rtt = sum(baseline) / len(baseline)
        if mean_rtt > 0 and pkt.rtt_estimate < mean_rtt / self.profile.rtt_anomaly_factor:
            return "RTT_ANOMALY"
        return None

    def _rule_neighbour_inconsistency(self, pkt: Packet) -> Optional[str]:
        """
        Flag if any node on the packet's path has 2 or more neighbours that are
        physically beyond the legitimate communication range.
        """
        threshold_dist = self.profile.comm_range * self.profile.neighbour_inconsistency_threshold
        for nid in pkt.path:
            node = self.topology.nodes[nid]
            inconsistent_count = 0
            for nb_id in node.neighbours:
                nb = self.topology.nodes[nb_id]
                if node.distance_to(nb) > threshold_dist:
                    inconsistent_count += 1
            if inconsistent_count >= 2:
                return "NEIGHBOUR_INCONSISTENCY"
        return None

    def _rule_path_stretch(self, pkt: Packet) -> Optional[str]:
        """
        Flag if the delay per hop is anomalously high.
        Encapsulation tunnels hide intermediate hops but preserve the physical delay
        of traversing them. As a result, the perceived delay per hop skyrockets.
        """
        pair = (pkt.src, pkt.dst)
        baseline_hops = self._baseline_hops.get(pair)
        baseline_rtt = self._baseline_rtt.get(pair)
        
        if not baseline_hops or not baseline_rtt:
            return None
            
        mean_hops = sum(baseline_hops) / len(baseline_hops)
        # RTT is roughly 2x one-way delay, so we estimate one-way baseline delay
        mean_delay = (sum(baseline_rtt) / len(baseline_rtt)) / 2.0
        
        if mean_hops > 0 and pkt.hop_count > 0:
            expected_delay_per_hop = mean_delay / mean_hops
            actual_delay_per_hop = pkt.total_delay / pkt.hop_count
            
            # If the tunnel delay per hop is massively stretched compared to baseline
            if expected_delay_per_hop > 0:
                stretch = actual_delay_per_hop / expected_delay_per_hop
                if stretch > self.profile.path_stretch_threshold:
                    return "PATH_STRETCH_ANOMALY"
        return None

    def reset(self) -> None:
        """Reset baseline data for a new experiment run."""
        self._baseline_hops.clear()
        self._baseline_rtt.clear()
        self._baseline_fwd.clear()
        self._baseline_neighbours.clear()
        self._warmup_complete = False
        self._warmup_packet_count = 0
