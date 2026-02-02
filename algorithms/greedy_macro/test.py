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


def _run_pool(
    design_file: str,
    macros_prefix: List[MacroAction],
    macro_pool: List[MacroAction],
    lut_k: int,
    ref_metrics: Dict[str, float],
    logger: logging.Logger,
):
    """
    Try all macros in macro_pool, return best (macro, metrics, qor)
    """
    best_macro = None
    best_metrics = None
    best_qor = None

    for macro in macro_pool:
        cand_seq = macros_prefix + [macro]

        metrics = evaluate_fpga_design_macro(
            design_file=design_file,
            macros=cand_seq,
            lut_k=lut_k,
        )
        qor = compute_qor(metrics, ref_metrics)

        logger.info(
            "    Try Macro-%02d | LUT=%4d LEVEL=%3d QOR=%.4f",
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
    max_slots: int = 5,
) -> Dict[str, object]:
    """
    Slot plan (fixed):
      Slot 1        : STRUCT (no threshold)
      Slot 2-3      : MIX (thr=0.2) -> fallback STRUCT
      Slot 4-5      : POLISH (thr=0.1) -> MIX -> STRUCT
    """

    logger = logging.getLogger("greedy_macro")

    # -------- Init --------
    cur_seq: List[MacroAction] = []
    cur_metrics = ref_metrics
    cur_qor = compute_qor(cur_metrics, ref_metrics)

    logger.info("Greedy-Macro start | LUT_K=%d | slots=%d", lut_k, max_slots)
    logger.info(
        "Reference | LUT=%d LEVEL=%d QOR=%.4f",
        ref_metrics["lut"],
        ref_metrics["levels"],
        cur_qor,
    )

    for slot in range(1, max_slots + 1):
        logger.info("== Slot %d/%d ==", slot, max_slots)

        # ---------------- Slot 1 ----------------
        if slot == 1:
            logger.info("  Phase = STRUCT (no threshold)")

            best_m, best_metrics, best_qor = _run_pool(
                design_file,
                cur_seq,
                STRUCT_MACRO_SPACE,
                lut_k,
                ref_metrics,
                logger,
            )

            improve = cur_qor - best_qor
            logger.info(
                "  Best STRUCT | Macro-%02d | QOR=%.4f | Improve=%.4f | Commit=True",
                best_m.id,
                best_qor,
                improve,
            )

            cur_seq.append(best_m)
            cur_metrics = best_metrics
            cur_qor = best_qor
            continue

        # ---------------- Slot 2-3 ----------------
        if slot in (2, 3):
            logger.info("  Phase = MIX (thr=0.1)")

            best_m, best_metrics, best_qor = _run_pool(
                design_file,
                cur_seq,
                MIX_MACRO_SPACE,
                lut_k,
                ref_metrics,
                logger,
            )

            improve = cur_qor - best_qor
            if improve >= 0.1:
                logger.info(
                    "  Best MIX | Macro-%02d | QOR=%.4f | Improve=%.4f | Commit=True",
                    best_m.id,
                    best_qor,
                    improve,
                )
                cur_seq.append(best_m)
                cur_metrics = best_metrics
                cur_qor = best_qor
            else:
                logger.info(
                    "  MIX not enough (Improve=%.4f < 0.1) -> fallback STRUCT",
                    improve,
                )

                best_m, best_metrics, best_qor = _run_pool(
                    design_file,
                    cur_seq,
                    STRUCT_MACRO_SPACE,
                    lut_k,
                    ref_metrics,
                    logger,
                )

                logger.info(
                    "  Fallback STRUCT | Macro-%02d | QOR=%.4f | Commit=True",
                    best_m.id,
                    best_qor,
                )

                cur_seq.append(best_m)
                cur_metrics = best_metrics
                cur_qor = best_qor

            continue

        # ---------------- Slot 4-5 ----------------
        logger.info("  Phase = POLISH (thr=0.03)")

        best_m, best_metrics, best_qor = _run_pool(
            design_file,
            cur_seq,
            POLISH_MACRO_SPACE,
            lut_k,
            ref_metrics,
            logger,
        )

        improve = cur_qor - best_qor
        if improve >= 0.03:
            logger.info(
                "  Best POLISH | Macro-%02d | QOR=%.4f | Improve=%.4f | Commit=True",
                best_m.id,
                best_qor,
                improve,
            )
            cur_seq.append(best_m)
            cur_metrics = best_metrics
            cur_qor = best_qor
            continue

        logger.info(
            "  POLISH not enough (Improve=%.4f < 0.03) -> fallback MIX",
            improve,
        )

        best_m, best_metrics, best_qor = _run_pool(
            design_file,
            cur_seq,
            MIX_MACRO_SPACE,
            lut_k,
            ref_metrics,
            logger,
        )

        improve = cur_qor - best_qor
        if improve >= 0.03:
            logger.info(
                "  Fallback MIX | Macro-%02d | QOR=%.4f | Improve=%.4f | Commit=True",
                best_m.id,
                best_qor,
                improve,
            )
            cur_seq.append(best_m)
            cur_metrics = best_metrics
            cur_qor = best_qor
            continue

        logger.info(
            "  MIX not enough (Improve=%.4f < 0.03) -> fallback STRUCT",
            improve,
        )

        best_m, best_metrics, best_qor = _run_pool(
            design_file,
            cur_seq,
            STRUCT_MACRO_SPACE,
            lut_k,
            ref_metrics,
            logger,
        )

        logger.info(
            "  Fallback STRUCT | Macro-%02d | QOR=%.4f | Commit=True",
            best_m.id,
            best_qor,
        )

        cur_seq.append(best_m)
        cur_metrics = best_metrics
        cur_qor = best_qor

    logger.info(
        "FINAL | LUT=%d LEVEL=%d QOR=%.4f",
        cur_metrics["lut"],
        cur_metrics["levels"],
        cur_qor,
    )

    return {
        "sequence": cur_seq,
        "metrics": cur_metrics,
    }


# ============================================================
# Quick test
# ============================================================
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
        max_slots=5,
    )

