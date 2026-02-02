from common.action_space.actions import Action, ActionSimple, ActionComposed

# ActionSimple
BALANCE    = ActionSimple("balance")
REWRITE    = ActionSimple("rewrite")
REFACTOR   = ActionSimple("refactor")
RESUB      = ActionSimple("resub")
FRAIG      = ActionSimple("fraig")
STRASH     = ActionSimple("strash")

# Action (custom cmd)
REWRITE_Z  = Action("rewrite_z",  "rewrite -z;")
REFACTOR_Z = Action("refactor_z", "refactor -z;")
RESUB_Z    = Action("resub_z",    "resub -z;")

# ActionComposed
SOPB = ActionComposed("&sopb")
BLUT = ActionComposed("&blut")
DSDB = ActionComposed("&dsdb")


