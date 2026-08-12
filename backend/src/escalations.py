import json
import os
from datetime import datetime


ESCALATION_FILE = "escalations.json"


def create_escalation(
    name: str,
    issue: str,
    checked: str,
    urgency: str,
    language: str,
    follow_up_method: str,
) -> str:

    if os.path.exists(ESCALATION_FILE):
        try:
            with open(ESCALATION_FILE, "r", encoding="utf-8") as f:
                requests = json.load(f)
        except Exception:
            requests = []
    else:
        requests = []

    reference_id = (
        f"FA-{datetime.now().strftime('%Y%m%d')}-"
        f"{len(requests) + 1:03d}"
    )

    request = {
        "reference_id": reference_id,
        "name": name,
        "issue": issue,
        "checked": checked,
        "urgency": urgency,
        "language": language,
        "follow_up_method": follow_up_method,
        "status": "open",
        "created_at": datetime.now().isoformat(),
    }

    requests.append(request)

    with open(ESCALATION_FILE, "w", encoding="utf-8") as f:
        json.dump(requests, f, indent=4)

    return reference_id
