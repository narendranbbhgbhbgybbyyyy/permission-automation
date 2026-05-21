import requests
import os
from dotenv import load_dotenv

load_dotenv("config/.env")

BASE_URL  = os.getenv("JIRA_BASE_URL")
EMAIL     = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")

# Try getting a specific ticket directly
# Replace ITS-1 with your actual first ticket key
response = requests.get(
    f"{BASE_URL}/rest/api/3/issue/ITS-1",
    headers={"Accept": "application/json"},
    auth=(EMAIL, API_TOKEN),
    timeout=10
)

print("Status:", response.status_code)
if response.status_code == 200:
    fields = response.json()["fields"]
    print("Summary:", fields["summary"])
    print("Status:", fields["status"]["name"])
else:
    print("Error:", response.text[:200])