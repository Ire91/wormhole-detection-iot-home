"""
link.py – Network links between IoT nodes.

Link      – normal radio link; delay derived from Euclidean distance.
WormholeLink – malicious tunnel with artificially low latency.
"""

from __future__ import annotations
import math


class Link:
    """A legitimate wireless link between two mesh nodes."""

    # Propagation-speed factor: ms of delay per unit of Euclidean distance.
    # Adjust this to make the simulated network "faster" or "slower".
    DELAY_PER_UNIT_DISTANCE: float = 0.5  # ms

    def __init__(self, node_a_id: int, node_b_id: int, distance: float):
        self.node_a: int = node_a_id
        self.node_b: int = node_b_id
        self.distance: float = distance
        self.delay: float = distance * self.DELAY_PER_UNIT_DISTANCE  # milliseconds
        self.is_wormhole: bool = False

    def other(self, node_id: int) -> int:
        """Return the ID of the node on the other end of this link."""
        return self.node_b if node_id == self.node_a else self.node_a

    def __repr__(self) -> str:
        return (f"Link({self.node_a}<->{self.node_b}, "
                f"dist={self.distance:.1f}, delay={self.delay:.1f}ms)")


class WormholeLink(Link):
    """
    A covert tunnel between two colluding attacker nodes.

    Attack Modes:
      • out-of-band (default) – Fast tunnel, bypasses intermediate hops. 
        Hop count increment is +1.
      • encapsulation – Tunnel hides intermediate hops but packet delay is normal.
        Hop count increment is +1, delay is real_distance based.
      • intermittent – Tunnel toggles on and off randomly (50% chance per packet)
        to evade detection by baseline learning.

    Customisation:
      • tunnel_delay – lower values make the wormhole harder to detect via
        RTT alone; higher values are more "realistic" but easier to catch.
    """

    def __init__(self, node_a_id: int, node_b_id: int,
                 real_distance: float, tunnel_delay: float = 1.0, 
                 attack_mode: str = "out-of-band"):
        super().__init__(node_a_id, node_b_id, real_distance)
        self.attack_mode = attack_mode
        self.tunnel_delay: float = tunnel_delay   # fixed low-latency tunnel (ms)
        self.is_wormhole = True
        
        # Initial setup based on mode
        if attack_mode == "encapsulation":
            self.delay = real_distance * self.DELAY_PER_UNIT_DISTANCE # normal delay
        else:
            self.delay = tunnel_delay # 'out-of-band' or 'intermittent' uses fast tunnel delay

    def get_actual_delay(self) -> float:
        """Returns the delay for a specific packet transmission, handling intermittent mode."""
        if self.attack_mode == "intermittent":
            import random
            if random.random() < 0.5:
                self.is_active = True
                return self.tunnel_delay
            else:
                self.is_active = False
                return self.distance * self.DELAY_PER_UNIT_DISTANCE # act like normal link
        return self.delay

    def __repr__(self) -> str:
        return (f"WormholeLink({self.node_a}<->{self.node_b}, "
                f"mode={self.attack_mode}) [WORMHOLE]")
