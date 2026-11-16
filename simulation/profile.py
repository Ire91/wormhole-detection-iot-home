"""
profile.py – Smart-home profile loaded from a JSON config file.

Each profile defines the network shape, traffic intensity, and detection
thresholds.  Profiles live in the config/ directory.

Customisation:
  • Edit any JSON file in config/ to change node count, area, thresholds, etc.
  • Add a new JSON file and pass its path to the ExperimentRunner.
"""

from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class Profile:
    """All parameters for one simulation scenario."""

    # -- identity
    name: str = "default"

    # -- topology
    num_nodes: int = 15
    area_size: float = 100.0       # side length of 2-D deployment area
    comm_range: float = 40.0       # radio range (Euclidean distance)

    # -- traffic
    traffic_rate: float = 5.0      # packets per second
    simulation_duration: float = 30.0   # total duration (seconds)
    warmup_duration: float = 10.0       # baseline-learning phase (seconds)

    # -- wormhole attack
    scenario: str = "defence"      # 'baseline', 'attack_only', 'defence'
    attack_mode: str = "out-of-band" # attack types: 'out-of-band', 'encapsulation', 'intermittent'
    wormhole_node_a: int = 0       # first attacker node ID (auto-picked if out of range)
    wormhole_node_b: int = 9       # second attacker node ID
    tunnel_delay: float = 1.0      # wormhole tunnel delay in ms

    # -- detection thresholds (profile-aware)
    hop_count_drop_threshold: int = 2       # flag if hop count drops by >= this
    rtt_anomaly_factor: float = 2.0         # flag if RTT < baseline / this factor
    neighbour_inconsistency_threshold: float = 1.5  # factor × comm_range
    path_stretch_threshold: float = 1.5     # flag if path_len / expected > this
    forwarded_spike_factor: float = 3.0     # flag if fwd_count > baseline × this

    # ---------------------------------------------------------------- I/O
    @classmethod
    def from_json(cls, filepath: str | Path) -> "Profile":
        """Load a profile from a JSON config file."""
        with open(filepath, "r") as f:
            data: Dict[str, Any] = json.load(f)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_json(self, filepath: str | Path) -> None:
        """Save this profile to a JSON file."""
        import dataclasses
        with open(filepath, "w") as f:
            json.dump(dataclasses.asdict(self), f, indent=2)

    def __repr__(self) -> str:
        return f"Profile({self.name}, nodes={self.num_nodes}, rate={self.traffic_rate}/s)"
