from typing import List, Dict

from common.action_space.actions import Action
from common.action_space.primitives import *

INIT: List[Action] = [
    BALANCE,
]

RESYN: List[Action] = [
    BALANCE,
    REWRITE,
    REWRITE_Z,
    BALANCE,
    REWRITE_Z,
    BALANCE,
]

RESYN2: List[Action] = [
    BALANCE,
    REWRITE,
    REFACTOR,
    BALANCE,
    REWRITE,
    REWRITE_Z,
    BALANCE,
    REFACTOR_Z,
    REWRITE_Z,
    BALANCE,
]

BUILD_IN_SEQS: Dict[str, List[Action]] = {
    "init": INIT,
    "resyn": RESYN,
    "resyn2": RESYN2,
}

