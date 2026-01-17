from typing import List, Dict

# import trực tiếp class cần test
from common.action_space.actions import Action, ActionSimple, ActionComposed


def test_basic_actions():
    a = Action("raw", "opt; balance;")
    b = ActionSimple("rewrite")
    c = ActionComposed("balance")

    actions: List[Action] = [a, b, c]

    print("=== Action objects ===")
    for act in actions:
        print(act)
        print("  name:", act.name)
        print("  cmd :", act.cmd)
        print()


def test_action_in_dict():
    a = ActionSimple("opt")
    b = ActionComposed("rewrite")

    action_map: Dict[str, Action] = {
        a.name: a,
        b.name: b,
    }

    print("=== Action dict ===")
    for k, v in action_map.items():
        print(f"{k} -> {v.cmd}")


if __name__ == "__main__":
    test_basic_actions()
    print("-" * 40)
    test_action_in_dict()

