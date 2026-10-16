import json
import time


def log_json(event, **fields) -> None:
    record = {
        "ts": time.time(),
        "event": event,
        **fields
    }

    print(json.dumps(record), flush=True)
