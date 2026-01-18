from pathlib import Path
from typing import Dict, Any
import json
import pickle


def write_result(
    result_dir: Path,
    metrics: Dict[str, Any],
    write_json: bool = True,
    write_pkl: bool = True,
) -> None:
    """
    Write evaluation result to disk.

    Args:
        result_dir: directory like
            results/refs/<script>/<option>/<design>/
        metrics: dict containing at least {"lut": int, "levels": int}
        write_json: whether to write result.json
        write_pkl: whether to write result.pkl
    """
    result_dir.mkdir(parents=True, exist_ok=True)

    if write_json:
        json_path = result_dir / "result.json"
        with open(json_path, "w") as f:
            json.dump(metrics, f, indent=2)

    if write_pkl:
        pkl_path = result_dir / "result.pkl"
        with open(pkl_path, "wb") as f:
            pickle.dump(metrics, f)

