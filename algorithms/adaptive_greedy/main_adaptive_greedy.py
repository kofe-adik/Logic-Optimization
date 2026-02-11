# algorithms/adaptive_greedy/main_adaptive_greedy.py
import argparse
import logging

from common.action_space.test_space import SUPERSET_MACRO_SPACE, CLUSTER_MACRO_SPACE

from common.action_space.macro_spaces import FULL_MACRO_SPACE#, SUPERSET_MACRO_SPACE
from common.action_space.sequences import INIT, RESYN2
from common.execution.design_eval import evaluate_fpga_design
from common.storage.paths import get_project_root, get_run_result_dir
from common.storage.result_writer import write_result
from common.utils.logging_utils import setup_logger

from algorithms.adaptive_greedy.adaptive_greedy import adaptive_greedy

from common.action_space.actions import MacroAction
def main():
    parser = argparse.ArgumentParser("Adaptive Greedy Macro Optimization")
    parser.add_argument("--design", required=True)
    parser.add_argument("--lut-k", type=int, default=6)
    parser.add_argument("--space", choices=["full", "superset", "cluster"], required=True)
    parser.add_argument("--ref", choices=["init", "resyn2"], required=True)
    parser.add_argument("--pool-size", type=int, default=300)
    parser.add_argument("--max-steps", type=int, default=5)
    parser.add_argument("--n-jobs", type=int, default=12)

    args = parser.parse_args()

    # --------------------------------------------------
    # Result directory + logger (file logging)
    # --------------------------------------------------
    result_dir = get_run_result_dir(
        algo_name="adaptive_greedy",
        option=(
            f"lutk-{args.lut_k}"
            f"_space-{args.space}"
            f"_ref-{args.ref}"
            f"_pool-{args.pool_size}"
            f"_slots-{args.max_steps}"
        ),
        design_name=args.design,
        run_id=None,
    )

    setup_logger(
        name="adaptive_greedy",
        log_file=result_dir / "run.log",
        level=logging.INFO,
    )
    logger = logging.getLogger("adaptive_greedy")

    # --------------------------------------------------
    # Resolve inputs
    # --------------------------------------------------
    design_file = (
        get_project_root()
        / "benchmarks"
        / "epfl"
        / "arithmetic"
        / f"{args.design}.blif"
    )

    SPACE_MAP = {
        "full": FULL_MACRO_SPACE,
        "superset": SUPERSET_MACRO_SPACE,
        "cluster": CLUSTER_MACRO_SPACE,
    }

    REF_MAP = {
        "init": INIT,
        "resyn2": RESYN2,
    }

    try:
        macro_space = SPACE_MAP[args.space]
    except KeyError:
        raise ValueError(f"Unknown space: {args.space}")

    try:
        ref_seq = REF_MAP[args.ref]
    except KeyError:
        raise ValueError(f"Unknown ref: {args.ref}")
    
    # --------------------------------------------------
    # TERMINAL: CONFIG
    # --------------------------------------------------
    print("=== Adaptive Greedy ===")
    print(f"Design      : {args.design}")
    print(f"LUT K       : {args.lut_k}")
    print(f"Macro space : {args.space} ({len(macro_space)})")
    print(f"Reference   : {args.ref}")
    print(f"Pool size   : {args.pool_size}")
    print(f"Max steps   : {args.max_steps}")
    print(f"N jobs      : {args.n_jobs}")
    print(f"Result dir  : {result_dir}")
    print()
    print(">>> START RUN")

    # --------------------------------------------------
    # Reference evaluation
    # --------------------------------------------------
    ref_metrics = evaluate_fpga_design(
        design_file=str(design_file),
        actions=ref_seq,
        lut_k=args.lut_k,
    )

    logger.info(
        "Reference | LUT=%d LEVEL=%d",
        ref_metrics["lut"],
        ref_metrics["levels"],
    )

    # --------------------------------------------------
    # Run adaptive greedy (tqdm happens inside)
    # --------------------------------------------------
    result, pool = adaptive_greedy(
        design_file=str(design_file),
        macro_space=macro_space,
        lut_k=args.lut_k,
        ref_metrics=ref_metrics,
        pool_size=args.pool_size,
        max_steps=args.max_steps,
        n_jobs=args.n_jobs,
    )

    # --------------------------------------------------
    # TERMINAL: END RUN
    # --------------------------------------------------
    print(">>> RUN FINISHED")
    print()
    # --------------------------------------------------
    # FINAL SNAPSHOT (storage)
    # --------------------------------------------------
    final_metrics = {
        "final": {
            "sequence": [
                {"id": m.id, "cmd": m.cmd}
                for m in result["sequence"]
            ],
            "lut": result["metrics"]["lut"],
            "levels": result["metrics"]["levels"],
            "qor": result["qor"],
            "exec_time": result["exec_time"],
        },
        "eval_pool": [
            {"id": m.id, "cmd": m.cmd}
            for m in pool
        ],
    }

    write_result(
        result_dir=result_dir,
        metrics=final_metrics,
        write_json=True,
        write_pkl=True,
    )

    # --------------------------------------------------
    # TERMINAL: FINAL RESULT
    # --------------------------------------------------
    print("=== FINAL RESULT ===")
    print(f"LUT    : {result['metrics']['lut']}")
    print(f"LEVEL  : {result['metrics']['levels']}")
    print(f"QOR    : {result['qor']:.4f}")
    print(f"TIME   : {result['exec_time']:.2f}s")
    print(f"POOL   : {len(pool)}")
    #print("END")

    # --------------------------------------------------
    # LOG SUMMARY (file only)
    # --------------------------------------------------
    logger.info(
        "DONE | LUT=%d LEVEL=%d QOR=%.4f time=%.2fs pool=%d",
        result["metrics"]["lut"],
        result["metrics"]["levels"],
        result["qor"],
        result["exec_time"],
        len(pool),
    )


if __name__ == "__main__":
    main()

