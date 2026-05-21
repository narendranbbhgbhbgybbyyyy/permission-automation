

import sys
import os
import json

from engine.workflow import run
from audit.logger    import show_log
from jira.ticket     import check_sla_breaches
from config.settings import JIRA_PROJECT


def get_input_from_commandline():
    
    print("\nEnter request details:")
    user_id       = input("User ID: ").strip()
    system        = input("System name: ").strip()
    justification = input("Justification: ").strip()
    return user_id, system, justification


def get_input_from_file(filepath):
  

    Expected format:
    {
        "user_id": "abc-123",
        "system": "SharePoint-ReadOnly",
        "justification": "Required for Q3 project"
    }
    
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
        return (
            data.get("user_id", ""),
            data.get("system", ""),
            data.get("justification", "")
        )

    except FileNotFoundError:
        print(f"File not found: {filepath}")
        sys.exit(1)

    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)


def check_sla():
  
    print("\nChecking for SLA breaches...")
    overdue = check_sla_breaches(JIRA_PROJECT)

    if not overdue:
        print("No overdue tickets found")
    else:
        print(f"\nFound {len(overdue)} overdue ticket(s):")
        for key in overdue:
            print(f"  {key} — escalation comment added")


def show_menu():
   
    print("\n" + "=" * 55)
    print("Permission Request Automation System")
    print("=" * 55)
    print("1 — New request (command line)")
    print("2 — New request (from request.json)")
    print("3 — Check SLA breaches")
    print("4 — View audit log")
    print("5 — Exit")
    print("=" * 55)


if __name__ == "__main__":

  
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        print(f"Reading request from: {filepath}")
        user_id, system, justification = get_input_from_file(filepath)
        success = run(user_id, system, justification)
        show_log()
        sys.exit(0 if success else 1)

   
    while True:
        show_menu()
        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            user_id, system, justification = get_input_from_commandline()
            run(user_id, system, justification)
            show_log()

        elif choice == "2":
            if not os.path.isfile("request.json"):
                sample = {
                    "user_id":       "your-user-object-id",
                    "system":        "SharePoint-ReadOnly",
                    "justification": "Required for Q3 project work"
                }
                with open("request.json", "w") as f:
                    json.dump(sample, f, indent=4)
                print("\nCreated sample request.json")
                print("Edit it with your details then choose option 2 again")
            else:
                user_id, system, justification = get_input_from_file("request.json")
                run(user_id, system, justification)
                show_log()

        elif choice == "3":
            check_sla()

        elif choice == "4":
            show_log()

        elif choice == "5":
            print("\nExiting")
            break

        else:
            print("Invalid choice — enter 1 to 5")
