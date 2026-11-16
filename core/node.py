"""
node.py – Represents a single IoT device in the smart-home mesh network.

Customisation:
  • Change node positions by modifying x, y when constructing.
  • Toggle is_attacker to mark a node as a wormhole endpoint.
"""

from __future__ import annotations
from typing import Dict, List, Optional


class Node:
    """A single IoT node in the mesh network."""

    def __init__(self, node_id: int, x: float, y: float, is_attacker: bool = False):
        self.id: int = node_id
        self.x: float = x                          # X-coordinate in the 2-D plane
        self.y: float = y                          # Y-coordinate in the 2-D plane
        self.is_attacker: bool = is_attacker       # True if this node is a wormhole endpoint

        # Neighbour IDs (populated during topology build)
        self.neighbours: List[int] = []

        # Routing table: destination_id -> next_hop_id
        self.routing_table: Dict[int, int] = {}

        # Shortest known hop-count to every other node (filled by Dijkstra)
        self.hop_counts: Dict[int, int] = {}

        # Count of packets forwarded through this node (for spike detection)
        self.forwarded_count: int = 0

    # ------------------------------------------------------------------ helpers
    def add_neighbour(self, neighbour_id: int) -> None:
        """Register a direct neighbour (symmetric – call on both sides)."""
        if neighbour_id not in self.neighbours:
            self.neighbours.append(neighbour_id)

    def reset_metrics(self) -> None:
        """Reset per-run counters (called between experiment runs)."""
        self.forwarded_count = 0

    def distance_to(self, other: "Node") -> float:
        """Euclidean distance to another node."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __repr__(self) -> str:
        role = " [ATTACKER]" if self.is_attacker else ""
        return f"Node({self.id}, pos=({self.x:.1f},{self.y:.1f}){role})"
