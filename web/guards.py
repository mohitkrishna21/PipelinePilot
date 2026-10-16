
from collections import deque


def allow_request(hits, ip, max_per_min, now) -> bool:
    window = hits.setdefault(ip, deque())

    # Remove timestamps older than 60 seconds
    while window and now - window[0] >= 60:
        window.popleft()

    # Reject requests when the limit is reached
    if len(window) >= max_per_min:
        return False

    # Record the accepted request
    window.append(now)

    return True


def client_ip(request) -> str:
    forwarded = request.headers.get("x-forwarded-for")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"
