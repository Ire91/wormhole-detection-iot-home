"""
traffic_generator.py – Generates normal and attack-phase traffic.

Normal traffic: random src→dst pairs at the configured rate.
Attack traffic: same generation, but a wormhole link is active so packets
                may (or may not) naturally route through the shortcut.

Customisation:
  • Adjust profile.traffic_rate to change packet density.
  • Adjust profile.simulation_duration / warmup_duration for longer runs.
"""

from __future__ import annotations
import random
from typing import List

from core.packet import Packet
from core.topology import Topology
from simulation.profile import Profile


class TrafficGenerator:
    """Creates a time-ordered list of Packet objects for one simulation run."""

    def __init__(self, topology: Topology, profile: Profile,
                 seed: int | None = None):
        self.topology = topology
        self.profile = profile
        self.rng = random.Random(seed)

    # ------------------------------------------------------------ public API
    def generate(self) -> List[Packet]:
        """
        Generate the full packet sequence for the simulation.

        Timeline
        --------
        [0 … warmup_duration)              → warm-up (normal) traffic
        [warmup_duration … simulation_end)  → attack traffic (wormhole active)

        Every packet is stamped with its creation time.
        """
        packets: List[Packet] = []
        node_ids = list(self.topology.nodes.keys())
        interval = 1.0 / self.profile.traffic_rate  # seconds between packets
        t = 0.0
        warmup_end = self.profile.warmup_duration
        sim_end = self.profile.simulation_duration

        while t < sim_end:
            src = self.rng.choice(node_ids)
            dst = self.rng.choice([n for n in node_ids if n != src])
            pkt = Packet(src, dst, created_at=t)

            # Mark packets created after the warm-up as potential attack traffic
            if t >= warmup_end:
                pkt.is_attack_traffic = True

            packets.append(pkt)
            t += interval

        return packets

    def generate_warmup_only(self) -> List[Packet]:
        """Generate ONLY warm-up (baseline) traffic — no attack phase."""
        packets: List[Packet] = []
        node_ids = list(self.topology.nodes.keys())
        interval = 1.0 / self.profile.traffic_rate
        t = 0.0

        while t < self.profile.warmup_duration:
            src = self.rng.choice(node_ids)
            dst = self.rng.choice([n for n in node_ids if n != src])
            pkt = Packet(src, dst, created_at=t)
            packets.append(pkt)
            t += interval

        return packets
