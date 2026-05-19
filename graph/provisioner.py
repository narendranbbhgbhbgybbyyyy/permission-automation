# graph/provisioner.py
# Adds and removes users from Entra ID security groups
# Official docs: learn.microsoft.com/graph/api/group-post-members

import requests
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import GRAPH_BASE


def add_user(token, user_id, group_id):
    """
    Adds a user to an Entra ID security group.
    Returns True on success, False on failure.
    204 No Content = success — Graph API returns no body.
    """

    url     = f"{GRAPH_BASE}/groups/{group_id}/members/$ref"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json"
    }
    payload = {
        "@odata.id": f"{GRAPH_BASE}/users/{user_id}"
    }

    try:
        response = requests.post(
            url, headers=headers,
            json=payload, timeout=10
        )

        if response.status_code == 204:
            print(f"  User added to group successfully")
            return True

        elif response.status_code == 400:
            error = response.json()
            if "already exist" in str(error).lower():
                print(f"  User already in group — skipping")
                return True
            print(f"  Error 400: {error}")

        elif response.status_code == 403:
            print("  Error 403 — check Group.ReadWrite.All permission")

        else:
            print(f"  Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"  Add user error: {e}")

    return False


def remove_user(token, user_id, group_id):
    """
    Removes a user from an Entra ID security group.
    Used for permission removal and leaver flows.
    Returns True on success, False on failure.
    """

    url     = (f"{GRAPH_BASE}/groups/{group_id}"
               f"/members/{user_id}/$ref")
    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.delete(
            url, headers=headers, timeout=10
        )

        # 204 = success
        if response.status_code == 204:
            print(f"  User removed from group")
            return True

        elif response.status_code == 404:
            print(f"  User not in group — nothing to remove")
            return True

        else:
            print(f"  Error {response.status_code}: {response.text}")

    except Exception as e:
        print(f"  Remove user error: {e}")

    return False


def verify_membership(token, user_id, group_id):
    """
    Checks if a user is in a group.
    Retries 3 times — Graph API takes a few seconds to update.
    Returns True if confirmed, False otherwise.
    """

    url     = f"{GRAPH_BASE}/groups/{group_id}/members"
    headers = {"Authorization": f"Bearer {token}"}

    for attempt in range(1, 4):
        try:
            response = requests.get(
                url, headers=headers, timeout=10
            )

            if response.status_code == 200:
                members    = response.json()["value"]
                member_ids = [m["id"] for m in members]

                if user_id in member_ids:
                    print(f"  Verified — user is in the group")
                    return True

                print(f"  Not visible yet — attempt {attempt}/3")
                if attempt < 3:
                    time.sleep(5)

            else:
                print(f"  Verify error: {response.status_code}")

        except Exception as e:
            print(f"  Verify error: {e}")

    print("  Could not verify — check Azure portal")
    return False
    