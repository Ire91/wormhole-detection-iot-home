"""
train_ml_model.py
-----------------
Trains a Random Forest classifier to detect wormhole-traversing packets
as an ML baseline alongside the rule-based IDS.

Key design decisions:
  - Label: `traversed_wormhole` (not `is_attack`) — measures detection of
    packets that actually used the wormhole tunnel, matching the
    wormhole_detection_rate metric used in the rule engine evaluation.
  - Features: hop_count, total_delay, rtt_estimate, path_length — the four
    signals the rule engine already uses, so feature importance is directly
    comparable.
  - Split strategy: group-aware split by (profile, run) to prevent topology
    leakage; no two runs from the same topology appear in both train and test.
  - Output: saves model to models/rf_model.joblib and prints a per-profile
    breakdown so rules vs ML comparison is easy to read.
"""

import os
import glob
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, precision_score, recall_score, f1_score
import joblib

FEATURES = ["hop_count", "total_delay", "rtt_estimate", "path_length"]
TARGET   = "traversed_wormhole"


def load_all_packet_data(output_dir="output"):
    """Load every packet_metrics.csv and tag each row with profile + run."""
    frames = []
    pattern = os.path.join(output_dir, "**", "packet_metrics.csv")
    for path in glob.glob(pattern, recursive=True):
        parts = path.replace("\\", "/").split("/")
        # path looks like: output/<profile>/run_<n>/packet_metrics.csv
        try:
            profile = parts[-3]
            run_tag = parts[-2]           # e.g. "run_0"
            run_id  = int(run_tag.split("_")[1])
        except (IndexError, ValueError):
            profile = "unknown"
            run_id  = 0

        df = pd.read_csv(path)
        df["profile"] = profile
        df["run_id"]  = run_id
        df["group"]   = profile + "_run" + str(run_id)
        frames.append(df)

    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def prepare(df):
    """Cast columns, drop rows with missing values."""
    for col in FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # traversed_wormhole may be True/False or 'True'/'False'
    df[TARGET] = df[TARGET].astype(str).str.lower().map({"true": True, "false": False})

    df = df.dropna(subset=FEATURES + [TARGET])
    df[TARGET] = df[TARGET].astype(int)   # 1 = traversed wormhole, 0 = normal
    return df


def group_aware_split(df, test_groups=None, n_test_runs=1):
    """
    Hold out `n_test_runs` runs per profile as the test set.
    This prevents topology leakage: if a topology appears in train,
    it never appears in test.
    """
    all_groups = df["group"].unique()

    if test_groups is None:
        # For reproducibility, pick the highest-numbered run per profile
        test_groups = []
        for profile in df["profile"].unique():
            runs = df[df["profile"] == profile]["run_id"].unique()
            for run_id in sorted(runs)[-n_test_runs:]:
                test_groups.append(f"{profile}_run{run_id}")

    mask_test = df["group"].isin(test_groups)
    return df[~mask_test], df[mask_test], test_groups


def train_and_evaluate(output_dir="output"):
    print("=" * 60)
    print("  Wormhole IDS — ML Baseline (Random Forest)")
    print("=" * 60)

    # ── Load ────────────────────────────────────────────────────────────────
    print("\n[1/4] Loading packet data from", output_dir)
    raw = load_all_packet_data(output_dir)
    if raw is None or len(raw) == 0:
        print("ERROR: No packet_metrics.csv files found. Run simulations first.")
        return

    df = prepare(raw.copy())
    print(f"      Loaded {len(df)} packets across profiles: "
          f"{sorted(df['profile'].unique())}")
    print(f"      Wormhole packets: {df[TARGET].sum()} "
          f"({100*df[TARGET].mean():.1f}%)")

    # ── Split ───────────────────────────────────────────────────────────────
    print("\n[2/4] Splitting by group (profile + run) to avoid topology leakage")
    train_df, test_df, test_groups = group_aware_split(df)
    print(f"      Train groups : {sorted(train_df['group'].unique())}")
    print(f"      Test  groups : {sorted(test_groups)}")
    print(f"      Train samples: {len(train_df)}   Test samples: {len(test_df)}")

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET]
    X_test  = test_df[FEATURES]
    y_test  = test_df[TARGET]

    # ── Train ───────────────────────────────────────────────────────────────
    print("\n[3/4] Training Random Forest (100 trees) …")
    clf = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    clf.fit(X_train, y_train)

    # Feature importance
    importances = dict(zip(FEATURES, clf.feature_importances_))
    print("      Feature importances:")
    for feat, imp in sorted(importances.items(), key=lambda x: -x[1]):
        print(f"        {feat:<20} {imp:.3f}")

    # ── Evaluate ─────────────────────────────────────────────────────────────
    print("\n[4/4] Evaluation on held-out test groups\n")
    y_pred = clf.predict(X_test)

    print("  Overall:")
    print(classification_report(y_test, y_pred,
                                target_names=["normal", "wormhole"],
                                zero_division=0))

    # Per-profile breakdown
    print("  Per-profile breakdown:")
    header = f"  {'Profile':<22} {'Precision':>9} {'Recall':>9} {'F1':>9} {'Support':>9}"
    print(header)
    print("  " + "-" * 62)
    for profile in sorted(test_df["profile"].unique()):
        mask = test_df["profile"] == profile
        yt = y_test[mask]
        yp = y_pred[mask.values]
        if yt.sum() == 0:
            print(f"  {profile:<22} {'—':>9} {'—':>9} {'—':>9} {len(yt):>9}  (no wormhole packets in test)")
            continue
        p = precision_score(yt, yp, zero_division=0)
        r = recall_score(yt, yp, zero_division=0)
        f = f1_score(yt, yp, zero_division=0)
        print(f"  {profile:<22} {p:>9.3f} {r:>9.3f} {f:>9.3f} {len(yt):>9}")

    # ── Save model ───────────────────────────────────────────────────────────
    os.makedirs("models", exist_ok=True)
    model_path = os.path.join("models", "rf_model.joblib")
    joblib.dump(clf, model_path)
    print(f"\nModel saved -> {model_path}")
    print("\nDone. Use this model alongside the rule engine for your complementary")
    print("detector story: rules = high precision, RF = higher recall.\n")


if __name__ == "__main__":
    # When run from the project root (where output/ lives)
    import sys
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "output"
    train_and_evaluate(output_dir)
