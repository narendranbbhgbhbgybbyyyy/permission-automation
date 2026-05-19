# engine/workflow.py
# Orchestrates the entire permission request flow.
# Calls validator, classifier, jira, graph, and audit logger.

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from engine.validator  import validate
from engine.classifier import classify
from graph.client      import get_token
from graph.provisioner import add_user, remove_user, verify_membership
from jira.ticket       import create_approval_ticket, poll_for_approval
from audit.logger      import (write_log, log_request_received,
                                log_validation_failed, log_auto_approved,
                                log_approval_required, log_ticket_approved,
                                log_ticket_rejected, log_access_granted,
                                log_access_failed, log_membership_verified)


def get_group_id(system):
    """
    Reads GROUP_MAPPING fresh every time.
    Avoids stale import issues.
    """
    # Re-import settings fresh to get latest values
    if "config.settings" in sys.modules:
        del sys.modules["config.settings"]

    from config.settings import GROUP_MAPPING
    group_id = GROUP_MAPPING.get(system)
    return group_id


def run(user_id, system, justification):
    """
    Runs the complete permission request workflow.

    Two paths:
    1. Low risk  — auto approve and grant access immediately
    2. High risk — create Jira ticket, wait for approval
    """

    print(f"\n{'='*55}")
    print(f"Permission Request")
    print(f"{'='*55}")
    print(f"User   : {user_id}")
    print(f"System : {system}")
    print(f"Reason : {justification}")
    print(f"{'='*55}")

    # Step 1: Validate
    print("\nStep 1 — Validating request...")
    errors = validate(user_id, system, justification)

    if errors:
        print("  Validation failed:")
        for error in errors:
            print(f"  - {error}")
        log_validation_failed(user_id, system, errors)
        return False

    print("  Request is valid")

    # Step 2: Classify
    print("\nStep 2 — Checking risk level...")
    result   = classify(system)
    risk     = result["risk"]
    decision = result["decision"]

    print(f"  Risk level : {risk.upper()}")
    print(f"  Decision   : {decision}")

    log_request_received(user_id, system, risk)

    # Step 3: Get Graph token
    print("\nStep 3 — Getting Graph API token...")
    token = get_token()

    if not token:
        print("  Failed to get token — check Graph credentials")
        log_access_failed(user_id, system, "Token failed")
        return False

    print("  Token received")

    # Step 4: Get group ID
    group_id = get_group_id(system)

    if not group_id:
        print(f"  No group ID found for {system}")
        print(f"  Check GROUP_SharePoint_ReadOnly in config/.env")
        log_access_failed(user_id, system, "No group ID")
        return False

    # Path A: Auto approve (low risk)
    if decision == "auto_approve":
        print(f"\nStep 4 — Auto approving (low risk)...")
        log_auto_approved(user_id, system)
        return grant_access(token, user_id,
                            system, group_id,
                            ticket_key="auto")

    # Path B: Needs approval (high risk)
    print(f"\nStep 4 — Creating approval ticket in Jira...")

    ticket = create_approval_ticket(
        user_id        = user_id,
        system         = system,
        justification  = justification,
        risk_level     = risk,
        approver_group = result["approver_group"]
    )

    if not ticket:
        print("  Failed to create ticket")
        log_access_failed(user_id, system, "Ticket creation failed")
        return False

    log_approval_required(user_id, system, risk, ticket)

    # Step 5: Wait for approval
    print(f"\nStep 5 — Waiting for approval...")
    outcome = poll_for_approval(
        issue_key = ticket,
        interval  = 30,
        max_polls = 20,
        system    = system,
        sla_hours = result["sla_hours"]
    )

    # Step 6: Act on outcome
    if outcome == "approved":
        log_ticket_approved(user_id, system, ticket)
        return grant_access(token, user_id,
                            system, group_id,
                            ticket_key=ticket)

    elif outcome == "rejected":
        print("\n  Request rejected — no access granted")
        log_ticket_rejected(user_id, system, ticket)
        return False

    else:
        print("\n  Timeout — ticket not actioned in time")
        write_log("request_timeout", "Timeout",
                  user_id=user_id, system=system,
                  ticket_key=ticket)
        return False


def grant_access(token, user_id, system,
                 group_id, ticket_key="auto"):
    """
    Adds user to Entra ID group and verifies membership.
    Called for both auto-approved and manually approved requests.
    """

    print(f"\n  Granting access to {system}...")
    print(f"  Adding user to Entra ID group...")

    added = add_user(token, user_id, group_id)

    if not added:
        log_access_failed(user_id, system, "Group add failed")
        return False

    log_access_granted(user_id, system, ticket_key)

    # Wait for Graph API to propagate
    print("  Verifying membership...")
    time.sleep(5)

    verified = verify_membership(token, user_id, group_id)

    if verified:
        log_membership_verified(user_id, system)

    print(f"\n{'='*55}")
    print(f"  ACCESS GRANTED")
    print(f"  User   : {user_id}")
    print(f"  System : {system}")
    print(f"  Group  : {group_id}")
    print(f"  Ticket : {ticket_key}")
    print(f"{'='*55}")

    return True


def remove_access(token, user_id, system, group_id, reason):
    """
    Removes a user from an Entra ID group.
    Used for permission removal and leaver flows.
    """

    print(f"\n  Removing access to {system}...")

    removed = remove_user(token, user_id, group_id)

    if removed:
        write_log("access_removed", "Success",
                  user_id=user_id, system=system,
                  detail=reason)
        print(f"  Access removed")
        return True

    write_log("access_remove_failed", "Failed",
              user_id=user_id, system=system)
    return False