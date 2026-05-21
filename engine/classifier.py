
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import SYSTEMS


def classify(system):


    config = SYSTEMS.get(system)

    if not config:
        return {
            "decision":         "needs_approval",
            "risk":             "high",
            "approver_group":   "SG-Default-Approvers",
            "fallback_approver": "it-manager@company.com",
            "sla_hours":        4
        }

    risk = config.get("risk", "high")

    
    if risk == "low":
        return {
            "decision":         "auto_approve",
            "risk":             risk,
            "approver_group":   None,
            "fallback_approver": None,
            "sla_hours":        0
        }

    
    return {
        "decision":          "needs_approval",
        "risk":              risk,
        "approver_group":    config.get("approver_group"),
        "fallback_approver": config.get("fallback_approver"),
        "sla_hours":         config.get("sla_hours", 8)
    }