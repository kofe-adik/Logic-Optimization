#!/usr/bin/env bash
set -euo pipefail

# ===== CONFIG =====
LUT_K=6
SPACE="superset"
REF="resyn2"
SLOTS=5
POOL=300
JOBS=30
BENCH_DIR="benchmarks/epfl/arithmetic"

# ===== CIRCUITS TO RUN =====
#circuits=(adder bar div hyp log2 max multiplier sin sqrt square)
circuits=(adder div hyp)
# ===== LOOP ALL DESIGNS =====
for circuit in "${circuits[@]}"; do
    blif="${BENCH_DIR}/${circuit}.blif"

    if [[ ! -f "$blif" ]]; then
        echo "== SKIP (not found): $circuit =="
        continue
    fi

    echo "== RUN $circuit =="

    python3 -m algorithms.adaptive_greedy.main_adaptive_greedy \
        --design "$circuit" \
        --lut-k "$LUT_K" \
        --space "$SPACE" \
        --ref "$REF" \
        --max-steps "$SLOTS" \
        --pool-size "$POOL" \
        --n-jobs "$JOBS"

    echo
done

echo "== ALL GREEDY RUNS DONE =="

