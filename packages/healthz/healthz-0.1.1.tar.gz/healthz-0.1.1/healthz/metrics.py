"""Metrics calculation and aggregation."""

import time
from collections import Counter
from collections.abc import Iterable


class MetricsCalculator:
    """Calculates metrics from completions (by completed_at) and pending requests."""

    @staticmethod
    def calculate(
        completions: Iterable, pending_requests: dict, total_sent: int, window_seconds: int, timeout_seconds: float
    ) -> dict:
        """
        Calculate comprehensive metrics from completions.

        Args:
            completions: Deque of Completion objects
            pending_requests: Dict of request_id -> sent_time
            total_sent: Total requests sent
            window_seconds: Time window to filter completions by completed_at
            timeout_seconds: Configured timeout for detecting stuck requests

        Returns:
            Dictionary of calculated metrics
        """
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        # Filter completions to only those COMPLETED within the window
        filtered = [c for c in completions if c.completed_at >= cutoff_time]

        # Count stuck requests (pending for > 3x timeout)
        stuck_count = sum(1 for sent_at in pending_requests.values() if current_time - sent_at > timeout_seconds * 3)

        if not filtered:
            return {
                "total_sent": total_sent,
                "total_completed": 0,
                "pending": len(pending_requests),
                "stuck_count": stuck_count,
                "success_count": 0,
                "timeout_count": 0,
                "error_count": 0,
                "status_codes": {},
                "success_rate": 0.0,
                "response_times": [],
                "p50": 0,
                "p95": 0,
                "p99": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
            }

        # Count by status
        success_count = sum(1 for c in filtered if c.status == "success")
        timeout_count = sum(1 for c in filtered if c.status == "timeout")
        error_count = sum(1 for c in filtered if c.status == "error")
        total_completed = len(filtered)

        success_rate = (success_count / total_completed * 100) if total_completed > 0 else 0

        # Status code breakdown (only for non-timeout/error)
        status_codes = Counter(c.status_code for c in filtered if c.status_code is not None)

        # Collect all response times
        response_times = [c.response_time_ms for c in filtered]
        response_times_sorted = sorted(response_times)

        return {
            "total_sent": total_sent,
            "total_completed": total_completed,
            "pending": len(pending_requests),
            "stuck_count": stuck_count,
            "success_count": success_count,
            "timeout_count": timeout_count,
            "error_count": error_count,
            "status_codes": dict(status_codes),  # {200: 50, 503: 10, ...}
            "success_rate": success_rate,
            "response_times": response_times,
            "p50": MetricsCalculator._percentile(response_times_sorted, 50),
            "p95": MetricsCalculator._percentile(response_times_sorted, 95),
            "p99": MetricsCalculator._percentile(response_times_sorted, 99),
            "min": min(response_times) if response_times else 0,
            "max": max(response_times) if response_times else 0,
            "avg": sum(response_times) / len(response_times) if response_times else 0,
        }

    @staticmethod
    def _percentile(data: list[float], p: float) -> float:
        """
        Calculate percentile from sorted data.

        Args:
            data: Sorted list of values
            p: Percentile to calculate (0-100)

        Returns:
            Percentile value
        """
        if not data:
            return 0

        k = (len(data) - 1) * p / 100
        f = int(k)
        c = f + 1

        if c >= len(data):
            return data[-1]

        return data[f] + (k - f) * (data[c] - data[f])

    @staticmethod
    def create_histogram(response_times: list[float], num_buckets: int = 6) -> list[tuple[str, int, float]]:
        """
        Create histogram buckets from response times.

        Args:
            response_times: List of response times in milliseconds
            num_buckets: Number of histogram buckets

        Returns:
            List of (label, count, percentage) tuples
        """
        if not response_times:
            return []

        # Define buckets (in ms)
        buckets = [
            (0, 50, "0-50ms"),
            (50, 100, "50-100ms"),
            (100, 200, "100-200ms"),
            (200, 500, "200-500ms"),
            (500, 1000, "500ms-1s"),
            (1000, float("inf"), ">1s"),
        ]

        # Count per bucket
        bucket_counts = []
        total = len(response_times)

        for min_val, max_val, label in buckets:
            if max_val == float("inf"):
                count = sum(1 for rt in response_times if rt >= min_val)
            else:
                count = sum(1 for rt in response_times if min_val <= rt < max_val)

            percentage = (count / total * 100) if total > 0 else 0
            bucket_counts.append((label, count, percentage))

        return bucket_counts

    @staticmethod
    def get_health_status(pending_count: int, rate: int) -> tuple[str, str]:
        """
        Determine health status based on pending requests.

        Args:
            pending_count: Number of pending requests
            rate: Current request rate

        Returns:
            Tuple of (status_text, color)
        """
        if pending_count < rate:
            return ("✓ Healthy", "green")
        elif pending_count < rate * 3:
            return ("⚠ Degraded", "yellow")
        else:
            return ("✗ Blocked", "red")
