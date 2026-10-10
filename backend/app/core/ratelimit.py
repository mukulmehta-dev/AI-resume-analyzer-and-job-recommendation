import time
from collections import defaultdict
from fastapi import HTTPException, status, Request
from backend.app.core.config import settings

requests_tracker = defaultdict(list)


def get_client_ip(request: Request) -> str:
    if settings.TRUSTED_PROXY:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def check_rate_limit(key_prefix: str, max_requests: int = 20, window_seconds: int = 60):
    def dependency(request: Request):
        client_ip = get_client_ip(request)
        key = f"{key_prefix}:{client_ip}"
        now = time.time()
        timestamps = requests_tracker[key]
        valid_timestamps = [t for t in timestamps if now - t < window_seconds]
        if len(valid_timestamps) >= max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
        valid_timestamps.append(now)
        requests_tracker[key] = valid_timestamps

    return dependency
