"""
ClairEat Backend — Per-User Sliding Window Rate Limiter
In-memory implementation using a deque per (user_id, endpoint_key).
No Redis required for single-instance deployments.
"""

import asyncio
from collections import defaultdict, deque
from time import monotonic
from typing import DefaultDict, Deque, Tuple

from app.core.exceptions import RateLimitError
from app.core.logging import get_logger

logger = get_logger(__name__)

# (user_id, endpoint_key) → deque of timestamps
_windows: DefaultDict[Tuple[str, str], Deque[float]] = defaultdict(deque)
_lock = asyncio.Lock()


async def check_rate_limit(
    user_id: str,
    endpoint_key: str,
    max_requests: int,
    window_seconds: int,
) -> None:
    """Enforce a sliding-window rate limit for a given user + endpoint.

    Raises ``RateLimitError`` if the caller exceeds ``max_requests`` within
    the rolling ``window_seconds`` window.

    Args:
        user_id:        Authenticated user's UUID.
        endpoint_key:   Logical name for the rate-limited resource
                        (e.g. ``"ai_chat"``, ``"food_search"``).
        max_requests:   Maximum allowed calls in the window.
        window_seconds: Duration of the sliding window in seconds.

    Raises:
        RateLimitError: When the limit is exceeded.
    """
    key: Tuple[str, str] = (user_id, endpoint_key)
    now = monotonic()
    cutoff = now - window_seconds

    async with _lock:
        window = _windows[key]

        # Evict timestamps outside the current window
        while window and window[0] < cutoff:
            window.popleft()

        if len(window) >= max_requests:
            retry_after = int(window[0] - cutoff) + 1
            logger.warning(
                "Rate limit exceeded",
                user_id=user_id,
                endpoint=endpoint_key,
                current=len(window),
                limit=max_requests,
            )
            raise RateLimitError(
                f"Rate limit exceeded for {endpoint_key}. "
                f"Try again in {retry_after}s.",
                retry_after=retry_after,
            )

        window.append(now)
