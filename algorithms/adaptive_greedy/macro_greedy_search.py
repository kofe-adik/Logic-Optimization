import time
import logging
from typing import List, Dict

from joblib import Parallel, delayed
from tqdm import tqdm

from common.action_space.actions import MacroAction
from common.execution.design_eval import evaluate_fpga_design_macro
from common.objectives.compute_qor import compute_qor

logger = logging.getLogger("adaptive_greedy")

def eval_one_macro(
    macro: MacroAction,
    cur_seq: List[MacroAction],
    design_file: str,
    lut_k: int,
    ref_metrics: Dict[str, float],
):
    cand_seq = cur_seq + [macro]

    try:
        metrics = evaluate_fpga_design_macro(
            design_file=design_file,
            macros=cand_seq,
            lut_k=lut_k,
        )
    except Exception as e:
        logger.warning(
            "ABC FAIL | Macro-%05d | seq=%s | err=%s",
            macro.id,
            [m.name for m in cand_seq],
            str(e),
        )
        return None

    qor = compute_qor(metrics, ref_metrics)

    logger.info(
        "Trial | Macro-%05d | LUT=%4d LEVEL=%3d QOR=%.4f",
        macro.id,
        metrics["lut"],
        metrics["levels"],
        qor,
    )

    return {
        "macro": macro,
        "metrics": metrics,
        "qor": qor,
    }


#def eval_one_macro(
#    macro: MacroAction,
#    cur_seq: List[MacroAction],
#    design_file: str,
#    lut_k: int,
#    ref_metrics: Dict[str, float],
#):
#    cand_seq = cur_seq + [macro]
#
#    metrics = evaluate_fpga_design_macro(
#        design_file=design_file,
#        macros=cand_seq,
#        lut_k=lut_k,
#    )
#
#    qor = compute_qor(metrics, ref_metrics)
#
#    logger.info(
#        "Trial | Macro-%05d | LUT=%4d LEVEL=%3d QOR=%.4f",
#        macro.id,
#        metrics["lut"],
#        metrics["levels"],
#        qor,
#    )
#
#    return {
#        "macro": macro,
#        "metrics": metrics,
#        "qor": qor,
#    }


def greedy_search_macro(
    design_file: str,
    macro_space: List[MacroAction],
    lut_k: int,
    ref_metrics: Dict[str, float],
    max_steps: int,
    n_jobs: int,
):
    t0 = time.time()

    cur_seq: List[MacroAction] = []
    cur_metrics = ref_metrics

    logger.info(
        "Greedy start | ref_LUT=%d ref_LEVEL=%d",
        ref_metrics["lut"],
        ref_metrics["levels"],
    )

    for step in range(max_steps):
        logger.info("=== Slot %d / %d ===", step + 1, max_steps)

        results = Parallel(
            n_jobs=min(n_jobs, len(macro_space)),
            backend="threading",
        )(
            delayed(eval_one_macro)(
                macro,
                cur_seq,
                design_file,
                lut_k,
                ref_metrics,
            )
            for macro in tqdm(
                macro_space,
                desc=f"Slot-{step+1} trials",
            )
        )

        best = min(results, key=lambda x: x["qor"])

        cur_seq.append(best["macro"])
        cur_metrics = best["metrics"]
        cur_qor = best["qor"]

        logger.info(
            "==> Pick | Macro-%05d | LUT=%4d LEVEL=%3d QOR=%.4f",
            best["macro"].id,
            cur_metrics["lut"],
            cur_metrics["levels"],
            cur_qor,
        )

    exec_time = time.time() - t0

    logger.info(
        "Greedy done | FINAL LUT=%d LEVEL=%d QOR=%.4f TIME=%.2fs",
        cur_metrics["lut"],
        cur_metrics["levels"],
        cur_qor,
        exec_time,
    )

    return {
        "sequence": cur_seq,
        "metrics": cur_metrics,
        "qor": cur_qor,
        "exec_time": exec_time,
    }

