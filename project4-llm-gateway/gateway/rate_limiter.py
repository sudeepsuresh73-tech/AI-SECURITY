"""
rate_limiter.py
---------------
Per-user rate limiting for the LLM Gateway.
Tracks request counts per user within a time window.
"""

from datetime import datetime, timedelta
from collections import defaultdict

# Default limits
MAX_REQUESTS_PER_MINUTE = 10
MAX_REQUESTS_PER_HOUR = 50
BLOCK_DURATION_MINUTES = 5


class RateLimiter:
    def __init__(
        self,
        max_per_minute: int = MAX_REQUESTS_PER_MINUTE,
        max_per_hour: int = MAX_REQUESTS_PER_HOUR,
        block_duration_minutes: int = BLOCK_DURATION_MINUTES
    ):
        self.max_per_minute = max_per_minute
        self.max_per_hour = max_per_hour
        self.block_duration = timedelta(minutes=block_duration_minutes)

        # user_id -> list of request timestamps
        self.request_log: dict[str, list[datetime]] = defaultdict(list)
        # user_id -> block expiry time
        self.blocked_until: dict[str, datetime] = {}

    def _clean_old_requests(self, user_id: str):
        """Remove requests older than 1 hour from the log."""
        cutoff = datetime.now() - timedelta(hours=1)
        self.request_log[user_id] = [
            t for t in self.request_log[user_id] if t > cutoff
        ]

    def check(self, user_id: str) -> dict:
        """
        Check if a user is allowed to make a request.
        Returns allow/block decision with reason.
        """
        now = datetime.now()

        # Check if currently blocked
        if user_id in self.blocked_until:
            if now < self.blocked_until[user_id]:
                remaining = (self.blocked_until[user_id] - now).seconds
                return {
                    "allowed": False,
                    "reason": f"User blocked for rate limit violation. Unblocks in {remaining}s.",
                    "requests_last_minute": None,
                    "requests_last_hour": None
                }
            else:
                del self.blocked_until[user_id]

        self._clean_old_requests(user_id)

        one_minute_ago = now - timedelta(minutes=1)
        requests_last_minute = sum(
            1 for t in self.request_log[user_id] if t > one_minute_ago
        )
        requests_last_hour = len(self.request_log[user_id])

        if requests_last_minute >= self.max_per_minute:
            self.blocked_until[user_id] = now + self.block_duration
            return {
                "allowed": False,
                "reason": f"Rate limit exceeded: {requests_last_minute} requests in last minute (max {self.max_per_minute}). Blocked for {self.block_duration.seconds // 60} minutes.",
                "requests_last_minute": requests_last_minute,
                "requests_last_hour": requests_last_hour
            }

        if requests_last_hour >= self.max_per_hour:
            self.blocked_until[user_id] = now + self.block_duration
            return {
                "allowed": False,
                "reason": f"Rate limit exceeded: {requests_last_hour} requests in last hour (max {self.max_per_hour}). Blocked for {self.block_duration.seconds // 60} minutes.",
                "requests_last_minute": requests_last_minute,
                "requests_last_hour": requests_last_hour
            }

        return {
            "allowed": True,
            "reason": None,
            "requests_last_minute": requests_last_minute,
            "requests_last_hour": requests_last_hour
        }

    def record(self, user_id: str):
        """Record a successful request for a user."""
        self.request_log[user_id].append(datetime.now())

    def get_user_stats(self, user_id: str) -> dict:
        """Get current stats for a user."""
        self._clean_old_requests(user_id)
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        return {
            "user_id": user_id,
            "requests_last_minute": sum(1 for t in self.request_log[user_id] if t > one_minute_ago),
            "requests_last_hour": len(self.request_log[user_id]),
            "is_blocked": user_id in self.blocked_until and now < self.blocked_until.get(user_id, now),
            "blocked_until": self.blocked_until.get(user_id, None)
        }

    def get_all_users(self) -> list[dict]:
        """Get stats for all tracked users."""
        all_users = set(list(self.request_log.keys()) + list(self.blocked_until.keys()))
        return [self.get_user_stats(uid) for uid in all_users]
