"""
topology.py – Mesh network topology: node placement, link creation,
Dijkstra routing, wormhole injection, and packet forwarding.

Customisation:
  • num_nodes      – number of IoT devices in the mesh.
  • area_size      – side-length of the square deployment area.
  • comm_range     – maximum radio range; nodes within this distance
                     are connected by a legitimate link.
  • Call inject_wormhole() to add a covert tunnel between any two nodes.
"""

from __future__ import annotations
import heapq
import math
import random
from typing import Dict, List, Optional, Tuple

from core.node import Node
from core.link import Link, WormholeLink
from core.packet import Packet


class Topology:
    """
    Builds and maintains the mesh network graph.

    Lifecycle
    ---------
    1. generate_mesh()       – place nodes, create links, run Dijkstra.
    2. inject_wormhole()     – (optional) add a wormhole & re-route.
    3. remove_wormhole()     – remove the wormhole & restore routes.
    4. forward_packet(pkt)   – simulate multi-hop forwarding of one packet.
    """

    def __init__(self, seed: int | None = None):
        self.nodes: Dict[int, Node] = {}
        self.links: List[Link] = []
        self.wormhole_link: Optional[WormholeLink] = None
        self._adjacency: Dict[int, List[Tuple[int, Link]]] = {}  # node_id -> [(neighbour_id, Link)]
        self._seed = seed

    # ============================================================ mesh build
    def generate_mesh(self, num_nodes: int, area_size: float,
                      comm_range: float) -> None:
        """
        Randomly place *num_nodes* in a square area and connect those
        within *comm_range*.  Ensures the graph is connected by retrying
        with a new layout if needed (max 50 attempts).
        """
        rng = random.Random(self._seed)

        for attempt in range(50):
            self.nodes.clear()
            self.links.clear()
            self._adjacency.clear()

            # --- place nodes randomly
            for i in range(num_nodes):
                x = rng.uniform(0, area_size)
                y = rng.uniform(0, area_size)
                self.nodes[i] = Node(i, x, y)
                self._adjacency[i] = []

            # --- create links for nodes within comm_range
            for i in range(num_nodes):
                for j in range(i + 1, num_nodes):
                    dist = self.nodes[i].distance_to(self.nodes[j])
                    if dist <= comm_range:
                        link = Link(i, j, dist)
                        self.links.append(link)
                        self._adjacency[i].append((j, link))
                        self._adjacency[j].append((i, link))
                        self.nodes[i].add_neighbour(j)
                        self.nodes[j].add_neighbour(i)

            if self._is_connected():
                break
            # If not connected, try a new random layout
            if self._seed is not None:
                self._seed += 1000
                rng = random.Random(self._seed)
        else:
            raise RuntimeError(
                f"Could not generate a connected mesh with {num_nodes} nodes, "
                f"area={area_size}, range={comm_range} after 50 attempts. "
                "Try increasing comm_range or reducing area_size."
            )

        self.compute_routes()

    # ============================================================ wormhole
    def inject_wormhole(self, node_a_id: int, node_b_id: int,
                        tunnel_delay: float = 1.0, attack_mode: str = "out-of-band") -> WormholeLink:
        """
        Create a covert wormhole tunnel between two nodes and recompute
        routes so that Dijkstra naturally picks up the shortcut.
        """
        a = self.nodes[node_a_id]
        b = self.nodes[node_b_id]
        a.is_attacker = True
        b.is_attacker = True
        real_dist = a.distance_to(b)

        wh = WormholeLink(node_a_id, node_b_id, real_dist, tunnel_delay, attack_mode)
        self.wormhole_link = wh
        self.links.append(wh)
        self._adjacency[node_a_id].append((node_b_id, wh))
        self._adjacency[node_b_id].append((node_a_id, wh))

        # The attackers "see" each other as neighbours now
        a.add_neighbour(node_b_id)
        b.add_neighbour(node_a_id)

        # Recompute routes — Dijkstra will prefer the low-delay shortcut
        self.compute_routes()
        return wh

    def remove_wormhole(self) -> None:
        """Remove the wormhole link and restore clean routes."""
        if self.wormhole_link is None:
            return
        wh = self.wormhole_link
        self.links = [l for l in self.links if l is not wh]
        self._adjacency[wh.node_a] = [
            (n, l) for n, l in self._adjacency[wh.node_a] if l is not wh
        ]
        self._adjacency[wh.node_b] = [
            (n, l) for n, l in self._adjacency[wh.node_b] if l is not wh
        ]
        self.nodes[wh.node_a].neighbours = [
            n for n in self.nodes[wh.node_a].neighbours if n != wh.node_b
        ]
        self.nodes[wh.node_b].neighbours = [
            n for n in self.nodes[wh.node_b].neighbours if n != wh.node_a
        ]
        self.nodes[wh.node_a].is_attacker = False
        self.nodes[wh.node_b].is_attacker = False
        self.wormhole_link = None
        self.compute_routes()

    # ============================================================ routing
    def compute_routes(self) -> None:
        """
        Run Dijkstra from every node to fill routing tables and hop counts.
        Weight = hop count (each link = 1 hop).
        """
        for src_id in self.nodes:
            dist, prev = self._dijkstra(src_id)
            node = self.nodes[src_id]
            node.routing_table.clear()
            node.hop_counts.clear()
            for dst_id in self.nodes:
                if dst_id == src_id:
                    continue
                if dst_id not in prev:
                    continue  # unreachable (should not happen in connected graph)
                node.hop_counts[dst_id] = dist[dst_id]
                # Trace back to find next hop
                current = dst_id
                while prev.get(current) != src_id and prev.get(current) is not None:
                    current = prev[current]
                node.routing_table[dst_id] = current

    def get_shortest_hop_count(self, src: int, dst: int) -> int:
        """Hop count according to current routing (may include wormhole)."""
        return self.nodes[src].hop_counts.get(dst, -1)

    def get_path(self, src: int, dst: int) -> List[int]:
        """Return the full shortest path (list of node IDs) from src to dst."""
        path = [src]
        current = src
        visited = set()
        while current != dst:
            if current in visited:
                break  # safety: avoid infinite loop
            visited.add(current)
            next_hop = self.nodes[current].routing_table.get(dst)
            if next_hop is None:
                break
            path.append(next_hop)
            current = next_hop
        return path

    # ============================================================ forwarding
    def forward_packet(self, packet: Packet) -> Packet:
        """
        Simulate forwarding a packet from src to dst along the shortest path.
        Populates packet.path, hop_count, total_delay, traversed_wormhole.
        Increments forwarded_count on each intermediate node.
        """
        current = packet.src
        while current != packet.dst:
            next_hop = self.nodes[current].routing_table.get(packet.dst)
            if next_hop is None:
                break  # destination unreachable

            # Find the link between current and next_hop
            link = self._find_link(current, next_hop)
            if link is None:
                break

            # Accumulate delay and hop
            if hasattr(link, 'get_actual_delay'):
                actual_delay = link.get_actual_delay()
                packet.total_delay += actual_delay
                if getattr(link, 'is_active', True): # if intermittent and inactive, don't count as WH
                    packet.traversed_wormhole = True
            else:
                packet.total_delay += link.delay
                if link.is_wormhole:
                    packet.traversed_wormhole = True
            
            packet.hop_count += 1
            packet.path.append(next_hop)

            # Count forwarding (only on intermediate nodes, not src/dst)
            if next_hop != packet.dst:
                self.nodes[next_hop].forwarded_count += 1

            current = next_hop

        if current == packet.dst:
            packet.arrived_at = packet.created_at + (packet.total_delay / 1000.0)

        return packet

    # ============================================================ internals
    def _dijkstra(self, src: int) -> Tuple[Dict[int, int], Dict[int, int]]:
        """Standard Dijkstra with hop-count weights (each edge = 1)."""
        dist: Dict[int, int] = {src: 0}
        prev: Dict[int, int] = {}
        pq = [(0, src)]
        visited = set()

        while pq:
            d, u = heapq.heappop(pq)
            if u in visited:
                continue
            visited.add(u)
            for v, link in self._adjacency.get(u, []):
                new_dist = d + 1  # hop count weight
                if v not in dist or new_dist < dist[v]:
                    dist[v] = new_dist
                    prev[v] = u
                    heapq.heappush(pq, (new_dist, v))

        return dist, prev

    def _find_link(self, a: int, b: int) -> Optional[Link]:
        """Find the link object between two adjacent nodes."""
        for neighbour_id, link in self._adjacency.get(a, []):
            if neighbour_id == b:
                return link
        return None

    def _is_connected(self) -> bool:
        """BFS to check if all nodes are reachable from node 0."""
        if not self.nodes:
            return False
        start = next(iter(self.nodes))
        visited = set()
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            for neighbour_id, _ in self._adjacency.get(node, []):
                if neighbour_id not in visited:
                    queue.append(neighbour_id)
        return len(visited) == len(self.nodes)

    def reset_node_metrics(self) -> None:
        """Reset per-run counters on all nodes."""
        for node in self.nodes.values():
            node.reset_metrics()

    def __repr__(self) -> str:
        wh = " +WORMHOLE" if self.wormhole_link else ""
        return f"Topology({len(self.nodes)} nodes, {len(self.links)} links{wh})"
