from common.execution.design_eval import evaluate_fpga_design
from common.action_space.sequences import BUILD_IN_SEQS


def test_fpga_builtin_sequences():
    design_file = "benchmarks/epfl/adder.blif"
    lut_k = 6

    print("=== FPGA BUILT-IN SEQUENCE TEST ===")
    print("Design:", design_file)

    for seq_name, actions in BUILD_IN_SEQS.items():
        print(f"\n>>> Sequence: {seq_name}")
        print("Actions:", [a.name for a in actions])

        result = evaluate_fpga_design(
            design_file=design_file,
            actions=actions,
            lut_k=lut_k,
        )

        print("RESULT")
        for k, v in result.items():
            print(f"{k}: {v}")
        print("=" * 40)


if __name__ == "__main__":
    test_fpga_builtin_sequences()

