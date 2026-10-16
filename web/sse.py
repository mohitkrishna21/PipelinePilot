
import json


def sse(event: str, data: dict | list) -> str:
    payload = json.dumps(data)

    return f"event: {event}\ndata: {payload}\n\n"
