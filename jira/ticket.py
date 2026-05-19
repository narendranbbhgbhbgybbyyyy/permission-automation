# ============================================================
# jira/ticket.py
# Higher level ticket operations built on jira/client.py.
# Handles ticket creation with full context and polling logic.
# ============================================================

import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from jira.client import (create_issue, get_issue_status,
                          add_comment, search_issues)
from config.settings import JIRA_BASE_URL, SYSTEMS


def build_description(user_id, system,
                      justification, risk_level,
                      approver_group):
    """
    Builds a structured ticket description.
    Shows all context the approver needs to make a decision.
    """

    system_config = SYSTEMS.get(system, {})
    description   = system_config.get("description", system)

    return (
        f"PERMISSION REQUEST\n\n"
        f"User ID: {user_id}\n"
        f"System: {system}\n"
        f"System description: {description}\n"
        f"Risk level: {risk_level.upper()}\n"
        f"Justification: {justification}\n\n"
        f"Approver group: {approver_group}\n\n"
        f"ACTION ON APPROVAL:\n"
        f"User will be automatically added to the "
        f"Entra ID security group via Graph API.\n"
        f"No manual IT action required after approval.\n\n"
        f"ACTION ON REJECTION:\n"
        f"Request will be logged and requester notified.\n"
        f"No access will be granted."
    )


def create_approval_ticket(user_id, system,
                           justification, risk_level,
                           approver_group):
    """
    Creates a Jira approval ticket with full context.
    Priority set based on risk level.
    Returns issue key on success, None on failure.
    """

    # Map risk level to Jira priority
    priority_map = {
        "low":    "Low",
        "medium": "Medium",
        "high":   "High"
    }

    summary     = f"Access request — {system} — User {user_id}"
    description = build_description(
        user_id, system, justification,
        risk_level, approver_group
    )
    priority    = priority_map.get(risk_level, "Medium")

    print(f"\n  Creating Jira approval ticket...")
    print(f"  System: {system} | Risk: {risk_level} | Priority: {priority}")

    key = create_issue(summary, description,
                       priority=priority)

    if key:
        print(f"  Ticket created: {key}")
        print(f"  View at: {JIRA_BASE_URL}/browse/{key}")
        add_comment(
            key,
            f"Automated system: This request requires "
            f"{risk_level} risk approval. "
            f"Assigned to approver group: {approver_group}. "
            f"SLA monitoring is active."
        )
    return key


def poll_for_approval(issue_key,
                      interval=30,
                      max_polls=20,
                      system="",
                      sla_hours=8):
    """
    Polls a Jira ticket every interval seconds.
    Stops when status is Done or max_polls reached.
    Adds SLA warning comment when half the SLA has elapsed.
    Returns True if approved, False if timeout or rejected.
    """

    print(f"\n  Monitoring ticket {issue_key}...")
    print(f"  Checking every {interval} seconds")
    print(f"  Go to Jira and move ticket to Done to approve")
    print(f"  URL: {JIRA_BASE_URL}/browse/{issue_key}\n")

    # Calculate when to send SLA warning
    total_seconds    = sla_hours * 3600
    half_sla_seconds = total_seconds / 2
    elapsed_seconds  = 0
    sla_warning_sent = False

    for poll in range(1, max_polls + 1):

        result = get_issue_status(issue_key)

        if result:
            status = result["status"]
            from datetime import datetime, timezone
            time_now = datetime.now(
                timezone.utc).strftime("%H:%M:%S")
            print(f"  [{poll:02d}] {time_now} UTC "
                  f"— Status: {status}")

            # Approved
            if status == "Done":
                print(f"\n  APPROVED — proceeding to grant access")
                return "approved"

            # Rejected — check resolution
            if (status in ["Cancelled", "Rejected"] or
                    result.get("resolution") == "Won't Do"):
                print(f"\n  REJECTED — no access will be granted")
                return "rejected"

        # SLA warning — send once at halfway point
        elapsed_seconds += interval
        if (not sla_warning_sent and
                sla_hours > 0 and
                elapsed_seconds >= half_sla_seconds):
            add_comment(
                issue_key,
                f"SLA WARNING: This request has been pending "
                f"for {elapsed_seconds // 3600} hours. "
                f"SLA is {sla_hours} hours. "
                f"Please approve or reject."
            )
            sla_warning_sent = True
            print(f"  SLA warning comment added to {issue_key}")

        if poll < max_polls:
            time.sleep(interval)

    # Timeout
    add_comment(
        issue_key,
        f"TIMEOUT: Request not actioned within the "
        f"polling window. Manual review required."
    )
    print(f"\n  Timeout — ticket not resolved")
    return "timeout"


def check_sla_breaches(project):
    """
    Queries Jira for open tickets past their SLA.
    Used by scheduled SLA monitoring job.
    Returns list of overdue tickets.
    """

    # JQL — find open tickets older than 4 hours
    jql = (f"project = {project} AND "
           f"status != Done AND "
           f"status != Cancelled AND "
           f"created <= -4h AND "
           f"summary ~ 'Access request'")

    overdue = search_issues(jql)

    if overdue:
        print(f"\n  Found {len(overdue)} potentially "
              f"overdue tickets")
        for ticket in overdue:
            key     = ticket["key"]
            summary = ticket["fields"]["summary"]
            print(f"  → {key}: {summary}")

    return overdue