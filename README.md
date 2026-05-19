# Permission Request Automation

Automated permission request workflow using Jira REST API 
and Microsoft Graph API.

## What it does

- Employee submits a permission request
- System checks risk level from configuration
- Low risk → access granted automatically
- High risk → Jira approval ticket created
- On approval → user added to Entra ID security group
- Every action logged to audit CSV

## Tech stack

- Python
- Jira REST API (Atlassian)
- Microsoft Graph API (Entra ID)

## Project structure
permission-automation/
├── audit/          # Audit logging
├── config/         # Settings and system risk config
├── engine/         # Validation, classification, workflow
├── graph/          # Graph API client and provisioner
├── jira/           # Jira API client and ticket handling
├── main.py         # Entry point
└── requirements.txt

## Setup

1. Copy `config/.env.example` to `config/.env` and fill in credentials
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python main.py`

## Two request paths

**Low risk (SharePoint-ReadOnly)**
- Auto approved instantly
- No human involvement
- User added to Entra ID group immediately

**High risk (SharePoint-FullAccess)**
- Jira approval ticket created automatically
- Approver reviews and approves in Jira
- User added to Entra ID group on approval
- Full audit trail throughout

## Security

- Credentials stored in `.env` file — never in code
- `.gitignore` prevents credentials being committed
- Audit log uses record IDs only — no personal data values
- UTC timestamps throughout