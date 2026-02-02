from common.execution.design_eval import evaluate_fpga_design_macro
from common.action_space.spaces import EXTENDED_MACRO_SPACE


def test_fpga_macro_sequences():
    design_file = "benchmarks/epfl/arithmetic/adder.blif"
    lut_k = 6

    print("=== FPGA MACRO SEQUENCE TEST ===")
    print("Design:", design_file)

    # test vài macro đầu cho nhanh, không cần all 40
    for macro in EXTENDED_MACRO_SPACE[:10]:
        print(f"\n>>> Macro ID: {macro.id}")
        print("Cmd:", macro.cmd)

        result = evaluate_fpga_design_macro(
            design_file=design_file,
            macros=[macro],
            lut_k=lut_k,
        )

        print("RESULT")
        for k, v in result.items():
            print(f"{k}: {v}")
        print("=" * 40)


if __name__ == "__main__":
    test_fpga_macro_sequences()

