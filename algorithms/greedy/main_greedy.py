import argparse
import logging
from typing import List

from common.action_space.spaces import ACTION_SPACES
from common.action_space.actions import Action
from common.execution.design_eval import evaluate_fpga_design
from common.storage.paths import (
    get_project_root,
    get_run_result_dir,
)
from common.storage.result_writer import write_result
from common.utils.logging_utils import setup_logger
from algorithms.greedy.greedy_search import greedy_search


def main():
    parser = argparse.ArgumentParser("Greedy logic optimization")
    parser.add_argument("--design", required=True)
    parser.add_argument("--lut-k", type=int, default=6)
    parser.add_argument(
        "--space",
        default="standard",
        choices=ACTION_SPACES.keys(),
    )
    parser.add_argument("--max-steps", type=int, default=20)

    args = parser.parse_args()

    # ===== option string =====
    option = f"lutk{args.lut_k}_space-{args.space}_steps-{args.max_steps}"

    # ===== result dir =====
    result_dir = get_run_result_dir(
        algo_name="greedy",
        option=option,
        design_name=args.design,
        run_id=None,
    )

    # ===== skip if exists =====
    if result_dir.exists() and any(result_dir.iterdir()):
        print(f"[SKIP] Result already exists: {result_dir}")
        return

    # ===== logging (ONE place only) =====
    log_file = result_dir / "run.log"
    setup_logger(
        name="greedy",
        log_file=log_file,
        level=logging.INFO,
    )
    logger = logging.getLogger("greedy")

    # ===== action space =====
    action_space: List[Action] = ACTION_SPACES[args.space]

    # ===== design file =====
    design_file = (
        get_project_root()
        / "benchmarks"
        / "epfl"
        / "arithmetic"
        / f"{args.design}.blif"
    )

    logger.info("== Greedy optimization ==")
    logger.info("Design     : %s", args.design)
    logger.info("LUT K      : %d", args.lut_k)
    logger.info("Space      : %s", args.space)
    logger.info("Max steps  : %d", args.max_steps)
    logger.info("Action cnt : %d", len(action_space))
    logger.info("Result dir : %s", result_dir)

    # ===== reference =====
    ref_metrics = evaluate_fpga_design(
        design_file=str(design_file),
        actions=[],
        lut_k=args.lut_k,
    )

    logger.info(
        "Reference | LUT=%d LEVEL=%d",
        ref_metrics["lut"],
        ref_metrics["levels"],
    )

    # ===== run greedy =====
    result = greedy_search(
        design_file=str(design_file),
        action_space=action_space,
        lut_k=args.lut_k,
        ref_metrics=ref_metrics,
        max_steps=args.max_steps,
    )

    # ===== write result =====
    write_result(
        result_dir=result_dir,
        metrics={
            "sequence": [a.name for a in result["sequence"]],
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

