#!/usr/bin/env bash
set -euo pipefail

# ========= CONFIG =========
BENCH_DIR="benchmarks/epfl"
SCRIPT_NAME="resyn2"
LUT_K=6
OPTION="fpga-${LUT_K}"

PYTHON_BIN="python -m"
RUNNER="refs.run_ref"

RESULTS_ROOT="results/refs"
# ==========================

echo "=== RUN FPGA REFS ==="
echo "Script : ${SCRIPT_NAME}"
echo "LUT-K  : ${LUT_K}"
echo "Bench  : ${BENCH_DIR}"
echo "======================"

for design in ${BENCH_DIR}/*.blif; do
    name=$(basename "$design" .blif)
    result_file="${RESULTS_ROOT}/${SCRIPT_NAME}/${OPTION}/${name}/result.json"

    if [[ -f "${result_file}" ]]; then
        echo ">>> SKIP ${name} (exists)"
        continue
    fi

    echo
    echo ">>> Running ${name}"

    ${PYTHON_BIN} ${RUNNER} \
        --design_file "$design" \
        --script "${SCRIPT_NAME}" \
        --lut_k "${LUT_K}"
done

echo
echo "=== DONE ALL FPGA REFS ==="

