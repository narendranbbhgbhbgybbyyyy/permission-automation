
import requests
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import (GRAPH_TENANT_ID, GRAPH_CLIENT_ID,
                              GRAPH_CLIENT_SECRET)


def get_token():
    

    url = (f"https://login.microsoftonline.com/"
           f"{GRAPH_TENANT_ID}/oauth2/v2.0/token")

    
    body = {
        "grant_type":    "client_credentials",
        "client_id":     GRAPH_CLIENT_ID,
        "client_secret": GRAPH_CLIENT_SECRET,
        "scope":         "https://graph.microsoft.com/.default"
    }

    try:
        response = requests.post(url, data=body, timeout=10)

        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            print(f"  Token failed: {response.status_code}")
            print(f"  {response.json().get('error_description')}")
            return None

    except requests.exceptions.Timeout:
        print("  Token request timed out")
        return None

    except Exception as e:
        print(f"  Token error: {e}")
        return None