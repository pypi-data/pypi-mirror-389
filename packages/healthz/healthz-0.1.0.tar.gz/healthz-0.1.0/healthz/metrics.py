"""Metrics calculation and aggregation."""

import time
from typing import Optional


class MetricsCalculator:
    """Calculates metrics from per-second buckets."""

    @staticmethod
    def calculate(buckets: dict, pending_count: int, total_sent: int, window_seconds: int = 10) -> dict:
        """
        Calculate comprehensive metrics from buckets.

        Args:
            buckets: Dict of second -> SecondBucket
            pending_count: Number of pending requests
            total_sent: Total requests sent
            window_seconds: Time window to filter buckets by second

        Returns:
            Dictionary of calculated metrics
        """
        # Filter buckets to only those within the window
        current_time = time.time()
        cutoff_second = int(current_time) - window_seconds

        filtered_buckets = [b for s, b in buckets.items() if s >= cutoff_second]

        if not filtered_buckets:
            return {
                "total_sent": total_sent,
                "total_completed": 0,
                "pending": pending_count,
                "success_count": 0,
                "timeout_count": 0,
                "error_count": 0,
                "success_rate": 0.0,
                "response_times": [],
                "p50": 0,
                "p95": 0,
                "p99": 0,
                "min": 0,
                "max": 0,
                "avg": 0,
            }

        # Aggregate across all filtered buckets
        success_count = sum(b.success_count for b in filtered_buckets)
        timeout_count = sum(b.timeout_count for b in filtered_buckets)
        error_count = sum(b.error_count for b in filtered_buckets)
        total_completed = sum(b.total_count for b in filtered_buckets)

        success_rate = (success_count / total_completed * 100) if total_completed > 0 else 0

        # Collect all response times
        response_times = []
        for bucket in filtered_buckets:
            response_times.extend(bucket.response_times)
        response_times_sorted = sorted(response_times)

        return {
            "total_sent": total_sent,
            "total_completed": total_completed,
            "pending": pending_count,
            "success_count": success_count,
            "timeout_count": timeout_count,
            "error_count": error_count,
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
