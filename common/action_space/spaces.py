from typing import Dict, List

from common.action_space.actions import Action
from common.action_space.primitives import *

STD_ACTION_SPACE: List[Action] = [
    REWRITE,
    REWRITE_Z,
    REFACTOR,
    REFACTOR_Z,
    RESUB,
    RESUB_Z,
    BALANCE,
]

EXTENDED_ACTION_SPACE: List[Action] = [
    *STD_ACTION_SPACE,
    FRAIG,
    SOPB,
    BLUT,
    DSDB,
]

STRASH_EXTENDED_ACTION_SPACE: List[Action] = [
    *EXTENDED_ACTION_SPACE,
    STRASH,
]

ACTION_SPACES: Dict[str, List[Action]] = {
    "standard": STD_ACTION_SPACE,
    "extended": EXTENDED_ACTION_SPACE,
    "strash_extended": STRASH_EXTENDED_ACTION_SPACE,
}
