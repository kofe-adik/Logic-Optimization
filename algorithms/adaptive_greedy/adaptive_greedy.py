# algorithms/adaptive_greedy/adaptive_greedy.py
import logging
from typing import Dict, List

from common.action_space.actions import MacroAction

from .extract_eval_pool import extract_eval_pool
from .macro_greedy_search import greedy_search_macro

logger = logging.getLogger("adaptive_greedy")


def adaptive_greedy(
    design_file: str,
    macro_space: List[MacroAction],
    lut_k: int,
    ref_metrics: Dict[str, float],
    pool_size: int,
    max_steps: int,
    n_jobs: int,
):
    logger.info("=== Adaptive Greedy start ===")

    # --------------------------------------------------
    # 1. Extract evaluation pool
    # --------------------------------------------------
    logger.info(
        "Extract eval pool | pool_size=%d | macro_space=%d",
        pool_size,
        len(macro_space),
    )

    pool = extract_eval_pool(
        macro_space=macro_space,
        design_file=design_file,
        lut_k=lut_k,
        ref_metrics=ref_metrics,
        pool_size=pool_size,
        n_jobs=n_jobs,
    )

    logger.info("Eval pool ready | pool_size=%d", len(pool))

    # --------------------------------------------------
    # 2. Greedy search on pool
    # --------------------------------------------------
    result = greedy_search_macro(
        design_file=design_file,
        macro_space=pool,
        lut_k=lut_k,
        ref_metrics=ref_metrics,
        max_steps=max_steps,
        n_jobs=n_jobs,
    )

    logger.info(
        "Adaptive Greedy done | FINAL LUT=%d LEVEL=%d QOR=%.4f TIME=%.2fs",
        result["metrics"]["lut"],
        result["metrics"]["levels"],
        result["qor"],
        result["exec_time"],
    )

    return result, pool

