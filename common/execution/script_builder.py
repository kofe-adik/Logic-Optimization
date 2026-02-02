from typing import List
from common.action_space.actions import Action, MacroAction


def build_fpga_script(
    design_file: str,
    actions: List[Action],
    lut_k: int
) -> str:
    cmds = []
    cmds.append(f"read {design_file};")
    cmds.append("strash;")

    for act in actions:
        cmds.append(act.cmd)

    cmds.append(f"if -K {lut_k};")
    cmds.append("print_stats;")

    return " ".join(cmds)

def build_fpga_script_from_macro(
    design_file: str,
    macros: List[MacroAction],
    lut_k: int
) -> str:
    cmds = []
    cmds.append(f"read {design_file};")
    cmds.append("strash;")

    for m in macros:
        cmds.append(m.cmd)

    cmds.append(f"if -K {lut_k};")
    cmds.append("print_stats;")

    return " ".join(cmds)
