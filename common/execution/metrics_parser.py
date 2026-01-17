# common/execution/metrics_parser.py

import re
from typing import Dict


class AbcStatsParseError(ValueError):
    pass


def parse_fpga_stats(stdout: str) -> Dict[str, int]:
    """
    Parse FPGA mapping stats from ABC stdout.

    Expected fields:
        - lev
        - nd

    Returns:
        dict(levels=..., lut=...)

    Raises:
        AbcStatsParseError if parsing fails
    """
    lines = stdout.strip().splitlines()

    stats_line = None
    for line in reversed(lines):
        if "lev" in line and "nd" in line:
            stats_line = line
            break

    if stats_line is None:
        raise AbcStatsParseError(
            "Cannot find stats line in ABC output"
        )

    def _extract(pattern: str, name: str) -> int:
        m = re.search(pattern, stats_line)
        if not m:
            raise AbcStatsParseError(
                f"Cannot parse {name} from line:\n{stats_line}"
            )
        return int(m.group(1))

    levels = _extract(r"lev\s*=\s*(\d+)", "levels")
    lut    = _extract(r"nd\s*=\s*(\d+)", "lut")

    return {
        "levels": levels,
        "lut": lut,
    }

