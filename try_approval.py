import json
import sys

import httpx

BASE = "http://127.0.0.1:8001"
approved = (sys.argv[1] == "y") if len(sys.argv) > 1 else True
message = "Mark Amazon as followed up with this note: Followed up on my application."

session_id = None

with httpx.Client(timeout=None) as client:
    with client.stream("POST", f"{BASE}/chat", json={"message": message}) as resp:
        event = None
        for line in resp.iter_lines():
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
                print(event, str(data)[:110])

                if event == "session":
                    session_id = data["session_id"]

                if event == "approval_required":
                    r = client.post(
                        f"{BASE}/approve",
                        json={"session_id": session_id, "approved": approved},
                    )
                    print("approve ->", r.json())
                    