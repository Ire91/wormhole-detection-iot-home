"""
app.py - Flask Web Dashboard for Wormhole Detection Prototype

Usage:
  python app.py
  Go to http://127.0.0.1:5000 in your browser.
"""

from flask import Flask, send_from_directory, jsonify, request
import logging
from flask_cors import CORS
import os
import json
import csv
import joblib

from simulation.profile import Profile
from metrics.experiment_runner import ExperimentRunner
from core.packet import Packet

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("app")

OUTPUT_DIR = "output"
CONFIG_DIR = "config"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)

# ======================================================================
# HELPERS
# ======================================================================

def _read_csv(path: str):
    if not os.path.isfile(path):
        return []
    with open(path, newline="") as f:
        return list(csv.DictReader(f))

def _histogram(values, bins=10):
    if not values:
        return []
    lo, hi = min(values), max(values)
    if lo == hi:
        return [{"label": f"{lo:.1f}", "count": len(values)}]
    width = (hi - lo) / bins
    counts = [0] * bins
    for v in values:
        idx = min(int((v - lo) / width), bins - 1)
        counts[idx] += 1
    return [
        {"label": f"{lo + i*width:.1f}\u2013{lo + (i+1)*width:.1f}", "count": counts[i]}
        for i in range(bins)
    ]

# ======================================================================
# API ENDPOINTS
# ======================================================================

@app.route("/")
def index():
    """Serve the polished dashboard from templates/."""
    return send_from_directory(os.path.join(os.path.dirname(__file__), "templates"), "index.html")

@app.route("/api/profiles", methods=["GET"])
def get_profiles():
    """List available simulation profiles with metadata."""
    profiles = []
    if os.path.exists(CONFIG_DIR):
        for filename in sorted(os.listdir(CONFIG_DIR)):
            if filename.endswith(".json"):
                path = os.path.join(CONFIG_DIR, filename)
                try:
                    p = Profile.from_json(path)
                    profiles.append({"name": p.name, "num_nodes": p.num_nodes})
                except Exception:
                    logger.exception("Failed to load profile from %s", path)
    return jsonify(profiles)

@app.route("/api/run", methods=["POST"])
def run_simulation():
    """Run a fresh simulation and return rich metrics for the dashboard charts."""
    data = request.json or {}
    profile_name = data.get("profile", "small_flat")
    attack_mode = data.get("attack_mode", "out-of-band")
    scenario = data.get("scenario", "defence")
    try:
        seed = int(data.get("seed", 42))
    except Exception:
        seed = 42

    allowed_attacks = {"out-of-band", "in-band", "encapsulation", "intermittent"}
    allowed_scenarios = {"defence", "attack_only", "baseline"}
    if attack_mode not in allowed_attacks:
        attack_mode = "out-of-band"
    if scenario not in allowed_scenarios:
        scenario = "defence"

    config_path = os.path.join(CONFIG_DIR, f"{profile_name}.json")
    if not os.path.exists(config_path):
        return jsonify({"error": f"Profile {profile_name} not found."}), 404

    try:
        profile = Profile.from_json(config_path)
        profile.attack_mode = attack_mode
        profile.scenario = scenario
        logger.info("Running simulation: profile=%s, attack=%s, scenario=%s, seed=%d",
                    profile.name, attack_mode, scenario, seed)

        Packet.reset_counter()
        runner = ExperimentRunner(profile, output_dir=OUTPUT_DIR)
        summaries = runner.run(num_runs=1, base_seed=seed)
        summary = summaries[0]

        run_dir = os.path.join(OUTPUT_DIR, profile.name, "run_0")
        packets = _read_csv(os.path.join(run_dir, "packet_metrics.csv"))
        nodes_csv = _read_csv(os.path.join(run_dir, "node_metrics.csv"))

        node_positions = []
        for n in nodes_csv:
            node_positions.append({
                "id": int(n["node_id"]),
                "x": float(n["x"]),
                "y": float(n["y"]),
                "is_attacker": n["is_attacker"] == "True",
                "neighbours": [int(x) for x in n["neighbours"].split(";") if x],
                "forwarded": int(n["forwarded_count"]),
            })

        attack_pkts = [p for p in packets if p.get("is_attack") == "True"][-100:]
        packet_feed = []
        for p in attack_pkts:
            packet_feed.append({
                "id": int(p["packet_id"]),
                "src": int(p["src"]),
                "dst": int(p["dst"]),
                "hops": int(p["hop_count"]),
                "delay": round(float(p["total_delay"]), 2),
                "wormhole": p["traversed_wormhole"] == "True",
                "detected": p["detected"] == "True",
                "confidence": p.get("confidence_tier", "None"),
                "alerts": p["alerts"].replace(";", ", "),
            })

        confidence_counts = {"High": 0, "Medium": 0, "Low": 0, "None": 0}
        for p in packets:
            if p.get("is_attack") == "True":
                tier = p.get("confidence_tier", "None")
                if tier in confidence_counts:
                    confidence_counts[tier] += 1

        rule_counts = {
            "HOP_COUNT_DROP": 0, "RTT_ANOMALY": 0,
            "NEIGHBOUR_INCONSISTENCY": 0, "PATH_STRETCH_ANOMALY": 0,
            "FORWARDED_SPIKE": 0,
        }
        for p in packets:
            for rule in p.get("alerts", "").split(";"):
                rule = rule.strip()
                if rule in rule_counts:
                    rule_counts[rule] += 1

        five_rule_total = sum(rule_counts.values())
        hop_baseline = sum(1 for p in packets if int(p.get("hop_count", 0)) >= 3)

        all_delays = [float(p["total_delay"]) for p in packets if p.get("total_delay")]
        latency_histogram = _histogram(all_delays, bins=10)

        total_packets = len(packets)
        total_attacks = sum(1 for p in packets if str(p.get("is_attack")).lower() == "true")
        detected_attacks = sum(1 for p in packets if str(p.get("is_attack")).lower() == "true" and str(p.get("detected")).lower() == "true")
        false_positives = sum(1 for p in packets if str(p.get("is_attack")).lower() != "true" and str(p.get("detected")).lower() == "true")
        non_attacks = total_packets - total_attacks
        detection_rate = (detected_attacks / total_attacks * 100) if total_attacks > 0 else 0.0
        false_positive_rate = (false_positives / non_attacks * 100) if non_attacks > 0 else 0.0

        # Batch predict ML model if available
        ml_model_path = os.path.join("models", "rf_model.joblib")
        ml_model = joblib.load(ml_model_path) if os.path.exists(ml_model_path) else None

        ml_detected_attacks = 0
        ml_false_positives = 0

        if ml_model and len(packets) > 0:
            import pandas as pd
            features = ['hop_count', 'total_delay', 'rtt_estimate', 'path_length']
            df = pd.DataFrame(packets)
            # Ensure columns exist and format to numeric
            for col in features:
                if col not in df: df[col] = 0
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            preds = ml_model.predict(df[features])
            for idx, p in enumerate(packets):
                is_attack = str(p.get("is_attack")).lower() == "true"
                pred_attack = bool(preds[idx])
                if pred_attack and is_attack:
                    ml_detected_attacks += 1
                elif pred_attack and not is_attack:
                    ml_false_positives += 1
                # Attach to packet feed data
                if len(packet_feed) > 0 and idx >= len(packets) - len(packet_feed):
                    packet_feed[idx - (len(packets) - len(packet_feed))]["ml_detected"] = pred_attack

        ml_detection_rate = (ml_detected_attacks / total_attacks * 100) if total_attacks > 0 else 0.0
        ml_fpr = (ml_false_positives / non_attacks * 100) if non_attacks > 0 else 0.0

        return jsonify({
            "summary": summary,
            "scenario": scenario,
            "attack_mode": attack_mode,
            "profile_name": profile.name,
            "num_nodes": profile.num_nodes,
            "nodes": node_positions,
            "packets": packets,
            "packet_feed": packet_feed,
            "confidence_counts": confidence_counts,
            "rule_counts": rule_counts,
            "rule_bar": {"five_rule_total": five_rule_total, "hop_baseline": hop_baseline},
            "latency_histogram": latency_histogram,
            "packets_analyzed": total_packets,
            "detection_rate": detection_rate,
            "false_positive_rate": false_positive_rate,
            "ml_available": ml_model is not None,
            "ml_detection_rate": ml_detection_rate,
            "ml_false_positive_rate": ml_fpr,
            "area_size": profile.area_size,
            "wormhole_endpoints": [profile.wormhole_node_a, profile.wormhole_node_b],
            "baseline_thresholds": {
                "rtt_anomaly_factor": profile.rtt_anomaly_factor,
                "hop_count_drop": profile.hop_count_drop_threshold,
                "stretch_threshold": profile.path_stretch_threshold,
                "fwd_spike_factor": profile.forwarded_spike_factor
            },
            "simulation_params": {
                "warmup_duration": profile.warmup_duration,
                "traffic_rate": profile.traffic_rate
            }
        })

    except Exception as e:
        logger.exception("Error during run_simulation")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/scan", methods=["POST"])
def scan_file():
    """Scan an uploaded CSV or JSON file with the 5 detection rules."""
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    packets = []
    try:
        if file.filename.endswith(".json"):
            packets = json.load(file)
        elif file.filename.endswith(".csv"):
            stream = file.stream.read().decode("utf-8").splitlines()
            packets = list(csv.DictReader(stream))
        else:
            return jsonify({"error": "Unsupported format. Upload JSON or CSV."}), 400
    except Exception as e:
        logger.exception("Failed to parse uploaded file")
        return jsonify({"error": f"Failed to parse file: {str(e)}"}), 400

    rule_counts = {
        "HOP_COUNT_DROP": 0, "RTT_ANOMALY": 0,
        "NEIGHBOUR_INCONSISTENCY": 0, "PATH_STRETCH_ANOMALY": 0,
        "FORWARDED_SPIKE": 0,
    }
    confidence_counts = {"High": 0, "Medium": 0, "Low": 0, "None": 0}
    packet_feed = []
    total_attacks = 0
    false_positives = 0
    true_positives = 0

    for idx, p in enumerate(packets):
        alerts = []
        hop_count = int(p.get("hop_count", p.get("hops", 0)))
        total_delay = float(p.get("total_delay", p.get("delay", 0.0)))
        forwarded_count = int(p.get("forwarded_count", 0))

        if hop_count == 1 and total_delay > 25.0:
            alerts.append("HOP_COUNT_DROP")
        if total_delay > 40.0:
            alerts.append("RTT_ANOMALY")
        if hop_count > 5:
            alerts.append("PATH_STRETCH_ANOMALY")
        if forwarded_count > 100:
            alerts.append("FORWARDED_SPIKE")
        neighbours = p.get("neighbours", [])
        if isinstance(neighbours, str):
            neighbours = [x for x in neighbours.replace("[","").replace("]","").split(",") if x.strip()]
        if len(neighbours) < 2 and hop_count == 1:
            alerts.append("NEIGHBOUR_INCONSISTENCY")

        score = len(alerts)
        confidence = "High" if score >= 3 else "Medium" if score == 2 else "Low" if score == 1 else "None"
        is_detected = score > 0

        if is_detected:
            for a in alerts:
                if a in rule_counts:
                    rule_counts[a] += 1
            confidence_counts[confidence] += 1

        is_attack = p.get("is_attack") in [True, "True", "true", "1", 1]
        if is_attack:
            total_attacks += 1
            if is_detected:
                true_positives += 1
        elif is_detected:
            false_positives += 1

        packet_feed.append({
            "id": int(p.get("packet_id", p.get("id", idx + 1))),
            "src": int(p.get("src", 0)),
            "dst": int(p.get("dst", 0)),
            "hops": hop_count,
            "delay": round(total_delay, 2),
            "wormhole": is_attack,
            "detected": is_detected,
            "confidence": confidence,
            "alerts": ", ".join(alerts),
        })

    total_packets = len(packets)
    non_attacks = total_packets - total_attacks
    detection_rate = (true_positives / total_attacks * 100) if total_attacks > 0 else 0.0
    false_positive_rate = (false_positives / non_attacks * 100) if non_attacks > 0 else 0.0

    # ML batch prediction
    ml_model_path = os.path.join("models", "rf_model.joblib")
    ml_model = joblib.load(ml_model_path) if os.path.exists(ml_model_path) else None

    ml_detected_attacks = 0
    ml_false_positives = 0

    if ml_model and len(packets) > 0:
        import pandas as pd
        features = ['hop_count', 'total_delay', 'rtt_estimate', 'path_length']
        df = pd.DataFrame(packets)
        for col in features:
            if col not in df: df[col] = 0
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        preds = ml_model.predict(df[features])
        for idx, p in enumerate(packets):
            is_attack = p.get("is_attack") in [True, "True", "true", "1", 1]
            pred_attack = bool(preds[idx])
            if pred_attack and is_attack:
                ml_detected_attacks += 1
            elif pred_attack and not is_attack:
                ml_false_positives += 1
            # Link pred_attack to packet feed if visible
            for feed_pkt in packet_feed:
                if feed_pkt["id"] == int(p.get("packet_id", p.get("id", idx + 1))):
                    feed_pkt["ml_detected"] = pred_attack
                    break

    ml_detection_rate = (ml_detected_attacks / total_attacks * 100) if total_attacks > 0 else 0.0
    ml_fpr = (ml_false_positives / non_attacks * 100) if non_attacks > 0 else 0.0

    all_delays = [float(p.get("total_delay", p.get("delay", 0.0))) for p in packets]
    latency_histogram = _histogram(all_delays, bins=10) if all_delays else []

    summary = {
        "total_packets": total_packets,
        "attack_packets": total_attacks,
        "normal_packets": non_attacks,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "detection_rate": detection_rate / 100.0,
        "false_positive_rate": false_positive_rate / 100.0,
        "avg_latency": sum(all_delays) / total_packets if total_packets > 0 else 0,
    }

    return jsonify({
        "summary": summary,
        "scenario": "scan",
        "attack_mode": "static",
        "profile_name": "Static Upload",
        "num_nodes": 0,
        "nodes": [],
        "packet_feed": sorted(packet_feed, key=lambda x: x["detected"], reverse=True)[:100],
        "confidence_counts": confidence_counts,
        "rule_counts": rule_counts,
        "rule_bar": {"five_rule_total": sum(rule_counts.values()), "hop_baseline": sum(1 for p in packets if int(p.get("hop_count", p.get("hops", 0))) >= 3)},
        "latency_histogram": latency_histogram,
        "packets_analyzed": total_packets,
        "detection_rate": detection_rate,
        "false_positive_rate": false_positive_rate,
        "ml_available": ml_model is not None,
        "ml_detection_rate": ml_detection_rate,
        "ml_false_positive_rate": ml_fpr,
    })





@app.route("/api/heterogeneity_results", methods=["GET"])
def get_heterogeneity_results():
    """Serve the 9-cell heterogeneity results from CSV if available."""
    csv_path = "heterogeneity_results.csv"
    if not os.path.isfile(csv_path):
        return jsonify({"error": "heterogeneity_results.csv not found. Run python run_heterogeneity_experiment.py first."}), 404
    rows = _read_csv(csv_path)
    results = []
    for r in rows:
        try:
            results.append({
                "profile": r["profile"],
                "attack_mode": r["attack_mode"],
                "wdr_mean": float(r["wdr_mean"]),
                "wdr_stdev": float(r["wdr_stdev"]),
                "fpr_mean": float(r["fpr_mean"]),
                "fpr_stdev": float(r["fpr_stdev"]),
                "latency_mean": float(r["latency_mean"]),
            })
        except (KeyError, ValueError):
            continue
    return jsonify(results)


if __name__ == "__main__":
    print("=" * 55)
    print("  Wormhole Detection Dashboard")
    print("  Open: http://localhost:5000")
    print("=" * 55)
    app.run(debug=True, port=5000)
