import argparse
import logging
from typing import List

from common.action_space.spaces import EXTENDED_MACRO_SPACE
from common.action_space.actions import MacroAction
from common.execution.design_eval import evaluate_fpga_design_macro
from common.storage.paths import (
    get_project_root,
    get_run_result_dir,
)
from common.storage.result_writer import write_result
from common.utils.logging_utils import setup_logger
from algorithms.subseq_greedy.greedy_search_macro import greedy_search_macro


def main():
    parser = argparse.ArgumentParser("Greedy MACRO logic optimization")
    parser.add_argument("--design", required=True)
    parser.add_argument("--lut-k", type=int, default=6)
    parser.add_argument("--max-slots", type=int, default=5)

    args = parser.parse_args()

    # ===== option string =====
    option = f"lutk{args.lut_k}_macro_slots-{args.max_slots}"

    # ===== result dir =====
    result_dir = get_run_result_dir(
        algo_name="greedy_macro",
        option=option,
        design_name=args.design,
        run_id=None,
    )

    # ===== skip if exists =====
    if result_dir.exists() and any(result_dir.iterdir()):
        print(f"[SKIP] Result already exists: {result_dir}")
        return

    # ===== logging =====
    log_file = result_dir / "run.log"
    setup_logger(
        name="greedy_macro",
        log_file=log_file,
        level=logging.INFO,
    )
    logger = logging.getLogger("greedy_macro")

    # ===== macro space =====
    macro_space: List[MacroAction] = EXTENDED_MACRO_SPACE

    # ===== design file =====
    design_file = (
        get_project_root()
        / "benchmarks"
        / "epfl"
        / "arithmetic"
#        / "random_control"
        / f"{args.design}.blif"
    )

    logger.info("== Greedy MACRO optimization ==")
    logger.info("Design      : %s", args.design)
    logger.info("LUT K       : %d", args.lut_k)
    logger.info("Max slots   : %d", args.max_slots)
    logger.info("Macro count : %d", len(macro_space))
    logger.info("Result dir  : %s", result_dir)

    # ===== reference =====
    ref_metrics = evaluate_fpga_design_macro(
        design_file=str(design_file),
        macros=[],
        lut_k=args.lut_k,
    )

    logger.info(
        "Reference | LUT=%d LEVEL=%d",
        ref_metrics["lut"],
        ref_metrics["levels"],
    )

    # ===== run greedy macro =====
    result = greedy_search_macro(
        design_file=str(design_file),
        macro_space=macro_space,
        lut_k=args.lut_k,
        ref_metrics=ref_metrics,
        max_slots=args.max_slots,
    )

    # ===== write result =====
    write_result(
        result_dir=result_dir,
        metrics={
            "sequence": [f"Macro-{m.id}" for m in result["sequence"]],
            "lut": result["metrics"]["lut"],
            "levels": result["metrics"]["levels"],
            "exec_time": result["exec_time"],
        },
        write_json=True,
        write_pkl=True,
    )

    logger.info(
        "Done | FINAL LUT=%d LEVEL=%d TIME=%.2fs",
        result["metrics"]["lut"],
        result["metrics"]["levels"],
        result["exec_time"],
    )


if __name__ == "__main__":
    main()

