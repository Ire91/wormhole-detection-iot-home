# Hybrid Wormhole Attack Detection for IoT Home Networks

Final-year project, B.Sc. Computer Science, Covenant University (2026).
Supervisor: Dr. Abiodun Theresa.

A Python simulation and detection framework for wormhole attacks (a covert tunnel between two colluding nodes that distorts routing) in small residential IoT networks of 10 to 30 nodes. It combines a five-rule composite detector with a Random Forest baseline, evaluates both across three home layouts and three attack modes, and exposes the results through a Flask dashboard.

## What is in the project

- **Simulator** (`core/`, `simulation/`): custom Python network simulation with node placement, communication range, Dijkstra routing, warm-up traffic and wormhole injection. No external simulator is used.
- **Rule engine** (`detection/rule_engine.py`): five rules evaluated per packet against a baseline learned during a warm-up phase: hop-count drop, RTT anomaly, neighbour inconsistency, path stretch anomaly, forwarded-packet spike. Thresholds live in JSON profiles under `config/`.
- **ML baseline** (`train_ml_model.py`): Random Forest on the same four packet features (`hop_count`, `total_delay`, `rtt_estimate`, `path_length`), labelled by whether the packet actually crossed the tunnel, with a run-grouped train/test split to avoid topology leakage.
- **Experiment runner** (`metrics/`, `run_heterogeneity_experiment.py`): 3 profiles x 3 attack modes (out-of-band, encapsulation, intermittent) x 5 seeded runs = 45 runs.
- **Dashboard** (`app.py`, `templates/`, `static/`): Flask REST API with a canvas topology view and Chart.js charts.

## Main results

| Profile | Nodes | Wormhole detection rate (mean over 5 runs, by attack mode) | False positive rate |
|---|---|---|---|
| Small flat | 10 | 0.0% to 3.3% | up to 1.3% |
| Medium apartment | 20 | 11.0% to 16.7% | about 1.3% |
| Large house | 30 | 6.5% to 9.3% | 0.7% to 0.9% |

- Detection depends mainly on network topology, not attack type.
- The neighbour-inconsistency rule produced 874 of the 921 true positives (94.9%). The forwarded-packet spike rule never fired, so it remains unvalidated by these experiments.
- On the medium apartment held-out run, the Random Forest reached recall 0.50 at precision 0.40, against the rule engine's much lower detection rate but sub-2% false positive rate.

## Run it

Requires Python 3.10+ (developed on 3.13).

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Dashboard
python app.py                   # then open http://127.0.0.1:5000

# Single simulation from the command line
python main.py --profile config/medium_apartment.json --runs 1

# Reproduce the 45-run experiment, then retrain the ML baseline
python run_heterogeneity_experiment.py
python train_ml_model.py output_hetero
```

The dashboard loads Tailwind and Chart.js from CDNs, so it needs an internet connection. If you see a scikit-learn version warning when loading `models/rf_model.joblib`, retrain it with `train_ml_model.py`.

## Limitations

Results come from a custom simulation, not real hardware or a packet-level simulator such as NS-3. Detection rates for the rule engine are low in absolute terms, and the study evaluates and compares established detection signals rather than proposing a new algorithm.