"""One-shot helper to register the QVM API service on Render.

Credentials are read from the environment - never hardcode them:

    export RENDER_API_KEY=rnd_...
    export RENDER_OWNER_ID=tea_...
    export SUPABASE_URL=https://<ref>.supabase.co
    export SUPABASE_KEY=<anon-or-service-key>
    python deploy_render.py
"""
import json
import os
import sys

import requests

RENDER_API_KEY = os.environ.get("RENDER_API_KEY")
RENDER_OWNER_ID = os.environ.get("RENDER_OWNER_ID")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

missing = [name for name, val in [
    ("RENDER_API_KEY", RENDER_API_KEY),
    ("RENDER_OWNER_ID", RENDER_OWNER_ID),
    ("SUPABASE_URL", SUPABASE_URL),
    ("SUPABASE_KEY", SUPABASE_KEY),
] if not val]
if missing:
    sys.exit(f"Missing required environment variables: {', '.join(missing)}")

url = "https://api.render.com/v1/services"

payload = {
    "type": "web_service",
    "name": "qvm-api",
    "ownerId": RENDER_OWNER_ID,
    "repo": "https://github.com/qayumXD/quantum-virtual-machine",
    "autoDeploy": "yes",
    "branch": "main",
    "envVars": [
        {"key": "SUPABASE_URL", "value": SUPABASE_URL},
        {"key": "SUPABASE_KEY", "value": SUPABASE_KEY},
    ],
    "serviceDetails": {
        "plan": "free",
        "env": "docker",
        "region": "singapore",
        "envSpecificDetails": {
            "dockerCommand": "",
            "dockerContext": "."
        }
    }
}

headers = {
    "Accept": "application/json",
    "Authorization": f"Bearer {RENDER_API_KEY}",
    "Content-Type": "application/json",
}

response = requests.post(url, json=payload, headers=headers, timeout=30)

print(response.status_code)
try:
    print(json.dumps(response.json(), indent=2))
except ValueError:
    print(response.text)
