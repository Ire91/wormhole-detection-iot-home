======================================================================
  WORMHOLE DETECTION — DETAILED ANALYSIS FOR CHAPTER 4
======================================================================

======================================================================
  PROFILE: SMALL_FLAT
======================================================================

  --- Q1: RULE FIRE FREQUENCY ---
  Total packets: 455 (attack=305, normal=150, traversed_wormhole=23)

  Rule                             Total  On Attack  On Normal  On WH pkts
  ------------------------------ ------- ---------- ---------- -----------
  RTT_ANOMALY                          3          1          2           3

  --- Q2: PER-RUN BREAKDOWN ---

  Run 0:
    Packets: 91 (attack=61, normal=30)
    Traversed wormhole: 19 (20.9%)
    Detection Rate: 1.64% (1/61)
    FPR: 6.67% (2/30)
    Rules fired: {'RTT_ANOMALY': 3}
    Wormhole usage: attack_phase=12, warm-up_phase=7

  Run 1:
    Packets: 91 (attack=61, normal=30)
    Traversed wormhole: 4 (4.4%)
    Detection Rate: 0.00% (0/61)
    FPR: 0.00% (0/30)
    Rules fired: NONE
    Wormhole usage: attack_phase=4, warm-up_phase=0

  Run 2:
    Packets: 91 (attack=61, normal=30)
    Traversed wormhole: 0 (0.0%)
    Detection Rate: 0.00% (0/61)
    FPR: 0.00% (0/30)
    Rules fired: NONE
    Wormhole usage: attack_phase=0, warm-up_phase=0

  Run 3:
    Packets: 91 (attack=61, normal=30)
    Traversed wormhole: 0 (0.0%)
    Detection Rate: 0.00% (0/61)
    FPR: 0.00% (0/30)
    Rules fired: NONE
    Wormhole usage: attack_phase=0, warm-up_phase=0

  Run 4:
    Packets: 91 (attack=61, normal=30)
    Traversed wormhole: 0 (0.0%)
    Detection Rate: 0.00% (0/61)
    FPR: 0.00% (0/30)
    Rules fired: NONE
    Wormhole usage: attack_phase=0, warm-up_phase=0

  --- Q3: LATENCY ANALYSIS ---
  Overall:      mean=13.93ms, min=0.50ms, max=46.36ms
  Via wormhole: mean=7.86ms, min=0.50ms, max=21.70ms
  Normal path:  mean=14.26ms, min=2.10ms, max=46.36ms

  --- Q4: HOP COUNT ANALYSIS ---
  Via wormhole: mean=2.26 hops, min=1, max=3
  Normal path:  mean=1.61 hops, min=1, max=4

  --- Q5: FALSE POSITIVE BREAKDOWN (by rule) ---
  RTT_ANOMALY                        2 FPs (1.3% of normal packets)

======================================================================
  PROFILE: MEDIUM_APARTMENT
======================================================================

  --- Q1: RULE FIRE FREQUENCY ---
  Total packets: 1125 (attack=820, normal=305, traversed_wormhole=204)

  Rule                             Total  On Attack  On Normal  On WH pkts
  ------------------------------ ------- ---------- ---------- -----------
  NEIGHBOUR_INCONSISTENCY            464        336        128         204
  RTT_ANOMALY                         23         19          4          23
  HOP_COUNT_DROP                       1          1          0           1
  PATH_STRETCH_ANOMALY                 1          1          0           1

  --- Q2: PER-RUN BREAKDOWN ---

  Run 0:
    Packets: 225 (attack=164, normal=61)
    Traversed wormhole: 53 (23.6%)
    Detection Rate: 41.46% (68/164)
    FPR: 44.26% (27/61)
    Rules fired: {'NEIGHBOUR_INCONSISTENCY': 95, 'RTT_ANOMALY': 3}
    Wormhole usage: attack_phase=36, warm-up_phase=17

  Run 1:
    Packets: 225 (attack=164, normal=61)
    Traversed wormhole: 15 (6.7%)
    Detection Rate: 32.32% (53/164)
    FPR: 34.43% (21/61)
    Rules fired: {'NEIGHBOUR_INCONSISTENCY': 74, 'RTT_ANOMALY': 2}
    Wormhole usage: attack_phase=11, warm-up_phase=4

  Run 2:
    Packets: 225 (attack=164, normal=61)
    Traversed wormhole: 16 (7.1%)
    Detection Rate: 32.32% (53/164)
    FPR: 37.70% (23/61)
    Rules fired: {'NEIGHBOUR_INCONSISTENCY': 76, 'RTT_ANOMALY': 2}
    Wormhole usage: attack_phase=10, warm-up_phase=6

  Run 3:
    Packets: 225 (attack=164, normal=61)
    Traversed wormhole: 78 (34.7%)
    Detection Rate: 56.10% (92/164)
    FPR: 50.82% (31/61)
    Rules fired: {'NEIGHBOUR_INCONSISTENCY': 123, 'RTT_ANOMALY': 9, 'HOP_COUNT_DROP': 1, 'PATH_STRETCH_ANOMALY': 1}
    Wormhole usage: attack_phase=52, warm-up_phase=26

  Run 4:
    Packets: 225 (attack=164, normal=61)
    Traversed wormhole: 42 (18.7%)
    Detection Rate: 42.68% (70/164)
    FPR: 42.62% (26/61)
    Rules fired: {'NEIGHBOUR_INCONSISTENCY': 96, 'RTT_ANOMALY': 7}
    Wormhole usage: attack_phase=31, warm-up_phase=11

  --- Q3: LATENCY ANALYSIS ---
  Overall:      mean=27.88ms, min=0.80ms, max=73.08ms
  Via wormhole: mean=24.30ms, min=0.80ms, max=46.35ms
  Normal path:  mean=28.67ms, min=1.23ms, max=73.08ms

  --- Q4: HOP COUNT ANALYSIS ---
  Via wormhole: mean=2.87 hops, min=1, max=4
  Normal path:  mean=2.01 hops, min=1, max=4

  --- Q5: FALSE POSITIVE BREAKDOWN (by rule) ---
  NEIGHBOUR_INCONSISTENCY          128 FPs (42.0% of normal packets)
  RTT_ANOMALY                        4 FPs (1.3% of normal packets)

======================================================================
  PROFILE: LARGE_HOUSE
======================================================================

  --- Q1: RULE FIRE FREQUENCY ---
  Total packets: 3000 (attack=2245, normal=755, traversed_wormhole=330)

  Rule                             Total  On Attack  On Normal  On WH pkts
  ------------------------------ ------- ---------- ---------- -----------
  NEIGHBOUR_INCONSISTENCY            723        538        185         265
  RTT_ANOMALY                         23         18          5          23
  PATH_STRETCH_ANOMALY                 8          6          2           8
  HOP_COUNT_DROP                       2          1          1           2

  --- Q2: PER-RUN BREAKDOWN ---

  Run 0:
    Packets: 600 (attack=449, normal=151)
    Traversed wormhole: 117 (19.5%)
    Detection Rate: 28.29% (127/449)
    FPR: 25.17% (38/151)
    Rules fired: {'RTT_ANOMALY': 8, 'NEIGHBOUR_INCONSISTENCY': 165, 'HOP_COUNT_DROP': 1, 'PATH_STRETCH_ANOMALY': 2}
    Wormhole usage: attack_phase=94, warm-up_phase=23

  Run 1:
    Packets: 600 (attack=449, normal=151)
    Traversed wormhole: 65 (10.8%)
    Detection Rate: 0.22% (1/449)
    FPR: 0.00% (0/151)
    Rules fired: {'RTT_ANOMALY': 1}
    Wormhole usage: attack_phase=45, warm-up_phase=20

  Run 2:
    Packets: 600 (attack=449, normal=151)
    Traversed wormhole: 62 (10.3%)
    Detection Rate: 31.63% (142/449)
    FPR: 25.17% (38/151)
    Rules fired: {'NEIGHBOUR_INCONSISTENCY': 180, 'RTT_ANOMALY': 10, 'PATH_STRETCH_ANOMALY': 5, 'HOP_COUNT_DROP': 1}
    Wormhole usage: attack_phase=48, warm-up_phase=14

  Run 3:
    Packets: 600 (attack=449, normal=151)
    Traversed wormhole: 30 (5.0%)
    Detection Rate: 12.03% (54/449)
    FPR: 15.89% (24/151)
    Rules fired: {'NEIGHBOUR_INCONSISTENCY': 78, 'RTT_ANOMALY': 1}
    Wormhole usage: attack_phase=19, warm-up_phase=11

  Run 4:
    Packets: 600 (attack=449, normal=151)
    Traversed wormhole: 56 (9.3%)
    Detection Rate: 47.88% (215/449)
    FPR: 56.29% (85/151)
    Rules fired: {'NEIGHBOUR_INCONSISTENCY': 300, 'RTT_ANOMALY': 3, 'PATH_STRETCH_ANOMALY': 1}
    Wormhole usage: attack_phase=42, warm-up_phase=14

  --- Q3: LATENCY ANALYSIS ---
  Overall:      mean=61.28ms, min=1.00ms, max=222.88ms
  Via wormhole: mean=46.85ms, min=1.00ms, max=178.84ms
  Normal path:  mean=63.06ms, min=2.34ms, max=222.88ms

  --- Q4: HOP COUNT ANALYSIS ---
  Via wormhole: mean=3.31 hops, min=1, max=8
  Normal path:  mean=2.79 hops, min=1, max=9

  --- Q5: FALSE POSITIVE BREAKDOWN (by rule) ---
  NEIGHBOUR_INCONSISTENCY          185 FPs (24.5% of normal packets)
  RTT_ANOMALY                        5 FPs (0.7% of normal packets)
  PATH_STRETCH_ANOMALY               2 FPs (0.3% of normal packets)
  HOP_COUNT_DROP                     1 FPs (0.1% of normal packets)

  Detailed analysis CSV: C:\Users\Ireoluwa\FYP\output\detailed_analysis.csv

======================================================================
  ANALYSIS COMPLETE
======================================================================
