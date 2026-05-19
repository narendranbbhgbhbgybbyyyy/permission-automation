# ============================================================
# settings.py
# Single place that loads ALL configuration.
# Every other file imports from here.
# Credentials never appear anywhere else in the codebase.
# ============================================================

import os
import json
from dotenv import load_dotenv

# Load .env from config folder
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=dotenv_path, override=True)

# ── Jira settings ───────────────────────────────────────────
JIRA_BASE_URL  = os.getenv("JIRA_BASE_URL")
JIRA_EMAIL     = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_PROJECT   = os.getenv("JIRA_PROJECT")

JIRA_AUTH = (JIRA_EMAIL, JIRA_API_TOKEN)
JIRA_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

# ── Graph API settings ──────────────────────────────────────
GRAPH_TENANT_ID     = os.getenv("GRAPH_TENANT_ID")
GRAPH_CLIENT_ID     = os.getenv("GRAPH_CLIENT_ID")
GRAPH_CLIENT_SECRET = os.getenv("GRAPH_CLIENT_SECRET")
GRAPH_BASE          = "https://graph.microsoft.com/v1.0"

# ── Group ID mapping ────────────────────────────────────────
# Maps system name to Entra ID security group object ID
# Add new systems here as they are onboarded
GROUP_MAPPING = {
    "SharePoint-ReadOnly":   os.getenv("GROUP_SharePoint_ReadOnly"),
    "SharePoint-FullAccess": os.getenv("GROUP_SharePoint_FullAccess")
}

# ── Load systems.json ───────────────────────────────────────
# Read fresh on every import — no restart needed after updates
SYSTEMS_FILE = os.path.join(os.path.dirname(__file__), "systems.json")

def load_systems():
    """
    Loads system risk configuration from systems.json.
    Called fresh each time — config changes take effect immediately.
    """
    try:
        with open(SYSTEMS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print("ERROR: systems.json not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"ERROR: systems.json is invalid JSON: {e}")
        return {}

SYSTEMS = load_systems()