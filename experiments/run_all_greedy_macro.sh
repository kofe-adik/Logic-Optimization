#!/usr/bin/env bash
set -euo pipefail

# ===== CONFIG =====
LUT_K=6
MAX_SLOTS=5

#BENCH_DIR="benchmarks/epfl/arithmetic"
BENCH_DIR="benchmarks/epfl/random_control"

echo "== Run ALL Greedy MACRO =="
echo "LUT_K      = ${LUT_K}"
echo "MAX_SLOTS  = ${MAX_SLOTS}"
echo "BENCH_DIR  = ${BENCH_DIR}"
echo

# ===== LOOP ALL DESIGNS =====
for blif in ${BENCH_DIR}/*.blif; do
    design=$(basename "${blif}" .blif)

    echo "--------------------------------------------"
    echo "Design : ${design}"
    echo "Algo   : greedy_macro"
    echo "--------------------------------------------"

    python -m algorithms.subseq_greedy.main_greedy_macro \
        --design "${design}" \
        --lut-k "${LUT_K}" \
        --max-slots "${MAX_SLOTS}"

    echo
done

echo "== ALL GREEDY MACRO RUNS DONE =="
