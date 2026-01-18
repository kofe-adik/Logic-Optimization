from pathlib import Path
from common.storage.result_writer import write_result

result_dir = Path(
    "results/refs/resyn2/fpga-6/adder"
)

metrics = {
    "lut": 257,
    "levels": 51,
}

write_result(result_dir, metrics)

