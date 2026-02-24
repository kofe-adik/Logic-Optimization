import subprocess
import re
from typing import List, Dict, Tuple

# ==========================================================
# Command dictionary (opcode -> ABC macro)
# ==========================================================
COMMAND_DICT: Dict[int, str] = {
    0b0000: "rewrite",
    0b0001: "rewrite -z",
    0b0010: "refactor",
    0b0011: "refactor -z",
    0b0100: "resub",
    0b0101: "resub -z",
    0b0110: "balance",
    0b0111: "ifraig",
    0b1000: "dfraig",
    0b1001: "rewrite",
    0b1010: "refactor",
    0b1011: "balance",
    0b1100: "&get -n; &sopb; &put",
    0b1101: "&get -n; &blut; &put",
    0b1110: "&get -n; &dsdb; &put",
    0b1111: "&get -n; &mfs; &put",
}

# ==========================================================
# 1) bits -> ABC script
# ==========================================================
def bits_to_script(bits: List[int]) -> str:
    assert len(bits) % 4 == 0, "bits length must be multiple of 4"

    script = []
    for i in range(0, len(bits), 4):
        opcode_bits = bits[i:i+4]
        opcode = (opcode_bits[0] << 3) | (opcode_bits[1] << 2) | (opcode_bits[2] << 1) | opcode_bits[3]
        script.append(COMMAND_DICT.get(opcode, f"#ERR:{opcode}"))

    return "; ".join(script) + ";"


# ==========================================================
# 2) parse ABC stats
# ==========================================================
def parse_stats(stdout: str) -> Tuple[float, float]:
    """
    Parse ABC print_stats output:
    nd  = LUT proxy
    lev = logic depth
    """
    lut = float("inf")
    level = float("inf")

    m_nd = re.search(r"nd\s*=\s*([0-9]+)", stdout)
    if m_nd:
        lut = float(m_nd.group(1))

    m_lev = re.search(r"lev\s*=\s*([0-9]+)", stdout)
    if m_lev:
        level = float(m_lev.group(1))

    return lut, level


# ==========================================================
# 3) run ABC evaluation
# ==========================================================
def evaluate_design(
    design_file: str,
    bits: List[int],
    lut_k: int,
    abc_bin: str = "yosys-abc",
) -> Tuple[float, float]:

    abc_macro = bits_to_script(bits)

    script = (
        f"read {design_file}; "
        "strash; "
        f"{abc_macro} "
        f"if -K {lut_k}; "
        "print_stats;"
    )

    try:
        proc = subprocess.run(
            [abc_bin, "-c", script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        raise RuntimeError(f"ABC binary not found: {abc_bin}") from e

    if proc.returncode != 0:
        raise RuntimeError(
            f"ABC failed\n"
            f"SCRIPT:\n{script}\n"
            f"STDERR:\n{proc.stderr}\n"
            f"STDOUT:\n{proc.stdout}"
        )

    return parse_stats(proc.stdout)


# ==========================================================
# 4) fitness function
# ==========================================================
def fitness(
    ref_lut: float,
    ref_level: float,
    lut: float,
    level: float,
) -> Tuple[float, float]:
    """
    Return:
        qor     : normalized QoR (lower is better)
        improve : improvement percentage (%)
    """

    if ref_lut <= 0 or ref_level <= 0:
        raise ValueError("Reference metrics must be positive")

    lut_n = lut / ref_lut
    lev_n = level / ref_level

    qor = lut_n + lev_n   # baseline = 2.0

    ref_qor = 2.0
    improve = (ref_qor - qor) / ref_qor * 100.0

    return qor, improve


# ==========================================================
# MAIN TEST
# ==========================================================
if __name__ == "__main__":
    import random

    # benchmark
    design = "./benchmarks/epfl/arithmetic/adder.blif"
    lut_k = 6

    # random genome: 40 bits = 10 macros
    bits = [random.randint(0, 1) for _ in range(40)]

    print("BITS  :", "".join(map(str, bits)))
    print("SCRIPT:", bits_to_script(bits))

    # reference genome (random for demo)
    ref_bits = [0,1,1,0, 0,0,0,0, 0,0,1,0, 0,1,1,0, 0,0,0,0, 0,0,0,1, 0,1,1,0, 0,0,1,1, 0,0,0,1, 0,1,1,0]

    print("\n=== RUN REFERENCE ===")
    ref_lut, ref_level = evaluate_design(design, ref_bits, lut_k)
    print(f"REF lut={ref_lut}, level={ref_level}")

    print("\n=== RUN TEST ===")
    lut, level = evaluate_design(design, bits, lut_k)
    print(f"TEST lut={lut}, level={level}")

    qor, improve = fitness(ref_lut, ref_level, lut, level)
    print(f"\nQoR = {qor:.6f}")
    print(f"Improve = {improve:.2f} %")
