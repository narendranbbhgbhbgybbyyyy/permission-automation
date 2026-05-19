# engine/validator.py
# Validates a request before doing anything with it.
# Catches bad input early — saves wasted API calls.

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import SYSTEMS


def validate(user_id, system, justification):
    """
    Checks the request is valid before processing.
    Returns a list of errors. Empty list means valid.
    """

    errors = []

    # Check user ID provided
    if not user_id or len(user_id.strip()) == 0:
        errors.append("User ID is required")

    # Check system name is known
    if system not in SYSTEMS:
        known = ", ".join(SYSTEMS.keys())
        errors.append(
            f"Unknown system: {system}. "
            f"Known systems: {known}"
        )

    # Check justification is meaningful
    if not justification or len(justification.strip()) < 10:
        errors.append(
            "Justification must be at least 10 characters"
        )

    return errors