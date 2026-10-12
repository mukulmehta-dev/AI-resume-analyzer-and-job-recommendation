import time
from collections import defaultdict
from typing import Optional
from fastapi import HTTPException, status, Request
from backend.app.core.config import settings

requests_tracker = defaultdict(list)


def get_client_ip(request: Request) -> str:
    if settings.TRUSTED_PROXY:
        real_ip = request.headers.get("X-Real-IP")
        if real_ip and real_ip.strip():
            return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


def purge_empty_keys(now: Optional[float] = None, max_window: int = 3600) -> None:
    current_time = now or time.time()
    stale_keys = [
        k for k, timestamps in list(requests_tracker.items())
        if not timestamps or (current_time - max(timestamps) >= max_window)
    ]
    for k in stale_keys:
        requests_tracker.pop(k, None)


def record_and_check_limit(key: str, max_requests: int, window_seconds: int) -> None:
    now = time.time()
    valid_timestamps = [t for t in requests_tracker.get(key, []) if now - t < window_seconds]
    if len(valid_timestamps) >= max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please try again later."
        )
    valid_timestamps.append(now)
    requests_tracker[key] = valid_timestamps
    if len(requests_tracker) > 200:
        purge_empty_keys(now=now, max_window=3600)


def check_rate_limit(key_prefix: str, max_requests: int = 20, window_seconds: int = 60):
    def dependency(request: Request):
        client_ip = get_client_ip(request)
        key = f"{key_prefix}:{client_ip}"
        record_and_check_limit(key, max_requests, window_seconds)

    return dependency
