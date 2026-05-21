
import requests
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import JIRA_BASE_URL, JIRA_AUTH, JIRA_HEADERS


def create_issue(summary, description_text, priority="Medium"):


    url = f"{JIRA_BASE_URL}/rest/api/3/issue"

    
    description = {
        "type": "doc",
        "version": 1,
        "content": [{
            "type": "paragraph",
            "content": [{"type": "text", "text": description_text}]
        }]
    }

    payload = {
        "fields": {
            "project":     {"key": os.getenv("JIRA_PROJECT", "ITS")},
            "summary":     summary,
            "description": description,
            "issuetype":   {"name": "Task"},
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
            return response.json()["key"]

        elif response.status_code == 400:
            print(f"  Jira 400: {response.json().get('errors')}")
        elif response.status_code == 401:
            print("  Jira 401 — check email and token in .env")
        elif response.status_code == 403:
            print("  Jira 403 — no permission to create tickets")
        else:
            print(f"  Jira {response.status_code}: {response.text}")

    except requests.exceptions.Timeout:
        print("  Jira timed out")
    except requests.exceptions.ConnectionError:
        print("  Cannot connect to Jira — check JIRA_BASE_URL")

    return None


def get_issue_status(issue_key):


    url    = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    params = {"fields": "status,resolution"}

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
                "status": fields["status"]["name"],
                "resolution": fields["resolution"]["name"]
                              if fields.get("resolution") else None
            }

        elif response.status_code == 404:
            print(f"  Ticket {issue_key} not found")
        else:
            print(f"  Jira {response.status_code}: {response.text}")

    except Exception as e:
        print(f"  Jira error: {e}")

    return None


def add_comment(issue_key, comment_text):


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


def search_issues(jql, fields=None):


    url    = f"{JIRA_BASE_URL}/rest/api/3/issue/search"
    params = {
        "jql":        jql,
        "fields":     ",".join(fields or ["summary", "status",
                                           "assignee", "created"]),
        "maxResults": 50
    }

    try:
        response = requests.get(
            url,
            headers=JIRA_HEADERS,
            auth=JIRA_AUTH,
            params=params,
            timeout=10
        )

        if response.status_code == 200:
            return response.json()["issues"]
        else:
            print(f"  Search error: {response.status_code}")

    except Exception as e:
        print(f"  Search error: {e}")

    return []