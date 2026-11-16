"""
packet.py – Data packet transmitted across the mesh network.

Each packet records its journey so the detection engine and metrics logger
can analyse hop counts, path, delay, and whether it was flagged.
"""

from __future__ import annotations
from typing import List
import itertools


class Packet:
    """Represents a single data packet traversing the mesh."""

    _counter = itertools.count(1)  # auto-incrementing packet ID

    def __init__(self, src: int, dst: int, created_at: float):
        self.id: int = next(Packet._counter)
        self.src: int = src                        # source node ID
        self.dst: int = dst                        # destination node ID
        self.hop_count: int = 0                    # incremented at each forwarding hop
        self.path: List[int] = [src]               # ordered list of node IDs visited
        self.created_at: float = created_at        # simulation timestamp (seconds)
        self.arrived_at: float | None = None       # set when packet reaches dst
        self.total_delay: float = 0.0              # accumulated link delays (ms)
        self.is_attack_traffic: bool = False       # True if generated during attack phase
        self.traversed_wormhole: bool = False       # True if packet used a wormhole link

        # Detection results (filled in by the RuleEngine)
        self.alerts: List[str] = []                # names of rules that flagged this packet
        self.detected: bool = False                # True if ANY rule flagged this packet
        self.confidence_score: int = 0             # Number of rules that flagged it
        self.confidence_tier: str = "None"         # High (>=3), Medium (2), Low (1), None (0)

    @property
    def rtt_estimate(self) -> float:
        """Estimated round-trip time = 2 × one-way delay."""
        return self.total_delay * 2.0

    @property
    def latency(self) -> float | None:
        """End-to-end latency in simulation seconds (None if not yet arrived)."""
        if self.arrived_at is not None:
            return self.arrived_at - self.created_at
        return None

    @classmethod
    def reset_counter(cls) -> None:
        """Reset the auto-increment counter (call between experiment runs)."""
        cls._counter = itertools.count(1)

    def __repr__(self) -> str:
        status = "DELIVERED" if self.arrived_at is not None else "IN-FLIGHT"
        return (f"Packet(id={self.id}, {self.src}->{self.dst}, "
                f"hops={self.hop_count}, delay={self.total_delay:.2f}ms, {status})")
