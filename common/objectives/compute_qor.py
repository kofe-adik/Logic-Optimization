# common/objectives/qor.py

from typing import Dict

def compute_qor(metrics: Dict[str, float], ref_metrics: Dict[str, float]) -> float:
    """
    Compute QoR = lut/ref_lut + levels/ref_levels
    """
    try:
        lut = metrics["lut"]
        levels = metrics["levels"]
        ref_lut = ref_metrics["lut"]
        ref_levels = ref_metrics["levels"]
    except KeyError as e:
        raise KeyError(f"Missing metric key: {e}")

    if ref_lut == 0 or ref_levels == 0:
        raise ValueError("Reference metrics must be non-zero")

    return (lut / ref_lut) + (levels / ref_levels)

