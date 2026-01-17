from typing import List, Dict
import time

from common.action_space.actions import Action
from common.execution.script_builder import build_fpga_script
from common.execution.abc_runner import run_abc_script
from common.execution.metrics_parser import parse_fpga_stats


def evaluate_fpga_design(
    design_file: str,
    actions: List[Action],
    lut_k: int,
    abc_bin: str = "yosys-abc",
    measure_time: bool = True,
) -> Dict[str, object]:
    """
    End-to-end FPGA evaluation:
        actions -> ABC -> metrics

    Returns:
        {
            "lut": int,
            "levels": int,
            "exec_time": float (optional)
        }
    """
    script = build_fpga_script(
        design_file=design_file,
        actions=actions,
        lut_k=lut_k,
    )

    t0 = time.time()
    stdout = run_abc_script(script, abc_bin=abc_bin)
    t1 = time.time()

    metrics = parse_fpga_stats(stdout)

    if measure_time:
        metrics["exec_time"] = t1 - t0

    return metrics

