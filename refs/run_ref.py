from pathlib import Path
import argparse

from common.execution.design_eval import evaluate_fpga_design
from common.action_space.sequences import BUILD_IN_SEQS
from common.storage.paths import get_ref_result_dir
from common.storage.result_writer import write_result


def run_fpga_ref(
    design_file: str,
    script_name: str,
    lut_k: int,
) -> None:
    if script_name not in BUILD_IN_SEQS:
        raise ValueError(f"Unknown script: {script_name}")

    design_path = Path(design_file)
    design_name = design_path.stem
    option = f"fpga-{lut_k}"

    actions = BUILD_IN_SEQS[script_name]

    print(f">>> [REF] {design_name} | {script_name} | {option}")

    result = evaluate_fpga_design(
        design_file=design_file,
        actions=actions,
        lut_k=lut_k,
    )

    result_dir = get_ref_result_dir(
        script_name=script_name,
        option=option,
        design_name=design_name,
    )

    write_result(
        result_dir=result_dir,
        metrics={
            "lut": result["lut"],
            "levels": result["levels"],
            "exec_time": result["exec_time"],
        },
    )

    print(f"[SAVED] {result_dir}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--design_file", required=True)
    parser.add_argument("--script", required=True)
    parser.add_argument("--lut_k", type=int, required=True)

    args = parser.parse_args()

    run_fpga_ref(
        design_file=args.design_file,
        script_name=args.script,
        lut_k=args.lut_k,
    )

