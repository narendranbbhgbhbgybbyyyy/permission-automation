import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import SYSTEMS


def validate(user_id, system, justification):


    errors = []

   
    if not user_id or len(user_id.strip()) == 0:
        errors.append("User ID is required")

    
    if system not in SYSTEMS:
        known = ", ".join(SYSTEMS.keys())
        errors.append(
            f"Unknown system: {system}. "
            f"Known systems: {known}"
        )

    
    if not justification or len(justification.strip()) < 10:
        errors.append(
            "Justification must be at least 10 characters"
        )

    return errors