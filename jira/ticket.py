# jira/ticket.py
# Ticket creation, polling, and SLA checking.
# Built on top of jira/client.py

import time
import csv
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from jira.client import create_issue, get_issue_status, add_comment
from config.settings import JIRA_BASE_URL, SYSTEMS


def build_description(user_id, system, justification,
                      risk_level, approver_group):
    """
    Builds the ticket description with all context
    the approver needs to make a decision.
    """
    system_desc = SYSTEMS.get(system, {}).get("description", system)

    return (
        f"PERMISSION REQUEST\n\n"
        f"User ID: {user_id}\n"
        f"System: {system}\n"
        f"Description: {system_desc}\n"
        f"Risk level: {risk_level.upper()}\n"
        f"Justification: {justification}\n\n"
        f"Approver group: {approver_group}\n\n"
        f"On approval: user added to Entra ID group automatically.\n"
        f"On rejection: no access will be granted."
    )


def create_approval_ticket(user_id, system, justification,
                           risk_level, approver_group):
    """
    Creates a Jira approval ticket with full context pre-filled.
    Returns issue key on success, None on failure.
    """

    priority_map = {"low": "Low", "medium": "Medium", "high": "High"}

    summary  = f"Access request — {system} — User {user_id}"
    priority = priority_map.get(risk_level, "Medium")

    print(f"\n  Creating Jira approval ticket...")
    print(f"  System: {system} | Risk: {risk_level} | Priority: {priority}")

    key = create_issue(
        summary          = summary,
        description_text = build_description(user_id, system,
                                             justification,
                                             risk_level,
                                             approver_group),
        priority         = priority
    )

    if key:
        print(f"  Ticket created: {key}")
        print(f"  View at: {JIRA_BASE_URL}/browse/{key}")
        add_comment(
            key,
            f"This request requires {risk_level} risk approval. "
            f"Approver group: {approver_group}. "
            f"SLA monitoring is active."
        )

    return key


def poll_for_approval(issue_key, interval=30, max_polls=20, sla_hours=8):
    """
    Checks ticket status every interval seconds.
    Returns approved / rejected / timeout.
    Sends SLA warning comment at the halfway point.
    """

    print(f"\n  Monitoring ticket {issue_key}...")
    print(f"  Checking every {interval} seconds")
    print(f"  Go to Jira and move the ticket to Done to approve")
    print(f"  URL: {JIRA_BASE_URL}/browse/{issue_key}\n")

    elapsed          = 0
    sla_warning_sent = False
    half_sla         = (sla_hours * 3600) / 2

    for poll in range(1, max_polls + 1):

        result = get_issue_status(issue_key)

        if result:
            status = result["status"]
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).strftime("%H:%M:%S")
            print(f"  [{poll:02d}] {now} UTC — Status: {status}")

            if status == "Done":
                print(f"\n  APPROVED — granting access")
                return "approved"

            if status in ["Cancelled", "Rejected"]:
                print(f"\n  REJECTED — no access granted")
                return "rejected"

        # Send SLA warning once at halfway point
        elapsed += interval
        if not sla_warning_sent and sla_hours > 0 and elapsed >= half_sla:
            add_comment(
                issue_key,
                f"SLA WARNING: This request has been pending for "
                f"{elapsed // 3600} hours. "
                f"SLA is {sla_hours} hours. Please action this ticket."
            )
            sla_warning_sent = True
            print(f"  SLA warning added to {issue_key}")

        if poll < max_polls:
            time.sleep(interval)

    # Timed out — get fallback contact from systems.json
    fallback = SYSTEMS.get(issue_key, {}).get("fallback_approver", "")
    timeout_msg = "TIMEOUT: This ticket was not actioned in time. Manual review required."
    if fallback:
        timeout_msg += f" Fallback contact: {fallback}"

    add_comment(issue_key, timeout_msg)
    print(f"\n  Timeout — ticket not resolved")
    return "timeout"


def check_sla_breaches(project):
    """
    Checks open approval tickets for SLA breaches.
    Reads ticket keys from audit_log.csv and checks each directly.
    Adds escalation comment to any still open.
    """

    log_file = "audit_log.csv"

    if not os.path.isfile(log_file):
        print("  No audit log found — no tickets to check")
        return []

    # Find all tickets created for approval
    pending = []
    with open(log_file, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if (row["action"] == "approval_required" and
                    row["ticket_key"] and
                    row["ticket_key"] != "auto"):
                pending.append(row["ticket_key"])

    # Remove duplicates
    pending = list(set(pending))

    if not pending:
        print("  No pending approval tickets in audit log")
        return []

    print(f"  Checking {len(pending)} ticket(s) from audit log...")

    overdue = []
    for key in pending:
        result = get_issue_status(key)

        if not result:
            continue

        status = result["status"]
        print(f"  → {key}: {status}")

        # Only escalate tickets still open
        if status not in ["Done", "Cancelled", "Rejected"]:
            overdue.append(key)
            add_comment(
                key,
                "SLA CHECK: This approval ticket is still open. "
                "Please approve or reject as soon as possible."
            )
            print(f"    Escalation comment added to {key}")

    if not overdue:
        print("  All tracked tickets are resolved")

    return overdue