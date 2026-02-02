#!/usr/bin/env bash
set -euo pipefail

# ===== CONFIG =====
LUT_K=6
MAX_STEPS=20
SPACES=("standard" "extended")

#BENCH_DIR="benchmarks/epfl/arithmetic"
BENCH_DIR="benchmarks/epfl/random_control"

echo "== Run ALL Greedy =="
echo "LUT_K     = ${LUT_K}"
echo "MAX_STEPS = ${MAX_STEPS}"
echo "SPACES    = ${SPACES[*]}"
echo "BENCH_DIR = ${BENCH_DIR}"
echo

# ===== LOOP ALL DESIGNS =====
for blif in ${BENCH_DIR}/*.blif; do
    design=$(basename "${blif}" .blif)

    for space in "${SPACES[@]}"; do
        echo "--------------------------------------------"
        echo "Design : ${design}"
        echo "Space  : ${space}"
        echo "--------------------------------------------"

        python -m algorithms.greedy.main_greedy \
            --design "${design}" \
            --lut-k "${LUT_K}" \
            --space "${space}" \
            --max-steps "${MAX_STEPS}"

        echo
    done
done

echo "== ALL GREEDY RUNS DONE =="

