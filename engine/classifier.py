# engine/classifier.py
# Reads systems.json and decides the approval path.
# Low risk = auto approve.
# Medium/High risk = needs approval.

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import SYSTEMS


def classify(system):
    """
    Returns the approval decision for a system request.
    Reads fresh from systems.json on every call.
    So config changes take effect immediately — no restart needed.

    Returns dict with:
    - decision: auto_approve / needs_approval
    - risk: low / medium / high
    - approver_group: group name or None
    - fallback_approver: email or None
    - sla_hours: int
    """

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

    # Low risk — no approval needed
    if risk == "low":
        return {
            "decision":         "auto_approve",
            "risk":             risk,
            "approver_group":   None,
            "fallback_approver": None,
            "sla_hours":        0
        }

    # Medium or high — needs approval
    return {
        "decision":          "needs_approval",
        "risk":              risk,
        "approver_group":    config.get("approver_group"),
        "fallback_approver": config.get("fallback_approver"),
        "sla_hours":         config.get("sla_hours", 8)
    }