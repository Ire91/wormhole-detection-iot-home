"""Loader to convert a public dataset (e.g., UNSW-NB15) into a format suitable
for the local wormhole detector detector pipeline.

This is intentionally lightweight and robust to schema variations. It maps a
public dataset row into a minimal packet representation with the fields the UI
expects:
- packet_id, src, dst, hop_count, total_delay, traversed_wormhole, detected,
  confidence_tier, alerts, is_attack
"""
import csv
import hashlib
import os
import random
from typing import List, Dict, Any


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def _ip_to_int(ip: str, max_id: int = 2**16 - 1) -> int:
    if not ip:
        return random.randint(1, max_id)
    h = hashlib.sha256(ip.encode("utf-8")).hexdigest()
    val = int(h[:8], 16)
    return val % (max_id + 1)


def _map_row_to_packet(row: Dict[str, Any], idx: int) -> Dict[str, Any]:
    # Common public dataset columns (UNSW-NB15-like) may include:
    # srcip, dstip, sport/dport, proto, dur, sbytes, dbytes, attack_cat/label
    src = _ip_to_int(row.get("src_ip") or row.get("srcip") or row.get("src") or "", max_id=65535)
    dst = _ip_to_int(row.get("dst_ip") or row.get("dstip") or row.get("dst") or "", max_id=65535)
    # Very rough guess for hops and delays since dataset doesn't include these in a simple form
    hop_count = _safe_int(row.get("hop_count"), default=random.randint(1, 5))
    total_delay = float(row.get("duration", 0) or random.uniform(0.5, 50.0))

    # Attack labeling
    is_attack = False
    label = row.get("label") or row.get("attack_cat") or row.get("class")
    if label:
        # Consider anything not explicitly "normal" as an attack in this mapping
        is_attack = str(label).lower() not in {"normal", "benign"}

    alerts = ""
    confidence_tier = None
    detected = False
    packet = {
        "packet_id": idx,
        "src": int(src),
        "dst": int(dst),
        "hop_count": int(hop_count),
        "total_delay": float(total_delay),
        "traversed_wormhole": False,
        "detected": bool(detected),
        "confidence_tier": confidence_tier,
        "alerts": alerts,
        "is_attack": is_attack,
    }
    return packet


def load_unsw_nb15_packets(dataset_root: str, max_packets: int = 100) -> List[Dict[str, Any]]:
    """Load UNSW-NB15 CSVs from dataset_root and convert to packet dicts.
    Returns a list of packet dicts suitable for feed into the UI/API.
    """
    # Find CSV files
    csv_files = []
    for root, _, files in os.walk(dataset_root):
        for f in files:
            if f.endswith(".csv"):
                csv_files.append(os.path.join(root, f))
    if not csv_files:
        return []
    # Take the first CSV as a representative subset
    csv_path = csv_files[0]
    packets: List[Dict[str, Any]] = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if max_packets is not None and i >= max_packets:
                break
            packets.append(_map_row_to_packet(row, i))
    return packets


__all__ = ["load_unsw_nb15_packets"]
