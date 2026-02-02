import argparse
import logging
from typing import List

from common.action_space.actions import MacroAction
from common.action_space.spaces import (
    STRUCT_MACRO_SPACE,
    MIX_MACRO_SPACE,
    POLISH_MACRO_SPACE,
)
from common.execution.design_eval import evaluate_fpga_design_macro
from common.storage.paths import (
    get_project_root,
    get_run_result_dir,
)
from common.storage.result_writer import write_result
from common.utils.logging_utils import setup_logger

from algorithms.greedy_macro.greedy_search_macro import greedy_search_macro


def main():
    parser = argparse.ArgumentParser("Greedy MACRO logic optimization (MPAG)")
    parser.add_argument("--design", required=True)
    parser.add_argument("--lut-k", type=int, default=6)
    parser.add_argument("--max-slots", type=int, default=5)

    # optional but clean
    parser.add_argument(
        "--phase-ratio",
        type=float,
        nargs=3,
        default=(0.4, 0.4, 0.2),
        metavar=("STRUCT", "MIX", "POLISH"),
    )

    args = parser.parse_args()

    # ===== option string =====
    option = (
        f"lutk{args.lut_k}_"
        f"slots{args.max_slots}_"
        f"mpag_{args.phase_ratio[0]:.1f}-"
        f"{args.phase_ratio[1]:.1f}-"
        f"{args.phase_ratio[2]:.1f}"
    )

    # ===== result dir =====
    result_dir = get_run_result_dir(
        algo_name="greedy_macro",
        option=option,
        design_name=args.design,
        run_id=None,
    )

    # ===== skip if exists =====
    #if result_dir.exists() and any(result_dir.iterdir()):
    #    print(f"[SKIP] Result already exists: {result_dir}")
    #    return

    # ===== logging =====
    log_file = result_dir / "run.log"
    setup_logger(
        name="greedy_macro",
        log_file=log_file,
        level=logging.INFO,
    )
    logger = logging.getLogger("greedy_macro")

    # ===== macro spaces =====
    struct_macros: List[MacroAction] = STRUCT_MACRO_SPACE
    mix_macros: List[MacroAction] = MIX_MACRO_SPACE
    polish_macros: List[MacroAction] = POLISH_MACRO_SPACE

    # ===== design file =====
    design_file = (
        get_project_root()
        / "benchmarks"
        / "epfl"
        #/ "random_control"
        / "arithmetic"
        / f"{args.design}.blif"
    )

    logger.info("== Greedy MACRO optimization (MPAG) ==")
    logger.info("Design        : %s", args.design)
    logger.info("LUT K         : %d", args.lut_k)
    logger.info("Max slots     : %d", args.max_slots)
    logger.info(
        "Phase ratio   : STRUCT=%.2f MIX=%.2f POLISH=%.2f",
        *args.phase_ratio,
    )
    logger.info(
        "Macro count   : STRUCT=%d MIX=%d POLISH=%d",
        len(struct_macros),
        len(mix_macros),
        len(polish_macros),
    )
    logger.info("Result dir    : %s", result_dir)

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

    # ===== run MPAG greedy macro =====
    result = greedy_search_macro(
        design_file=str(design_file),
        struct_macros=struct_macros,
        mix_macros=mix_macros,
        polish_macros=polish_macros,
        lut_k=args.lut_k,
        ref_metrics=ref_metrics,
        max_slots=args.max_slots,
        phase_ratio=tuple(args.phase_ratio),
    )

    # ===== write result =====
    write_result(
        result_dir=result_dir,
        metrics={
            "sequence": [
                {
                    "macro_id": m.id,
                    "macro_cmd": m.cmd,
                }
                for m in result["sequence"]
            ],
            "lut": result["metrics"]["lut"],
            "levels": result["metrics"]["levels"],
            "exec_time": result["exec_time"],
            "phase_split": result["phase_split"],
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

