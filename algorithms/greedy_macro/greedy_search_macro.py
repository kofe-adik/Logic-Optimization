import time
import logging
from typing import List, Dict, Tuple

from common.action_space.actions import MacroAction
from common.execution.design_eval import evaluate_fpga_design_macro
from common.objectives.compute_qor import compute_qor

logger = logging.getLogger("greedy_macro")


def greedy_search_macro(
    design_file: str,
    struct_macros: List[MacroAction],
    mix_macros: List[MacroAction],
    polish_macros: List[MacroAction],
    lut_k: int,
    ref_metrics: Dict[str, float],
    max_slots: int,
    phase_ratio: Tuple[float, float, float] = (0.4, 0.4, 0.2),
) -> Dict[str, object]:
    """
    Multi-Phase Adaptive Greedy (MPAG)

    - Phase 1: STRUCT  (structure-heavy macros)
    - Phase 2: MIX     (structure + local optimize)
    - Phase 3: POLISH  (local refine)

    1 slot = 1 MacroAction
    Fixed total budget = max_slots
    """

    assert abs(sum(phase_ratio) - 1.0) < 1e-6, "Phase ratio must sum to 1.0"

    t_start = time.time()

    # -------- Phase split --------
    n_struct = int(phase_ratio[0] * max_slots)
    n_mix = int(phase_ratio[1] * max_slots)
    n_polish = max_slots - n_struct - n_mix  # ensure sum == max_slots

    phase_plan: List[Tuple[str, List[MacroAction]]] = (
        [("STRUCT", struct_macros)] * n_struct +
        [("MIX", mix_macros)] * n_mix +
        [("POLISH", polish_macros)] * n_polish
    )

    # -------- Init --------
    cur_seq: List[MacroAction] = []
    cur_metrics = ref_metrics
    cur_qor = compute_qor(cur_metrics, ref_metrics)

    logger.info(
        "Greedy-Macro MPAG start | LUT_K=%d | slots=%d",
        lut_k,
        max_slots,
    )
    logger.info(
        "Phase split | STRUCT=%d MIX=%d POLISH=%d",
        n_struct,
        n_mix,
        n_polish,
    )
    logger.info(
        "Reference | LUT=%d LEVEL=%d QOR=%.4f",
        ref_metrics["lut"],
        ref_metrics["levels"],
        cur_qor,
    )

    # -------- Greedy over slots --------
    for slot, (phase_name, macro_space) in enumerate(phase_plan, start=1):
        logger.info(
            "Slot %d / %d | Phase=%s",
            slot,
            max_slots,
            phase_name,
        )

        best_macro = None
        best_metrics = None
        best_qor = None

        for macro in macro_space:
            cand_seq = cur_seq + [macro]

            metrics = evaluate_fpga_design_macro(
                design_file=design_file,
                macros=cand_seq,
                lut_k=lut_k,
            )

            qor = compute_qor(metrics, ref_metrics)

            logger.info(
                "  Try [%s] Macro-%02d | LUT=%4d LEVEL=%3d QOR=%.4f",
                phase_name,
                macro.id,
                metrics["lut"],
                metrics["levels"],
                qor,
            )

            if best_qor is None or qor < best_qor:
                best_macro = macro
                best_metrics = metrics
                best_qor = qor

        # ---- mandatory greedy commit ----
        cur_seq.append(best_macro)
        cur_metrics = best_metrics
        cur_qor = best_qor

        logger.info(
            " ==> Pick [%s] Macro-%02d | LUT=%4d LEVEL=%3d QOR=%.4f",
            phase_name,
            best_macro.id,
            cur_metrics["lut"],
            cur_metrics["levels"],
            cur_qor,
        )

    exec_time = time.time() - t_start

    logger.info(
        "Greedy-Macro MPAG done | final_LUT=%d final_LEVEL=%d | exec_time=%.2fs",
        cur_metrics["lut"],
        cur_metrics["levels"],
        exec_time,
    )

    return {
        "sequence": cur_seq,
        "metrics": cur_metrics,
        "exec_time": exec_time,
        "phase_split": {
            "struct": n_struct,
            "mix": n_mix,
            "polish": n_polish,
        },
    }

