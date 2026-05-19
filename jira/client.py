# ============================================================
# jira/client.py
# All Jira REST API calls in one place.
# Nothing else in the system calls Jira directly.
# If Jira changes their API — update this file only.
#
# Official docs:
# developer.atlassian.com/cloud/jira/platform/rest/v3/
# ============================================================

import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import JIRA_BASE_URL, JIRA_AUTH, JIRA_HEADERS


# ============================================================
# CREATE ISSUE
# POST /rest/api/3/issue
# Required: project.key, summary, issuetype.name
# Response: 201 Created — body contains issue key
# Description must be ADF format — plain text returns 400
# ============================================================
def create_issue(summary, description_text,
                 priority="Medium", issue_type="Task"):
    """
    Creates a Jira ticket.
    Description automatically converted to ADF format.
    Returns issue key on success, None on failure.
    """

    url = f"{JIRA_BASE_URL}/rest/api/3/issue"

    # ADF format required by Jira API v3
    description = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": description_text
                    }
                ]
            }
        ]
    }

    payload = {
        "fields": {
            "project":     {"key": os.getenv("JIRA_PROJECT", "ITS")},
            "summary":     summary,
            "description": description,
            "issuetype":   {"name": issue_type},
            "priority":    {"name": priority}
        }
    }

    try:
        response = requests.post(
            url,
            headers=JIRA_HEADERS,
            auth=JIRA_AUTH,
            json=payload,
            timeout=10
        )

        if response.status_code == 201:
            key = response.json()["key"]
            return key

        elif response.status_code == 400:
            print(f"  Jira 400: {response.json().get('errors')}")
        elif response.status_code == 401:
            print("  Jira 401: Check email and token in .env")
        elif response.status_code == 403:
            print("  Jira 403: No permission to create tickets")
        else:
            print(f"  Jira {response.status_code}: {response.text}")

    except requests.exceptions.Timeout:
        print("  Jira timeout — not responding")
    except requests.exceptions.ConnectionError:
        print("  Jira connection error — check JIRA_BASE_URL")

    return None


# ============================================================
# GET ISSUE STATUS
# GET /rest/api/3/issue/{issueKey}
# Returns current status name
# ============================================================
def get_issue_status(issue_key):
    """
    Gets the current status of a Jira ticket.
    Returns status name string or None on failure.
    """

    url    = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    params = {"fields": "status,resolution,assignee"}

    try:
        response = requests.get(
            url,
            headers=JIRA_HEADERS,
            auth=JIRA_AUTH,
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            fields = response.json()["fields"]
            return {
                "status":     fields["status"]["name"],
                "resolution": fields.get("resolution", {}).get("name")
                              if fields.get("resolution") else None,
                "assignee":   fields.get("assignee", {}).get(
                              "emailAddress") if fields.get("assignee")
                              else None
            }

        elif response.status_code == 404:
            print(f"  Ticket {issue_key} not found")
        else:
            print(f"  Jira {response.status_code}: {response.text}")

    except Exception as e:
        print(f"  Jira error: {e}")

    return None


# ============================================================
# GET TRANSITIONS
# GET /rest/api/3/issue/{issueKey}/transitions
# Returns list of available transitions with IDs
# Must use ID not name to transition a ticket
# ============================================================
def get_transitions(issue_key):
    """
    Gets available workflow transitions for a ticket.
    Returns dict mapping transition name to ID.
    """

    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"

    try:
        response = requests.get(
            url,
            headers=JIRA_HEADERS,
            auth=JIRA_AUTH,
            timeout=10
        )

        if response.status_code == 200:
            transitions = response.json()["transitions"]
            return {
                t["to"]["name"]: t["id"]
                for t in transitions
            }

    except Exception as e:
        print(f"  Transitions error: {e}")

    return {}


# ============================================================
# TRANSITION ISSUE
# POST /rest/api/3/issue/{issueKey}/transitions
# Body: { "transition": { "id": "transition-id" } }
# Response: 204 No Content = success
# ============================================================
def transition_issue(issue_key, transition_id):
    """
    Moves a ticket to a new status using transition ID.
    Returns True on success, False on failure.
    204 No Content = success — no body returned.
    """

    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/transitions"

    payload = {"transition": {"id": transition_id}}

    try:
        response = requests.post(
            url,
            headers=JIRA_HEADERS,
            auth=JIRA_AUTH,
            json=payload,
            timeout=10
        )

        # 204 = success — no body
        return response.status_code == 204

    except Exception as e:
        print(f"  Transition error: {e}")
        return False


# ============================================================
# ADD COMMENT
# POST /rest/api/3/issue/{issueKey}/comment
# Comment body also requires ADF format
# Response: 201 Created
# ============================================================
def add_comment(issue_key, comment_text):
    """
    Adds a comment to an existing Jira ticket.
    Comment body uses ADF format — same as description.
    Returns True on success.
    """

    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"

    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{
                "type": "paragraph",
                "content": [{"type": "text", "text": comment_text}]
            }]
        }
    }

    try:
        response = requests.post(
            url,
            headers=JIRA_HEADERS,
            auth=JIRA_AUTH,
            json=payload,
            timeout=10
        )
        return response.status_code == 201

    except Exception as e:
        print(f"  Comment error: {e}")
        return False


# ============================================================
# SEARCH WITH JQL
# POST /rest/api/3/issue/search
# JQL = Jira Query Language — like SQL for Jira
# Used for SLA monitoring and overdue ticket detection
# ============================================================
def search_issues(jql, fields=None):
    """
    Searches Jira tickets using JQL query.
    Used for SLA breach detection and overdue monitoring.
    Returns list of issue objects.
    """

    url = f"{JIRA_BASE_URL}/rest/api/3/issue/search"

    payload = {
        "jql":        jql,
        "fields":     fields or ["summary", "status",
                                  "assignee", "created",
                                  "priority"],
        "maxResults": 50
    }

    try:
        response = requests.post(
            url,
            headers=JIRA_HEADERS,
            auth=JIRA_AUTH,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()["issues"]
        else:
            print(f"  Search error: {response.status_code}")

    except Exception as e:
        print(f"  Search error: {e}")

    return []