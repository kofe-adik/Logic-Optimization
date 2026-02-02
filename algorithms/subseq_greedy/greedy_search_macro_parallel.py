import time
import logging
from typing import List, Dict, Optional

from joblib import Parallel, delayed

from common.action_space.actions import MacroAction
from common.action_space.sequences import RESYN2
from common.execution.design_eval import (
    evaluate_fpga_design_macro,
    evaluate_fpga_design,
)
from common.objectives.compute_qor import compute_qor

logger = logging.getLogger("greedy_macro")


# ============================================================
# Helper: evaluate ONE macro
# ============================================================
def eval_one_macro(
        macro: MacroAction,
        cur_seq: List[MacroAction],
        design_file: str,
        lut_k: int,
        ref_metrics: Dict[str, float], 
): 
    cand_seq = cur_seq + [macro]
    
    metrics = evaluate_fpga_design_macro(
        design_file=design_file,
        macros=cand_seq,
        lut_k=lut_k,
    )

    qor = compute_qor(metrics, ref_metrics) 

    return macro, metrics, qor

# ============================================================
# Greedy search with PARALLEL per slot
# ============================================================
def greedy_search_macro(
    design_file: str,
    macro_space: List[MacroAction],
    lut_k: int,
    ref_metrics: Dict[str, float],
    max_slots: int,
    n_jobs: int = 2,   # <<< USER-CONTROLLED, DEFAULT = 2
) -> Dict[str, object]:
    """
    Fixed-budget greedy search over MACRO slots.
    1 slot = 1 MacroAction.

    Parallelization:
      - ONLY inside a slot
      - n_jobs controls number of workers
      - Decision logic remains strictly greedy
    """

    t_start = time.time()

    cur_seq: List[MacroAction] = []
    cur_metrics = ref_metrics
    cur_qor = compute_qor(cur_metrics, ref_metrics)

    logger.info(
        "Greedy-Macro start | ref_lut=%d ref_levels=%d ref_qor=%.4f | n_jobs=%d",
        ref_metrics["lut"],
        ref_metrics["levels"],
        cur_qor,
        n_jobs,
    )

    for slot in range(max_slots):
        logger.info("Slot %d / %d", slot + 1, max_slots)

        best_macro = None
        best_metrics = None
        best_qor = None

        # clamp n_jobs to pool size
        jobs = min(n_jobs, len(macro_space))

        # ----------------------------------------------------
        # PARALLEL evaluation of macros
        # ----------------------------------------------------
        results = Parallel(n_jobs=jobs, backend="loky")(
            delayed(eval_one_macro)(
                macro,
                cur_seq,
                design_file,
                lut_k,
                ref_metrics,
            )
            for macro in macro_space
        )

        # ----------------------------------------------------
        # SERIAL greedy decision
        # ----------------------------------------------------
        for macro, metrics, qor in results:
            logger.info(
                "  Try Macro-%03d | LUT=%5d LEVEL=%4d QOR=%.4f",
                macro.id,
                metrics["lut"],
                metrics["levels"],
                qor,
            )

            if best_qor is None or qor < best_qor:
                best_macro = macro
                best_metrics = metrics
                best_qor = qor

        # mandatory greedy commit
        cur_seq.append(best_macro)
        cur_metrics = best_metrics
        cur_qor = best_qor

        logger.info(
            " ==> Pick Macro-%03d | LUT=%5d LEVEL=%4d QOR=%.4f",
            best_macro.id,
            cur_metrics["lut"],
            cur_metrics["levels"],
            cur_qor,
        )

    exec_time = time.time() - t_start

    logger.info(
        "Greedy-Macro done | slots=%d | final_lut=%d final_levels=%d | exec_time=%.2fs",
        max_slots,
        cur_metrics["lut"],
        cur_metrics["levels"],
        exec_time,
    )

    return {
        "sequence": cur_seq,
        "metrics": cur_metrics,
        "exec_time": exec_time,
    }


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    from common.utils.logging_utils import setup_logger
    from common.action_space.spaces import EXTENDED_MACRO_SPACE_TEST
    from common.action_space.macro_spaces import SUPERSET_MACRO_SPACE, FULL_MACRO_SPACE

    setup_logger(
        name="greedy_macro",
        level=logging.INFO,
    )

    logger = logging.getLogger("greedy_macro")

    design_file = "./benchmarks/epfl/arithmetic/adder.blif"
    lut_k = 6
    max_slots = 5
#    max_slots = 1

    # <<< CHANGE HERE >>>
#    n_jobs = 2   # default
    n_jobs = 6 # ví dụ muốn 4 core

    # reference
    ref_metrics = evaluate_fpga_design(
        design_file=design_file,
        actions=RESYN2,
#        actions=[],
        lut_k=lut_k,
    )

    logger.info(
        "design: %s",
        design_file,
    )

    logger.info(
        "Reference | LUT=%d LEVEL=%d",
        ref_metrics["lut"],
        ref_metrics["levels"],
    )

    result = greedy_search_macro(
        design_file=design_file,
        macro_space=FULL_MACRO_SPACE,
#        macro_space=SUPERSET_MACRO_SPACE,
#        macro_space=EXTENDED_MACRO_SPACE_TEST,
        lut_k=lut_k,
        ref_metrics=ref_metrics,
        max_slots=max_slots,
        n_jobs=n_jobs,
    )

    logger.info("Final sequence:")
    for i, macro in enumerate(result["sequence"], start=1):
        logger.info("  %d. Macro-%03d : %s", i, macro.id, macro.cmd)

    logger.info(
        "Final result | LUT=%d LEVEL=%d | exec_time=%.2fs",
        result["metrics"]["lut"],
        result["metrics"]["levels"],
        result["exec_time"],
    )

