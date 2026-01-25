import time
import logging
from typing import List, Dict

from common.action_space.actions import Action
from common.execution.design_eval import evaluate_fpga_design
from common.objectives.compute_qor import compute_qor

logger = logging.getLogger("greedy")


def greedy_search(
    design_file: str,
    action_space: List[Action],
    lut_k: int,
    ref_metrics: Dict[str, float],
    max_steps: int,
) -> Dict[str, object]:
    """
    Fixed-budget greedy search.
    Always runs exactly max_steps steps.
    Output = FINAL sequence only.
    """

    t_start = time.time()

    cur_seq: List[Action] = []
    cur_metrics = ref_metrics
    cur_qor = compute_qor(cur_metrics, ref_metrics)

    logger.info(
        "Greedy start | ref_lut=%d ref_levels=%d ref_qor=%.4f",
        ref_metrics["lut"],
        ref_metrics["levels"],
        cur_qor,
    )

    for step in range(max_steps):
        logger.info("Iter %d / %d", step + 1, max_steps)

        step_best_act = None
        step_best_metrics = None
        step_best_qor = None

        for act in action_space:
            cand_seq = cur_seq + [act]

            metrics = evaluate_fpga_design(
                design_file=design_file,
                actions=cand_seq,
                lut_k=lut_k,
            )

            qor = compute_qor(metrics, ref_metrics)

            logger.info(
                "  Try %-20s | LUT=%4d LEVEL=%3d QOR=%.4f",
                act.name,
                metrics["lut"],
                metrics["levels"],
                qor,
            )

            if step_best_qor is None or qor < step_best_qor:
                step_best_act = act
                step_best_metrics = metrics
                step_best_qor = qor

        # greedy → bắt buộc đi tiếp
        cur_seq.append(step_best_act)
        cur_metrics = step_best_metrics
        cur_qor = step_best_qor

        logger.info(
            " ==> Pick %-20s | LUT=%4d LEVEL=%3d QOR=%.4f",
            step_best_act.name,
            cur_metrics["lut"],
            cur_metrics["levels"],
            cur_qor,
        )

    exec_time = time.time() - t_start

    logger.info(
        "Greedy done | iter=%d | final_lut=%d final_levels=%d | exec_time=%.2fs",
        max_steps,
        cur_metrics["lut"],
        cur_metrics["levels"],
        exec_time,
    )

    return {
        "sequence": cur_seq,
        "metrics": cur_metrics,
        "exec_time": exec_time,
    }

