from __future__ import annotations

import math
import threading
import time

from fastapi import Depends, HTTPException, status

from research_copilot_server.dependencies.auth import get_current_user
from research_copilot_server.models.user import User

_request_windows: dict[tuple[str, int], tuple[float, int, float]] = {}
_request_windows_lock = threading.Lock()
_requests_since_cleanup = 0


def rate_limit(resource: str, limit: int, window_seconds: int):
    async def enforce_rate_limit(current_user: User = Depends(get_current_user)) -> None:
        global _requests_since_cleanup

        now = time.monotonic()
        key = (resource, current_user.id)
        retry_after = 0

        with _request_windows_lock:
            window = _request_windows.get(key)
            if window is None or now >= window[2]:
                _request_windows[key] = (now, 1, now + window_seconds)
            elif window[1] >= limit:
                retry_after = max(1, math.ceil(window[2] - now))
            else:
                _request_windows[key] = (window[0], window[1] + 1, window[2])

            _requests_since_cleanup += 1
            if _requests_since_cleanup >= 256:
                expired_keys = [
                    stored_key
                    for stored_key, stored_window in _request_windows.items()
                    if now >= stored_window[2]
                ]
                for expired_key in expired_keys:
                    del _request_windows[expired_key]
                _requests_since_cleanup = 0

        if retry_after:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
                headers={"Retry-After": str(retry_after)},
            )

    return enforce_rate_limit