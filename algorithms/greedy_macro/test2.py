import time
import logging
from typing import Dict, List

from common.action_space.actions import MacroAction
from common.action_space.spaces import (
    STRUCT_MACRO_SPACE,
    MIX_MACRO_SPACE,
    POLISH_MACRO_SPACE,
)
from common.execution.design_eval import evaluate_fpga_design_macro
from common.objectives.compute_qor import compute_qor
from common.utils.logging_utils import setup_logger


logger = logging.getLogger(__name__)


def run_greedy_slot(
    design_file: str,
    lut_k: int,
    ref_metrics: Dict[str, float],
    cur_seq: List[MacroAction],
    macro_space: List[MacroAction],
):
    """
    Run 1 greedy slot on given macro_space.
    Return best (macro, metrics, qor)
    """
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
            "  Try Macro-%02d | LUT=%4d LEVEL=%3d QOR=%.4f",
            macro.id,
            metrics["lut"],
            metrics["levels"],
            qor,
        )

        if best_qor is None or qor < best_qor:
            best_macro = macro
            best_metrics = metrics
            best_qor = qor

    return best_macro, best_metrics, best_qor


def greedy_search_macro(
    design_file: str,
    lut_k: int,
    ref_metrics: Dict[str, float],
):
    # -------- Init --------
    cur_seq: List[MacroAction] = []
    cur_metrics = ref_metrics
    cur_qor = compute_qor(cur_metrics, ref_metrics)

    logger.info("Greedy-Macro start | LUT_K=%d", lut_k)
    logger.info(
        "Reference | LUT=%d LEVEL=%d QOR=%.4f",
        ref_metrics["lut"],
        ref_metrics["levels"],
        cur_qor,
    )

    # ============================================================
    # SLOT 1 — STRUCT (no threshold)
    # ============================================================
    logger.info("Slot 1/5 | Phase = STRUCT")

    macro, metrics, qor = run_greedy_slot(
        design_file, lut_k, ref_metrics, cur_seq, STRUCT_MACRO_SPACE
    )

    cur_seq.append(macro)
    cur_metrics = metrics
    prev_qor = cur_qor
    cur_qor = qor

    logger.info(
        " ==> Pick Macro-%02d | QOR=%.4f (Δ=%.4f)",
        macro.id,
        cur_qor,
        prev_qor - cur_qor,
    )

    # ============================================================
    # SLOT 2 — MIX (warm-up)
    # ============================================================
    logger.info("Slot 2/5 | Phase = MIX (warm-up)")

    macro, metrics, qor = run_greedy_slot(
        design_file, lut_k, ref_metrics, cur_seq, MIX_MACRO_SPACE
    )

    cur_seq.append(macro)
    prev_qor = cur_qor
    cur_qor = qor
    cur_metrics = metrics

    logger.info(
        " ==> Pick Macro-%02d | QOR=%.4f (Δ=%.4f)",
        macro.id,
        cur_qor,
        prev_qor - cur_qor,
    )

    # ============================================================
    # SLOT 3 — MIX (threshold = 0.2, fallback STRUCT)
    # ============================================================
    logger.info("Slot 3/5 | Phase = MIX (threshold = 0.1)")

    macro, metrics, qor = run_greedy_slot(
        design_file, lut_k, ref_metrics, cur_seq, MIX_MACRO_SPACE
    )

    improvement = prev_qor - qor

    if improvement < 0.1:
        logger.info(
            "  MIX improvement %.4f < 0.2 → fallback STRUCT",
            improvement,
        )

        macro, metrics, qor = run_greedy_slot(
            design_file, lut_k, ref_metrics, cur_seq, STRUCT_MACRO_SPACE
        )

    cur_seq.append(macro)
    prev_qor = cur_qor
    cur_qor = qor
    cur_metrics = metrics

    logger.info(
        " ==> Pick Macro-%02d | QOR=%.4f (Δ=%.4f)",
        macro.id,
        cur_qor,
        prev_qor - cur_qor,
    )

    # ============================================================
    # SLOT 4 — POLISH (warm-up)
    # ============================================================
    logger.info("Slot 4/5 | Phase = POLISH (warm-up)")

    macro, metrics, qor = run_greedy_slot(
        design_file, lut_k, ref_metrics, cur_seq, POLISH_MACRO_SPACE
    )

    cur_seq.append(macro)
    prev_qor = cur_qor
    cur_qor = qor
    cur_metrics = metrics

    logger.info(
        " ==> Pick Macro-%02d | QOR=%.4f (Δ=%.4f)",
        macro.id,
        cur_qor,
        prev_qor - cur_qor,
    )

    # ============================================================
    # SLOT 5 — POLISH (threshold = 0.1, fallback MIX → STRUCT)
    # ============================================================
    logger.info("Slot 5/5 | Phase = POLISH (threshold = 0.03)")

    macro, metrics, qor = run_greedy_slot(
        design_file, lut_k, ref_metrics, cur_seq, POLISH_MACRO_SPACE
    )

    improvement = prev_qor - qor

    if improvement < 0.03:
        logger.info(
            "  POLISH improvement %.4f < 0.03 → fallback MIX",
            improvement,
        )

        macro, metrics, qor = run_greedy_slot(
            design_file, lut_k, ref_metrics, cur_seq, MIX_MACRO_SPACE
        )

        improvement = prev_qor - qor

        if improvement < 0.03:
            logger.info(
                "  MIX improvement %.4f < 0.03 → fallback STRUCT",
                improvement,
            )

            macro, metrics, qor = run_greedy_slot(
                design_file, lut_k, ref_metrics, cur_seq, STRUCT_MACRO_SPACE
            )

    cur_seq.append(macro)
    cur_metrics = metrics
    cur_qor = qor

    logger.info(
        " ==> Pick Macro-%02d | QOR=%.4f (Δ=%.4f)",
        macro.id,
        cur_qor,
        prev_qor - cur_qor,
    )

    return {
        "sequence": cur_seq,
        "metrics": cur_metrics,
        "qor": cur_qor,
    }


# ================================================================
# Quick test
# ================================================================
if __name__ == "__main__":
    setup_logger(name="greedy_macro", level=logging.INFO)
    logger = logging.getLogger("greedy_macro")

    ref_metrics = evaluate_fpga_design_macro(
        design_file="./benchmarks/epfl/arithmetic/multiplier.blif",
        macros=[],
        lut_k=6,
    )

    greedy_search_macro(
        design_file="./benchmarks/epfl/arithmetic/multiplier.blif",
        lut_k=6,
        ref_metrics=ref_metrics,
    )

