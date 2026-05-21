import csv
import os
from datetime import datetime, timezone

LOG_FILE = "audit_log.csv"

FIELDS = ["timestamp", "action", "user_id",
          "system", "risk_level", "ticket_key",
          "result", "detail"]


def write_log(action, result, user_id="", system="",
              risk_level="", ticket_key="", detail=""):

    timestamp  = datetime.now(timezone.utc).isoformat()
    log_exists = os.path.isfile(LOG_FILE)

    try:
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            if not log_exists:
                writer.writeheader()
            writer.writerow({
                "timestamp":  timestamp,
                "action":     action,
                "user_id":    user_id,
                "system":     system,
                "risk_level": risk_level,
                "ticket_key": ticket_key,
                "result":     result,
                "detail":     detail
            })
    except IOError as e:
        print(f"  Could not write to audit log: {e}")


def show_log():
    if not os.path.isfile(LOG_FILE):
        print("No audit log found")
        return

    print(f"\n{'='*70}")
    print("AUDIT LOG")
    print(f"{'='*70}")
    print(f"{'Timestamp':<28} {'Action':<30} {'Result':<10} {'System'}")
    print("-" * 80)

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(f"{row['timestamp']:<28} "
                  f"{row['action']:<30} "
                  f"{row['result']:<10} "
                  f"{row['system']}")


def log_request_received(user_id, system, risk_level):
    write_log("request_received", "Success",
              user_id=user_id, system=system,
              risk_level=risk_level)


def log_validation_failed(user_id, system, errors):
    write_log("validation_failed", "Failed",
              user_id=user_id, system=system,
              detail=str(errors))


def log_auto_approved(user_id, system):
    write_log("auto_approved", "Success",
              user_id=user_id, system=system,
              risk_level="low")


def log_approval_required(user_id, system, risk_level, ticket_key):
    write_log("approval_required", "Pending",
              user_id=user_id, system=system,
              risk_level=risk_level, ticket_key=ticket_key)


def log_ticket_approved(user_id, system, ticket_key):
    write_log("ticket_approved", "Success",
              user_id=user_id, system=system,
              ticket_key=ticket_key)


def log_ticket_rejected(user_id, system, ticket_key):
    write_log("ticket_rejected", "Rejected",
              user_id=user_id, system=system,
              ticket_key=ticket_key)


def log_access_granted(user_id, system, ticket_key="auto"):
    write_log("access_granted", "Success",
              user_id=user_id, system=system,
              ticket_key=ticket_key)


def log_access_failed(user_id, system, detail):
    write_log("access_failed", "Failed",
              user_id=user_id, system=system,
              detail=detail)


def log_membership_verified(user_id, system):
    write_log("membership_verified", "Success",
              user_id=user_id, system=system)


def log_sla_breach(ticket_key, system, hours_overdue):
    write_log("sla_breach", "Escalated",
              system=system, ticket_key=ticket_key,
              detail=f"Overdue by {hours_overdue} hours")