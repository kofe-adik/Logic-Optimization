from typing import List, Dict

# ---------- Core abstraction ----------

class Action:
    def __init__(self, name: str, cmd: str):
        self.name = name
        self.cmd = cmd

    def __repr__(self):
        return f"{self.name}: {self.cmd}"


class ActionSimple(Action):
    def __init__(self, name: str):
        super().__init__(name, f"{name};")


class ActionComposed(Action):
    def __init__(self, name: str):
       super().__init__(name, f"&get -n; {name}; &put;")

class MacroAction:
    def __init__(self, id: int, cmd: str):
        self.id = id
        self.cmd = cmd      

