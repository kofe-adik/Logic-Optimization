from joblib import Parallel, delayed
from typing import List, Dict
import logging
from tqdm import tqdm

from common.action_space.actions import MacroAction
from common.action_space.macro_spaces import SAFE_MACRO_SPACE
from common.execution.design_eval import evaluate_fpga_design_macro
from common.objectives.compute_qor import compute_qor

logger = logging.getLogger("adaptive_greedy")


def _eval_slot1(
    macro: MacroAction,
    design_file: str,
    lut_k: int,
    ref_metrics: Dict[str, float],
):
    metrics = evaluate_fpga_design_macro(
        design_file=design_file,
        macros=[macro],
        lut_k=lut_k,
    )

    qor = compute_qor(metrics, ref_metrics)

    # --------------------------------------------------
    # LOG every slot-1 evaluation (machine-facing)
    # --------------------------------------------------
    logger.info(
        "PoolEval | Macro-%05d | LUT=%4d LEVEL=%3d QOR=%.4f | CMD=%s",
        macro.id,
        metrics["lut"],
        metrics["levels"],
        qor,
        macro.cmd,
    )

    return macro, metrics, qor

def extract_eval_pool(
    macro_space: List[MacroAction],
    design_file: str,
    lut_k: int,
    ref_metrics: Dict[str, float],
    pool_size: int,
    n_jobs: int,
) -> List[MacroAction]:

    logger.info(
        "Extract eval pool | macros=%d pool_size=%d n_jobs=%d",
        len(macro_space),
        pool_size,
        n_jobs,
    )

    # --------------------------------------------------
    # Evaluate slot-1 macros
    # --------------------------------------------------
    results = Parallel(
        n_jobs=n_jobs,
        backend="threading",
    )(
        delayed(_eval_slot1)(
            macro,
            design_file,
            lut_k,
            ref_metrics,
        )
        for macro in tqdm(
            macro_space,
            desc="Adaptive Pool Generating:",
        )
    )

    # --------------------------------------------------
    # Ranking strategies
    # --------------------------------------------------
    ref_lut = ref_metrics["lut"]
    ref_lvl = ref_metrics["levels"]

    K = pool_size // 3
    lut_ratio = 1.5
    lvl_ratio = 1.5

    # --- Top-K LUT ---
    top_lut = sorted(
        results,
        key=lambda x: x[1]["lut"],
    )[:K]

    # --- Top-K LEVEL ---
    top_lvl = sorted(
        results,
        key=lambda x: x[1]["levels"],
    )[:K]

    # --- Top-K BOTH (constraint + best QOR) ---
    both_candidates = [
        r for r in results
        if (r[1]["lut"] / ref_lut <= lut_ratio)
        and (r[1]["levels"] / ref_lvl <= lvl_ratio)
    ]

    top_both = sorted(
        both_candidates,
        key=lambda x: x[2],  # QOR
    )[:K]

    # --------------------------------------------------
    # Merge + deduplicate (by macro id)
    # --------------------------------------------------
    merged = {}
    for group in (top_lut, top_lvl, top_both):
        for m, metrics, qor in group:
            merged[m.id] = (m, metrics, qor)

    final = list(merged.values())

#    final = sorted(
#        merged.values(),
#        key=lambda x: x[2],  # final order by QOR
#    )[:pool_size]
#
    pool = [m for m, _, _ in final]

    # --------------------------------------------------
    # LOG full pool (machine-facing)
    # --------------------------------------------------
    logger.info("=== Eval Pool Detail (Merged) ===")
    for rank, (m, metrics, qor) in enumerate(final, start=1):
        logger.info(
            "[%02d] Macro-%05d | LUT=%4d LEVEL=%3d QOR=%.4f | CMD=%s",
            rank,
            m.id,
            metrics["lut"],
            metrics["levels"],
            qor,
            m.cmd,
        )
    logger.info("Adaptive pool created | size=%d", len(pool))

    # --------------------------------------------------
    # Inject SAFE macros (baseline stability)
    # --------------------------------------------------
    safe_macros = SAFE_MACRO_SPACE

    existing_ids = {m.id for m in pool}
    for m in safe_macros:
        if m.id not in existing_ids:
            pool.append(m)

    logger.info(
        "Injected %d safe macros | final pool size=%d",
        len(safe_macros),
        len(pool),
    )

    logger.info("Eval pool created | size=%d", len(pool))
    return pool

    # --------------------------------------------------
    # Rank by QOR (lower is better)
    # --------------------------------------------------
#    results.sort(key=lambda x: x[2])

#    topk = results[:pool_size]
#    pool = [m for m, _, _ in topk]

#    # --------------------------------------------------
#    # PRINT to terminal (human-facing)
#    # --------------------------------------------------
#    print("\n=== Eval Pool (Top-%d by QOR) ===" % pool_size)
#    for rank, (m, metrics, qor) in enumerate(topk, start=1):
#        print(
#            f"[{rank:02d}] "
#            f"Macro-{m.id:05d} | "
#            f"LUT={metrics['lut']:5d} "
#            f"LEVEL={metrics['levels']:4d} "
#            f"QOR={qor:.4f}"
#        )

    # --------------------------------------------------
    # LOG full pool (machine-facing, reproducible)
    # --------------------------------------------------
#    logger.info("=== Eval Pool Detail (Top-%d) ===", pool_size)
#    for rank, (m, metrics, qor) in enumerate(topk, start=1):
#        logger.info(
#            "[%02d] Macro-%05d | LUT=%4d LEVEL=%3d QOR=%.4f | CMD=%s",
#            rank,
#            m.id,
#            metrics["lut"],
#            metrics["levels"],
#            qor,
#            m.cmd,
#        )

#    logger.info("Eval pool created | size=%d", len(pool))
#    return pool

