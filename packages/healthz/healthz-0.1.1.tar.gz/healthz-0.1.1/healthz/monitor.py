"""Core monitoring engine for sending requests and tracking results."""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

import aiohttp


@dataclass
class SecondBucket:
    """Aggregated stats for all requests sent in a specific second (for temporal latency graph)."""

    second: int  # Unix timestamp truncated to second
    response_times: list[float] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        return len(self.response_times)


@dataclass
class Completion:
    """A completed request (for current status metrics)."""

    completed_at: float
    status_code: Optional[int]  # None for timeout/error
    response_time_ms: float
    status: str  # 'success', 'timeout', 'error'


class HealthMonitor:
    """Monitors HTTP endpoint with constant-rate requests."""

    def __init__(
        self,
        url: str,
        rate: int,
        window_seconds: int = 10,
        method: str = "GET",
        headers: dict | None = None,
        data: str | None = None,
        timeout: float = 2.0,
    ):
        """
        Initialize the health monitor.

        Args:
            url: Target endpoint URL
            rate: Requests per second to send
            window_seconds: Rolling window size for metrics
            method: HTTP method (GET, POST, etc.)
            headers: Optional HTTP headers
            data: Optional request body data
            timeout: Request timeout in seconds
        """
        self.url = url
        self.rate = rate
        self.window_seconds = window_seconds
        self.method = method.upper()
        self.headers = headers or {}
        self.data = data
        self.timeout_seconds = timeout

        # Metrics
        self.total_sent = 0
        self.buckets = {}  # second -> SecondBucket (by sent_at, for temporal graph)
        self.completions = deque(maxlen=rate * 30)  # Last 30s of completions (by completed_at, for current metrics)
        self.pending_requests = {}  # request_id -> sent_time

        # Control flags
        self.paused = False
        self.should_stop = False

        # Async components
        self.session: Optional[aiohttp.ClientSession] = None
        self._sender_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start the monitoring session."""
        timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
        self.session = aiohttp.ClientSession(timeout=timeout)

        try:
            self._sender_task = asyncio.create_task(self._sender_loop())
            await self._sender_task
        finally:
            await self.session.close()

    async def stop(self):
        """Stop the monitoring session."""
        self.should_stop = True
        if self._sender_task:
            self._sender_task.cancel()
            try:
                await self._sender_task
            except asyncio.CancelledError:
                pass

    def pause(self):
        """Pause sending new requests."""
        self.paused = True

    def resume(self):
        """Resume sending requests."""
        self.paused = False

    def reset_stats(self):
        """Reset all statistics."""
        self.buckets.clear()
        self.completions.clear()
        self.total_sent = 0
        # Don't clear pending_requests as those are in-flight

    def set_rate(self, new_rate: int):
        """Change the request rate."""
        if new_rate < 1:
            new_rate = 1
        if new_rate > 1000:
            new_rate = 1000

        self.rate = new_rate
        # Resize completions deque to keep last 30 seconds at new rate
        self.completions = deque(self.completions, maxlen=new_rate * 30)

    def set_window(self, new_window: int):
        """Change the time window size."""
        if new_window < 1:
            new_window = 1
        if new_window > 300:
            new_window = 300

        self.window_seconds = new_window

    async def _sender_loop(self):
        """Send requests at constant rate."""
        interval = 1.0 / self.rate

        while not self.should_stop:
            if not self.paused:
                request_id = self.total_sent
                self.total_sent += 1

                # Track as pending
                sent_at = time.time()
                self.pending_requests[request_id] = sent_at

                # Send request (don't wait for response)
                asyncio.create_task(self._send_request(request_id, sent_at))

            # Sleep to maintain rate
            await asyncio.sleep(interval)

    async def _send_request(self, request_id: int, sent_at: float):
        """
        Send a single request and update both buckets and completions.

        Args:
            request_id: Unique identifier for this request
            sent_at: Timestamp when request was initiated
        """
        sent_second = int(sent_at)

        # Ensure bucket exists (for temporal graph)
        if sent_second not in self.buckets:
            self.buckets[sent_second] = SecondBucket(second=sent_second)

        bucket = self.buckets[sent_second]

        try:
            # Prepare request kwargs
            kwargs: dict = {"headers": self.headers}
            if self.data:
                kwargs["data"] = self.data

            # Send request
            async with self.session.request(self.method, self.url, **kwargs) as response:  # type: ignore[arg-type]
                completed_at = time.time()
                response_time_ms = (completed_at - sent_at) * 1000

                # Read response body to ensure request completes
                await response.read()

                # Update bucket (by sent_at) for graph
                bucket.response_times.append(response_time_ms)

                # Add completion (by completed_at) for current metrics
                status = "success" if response.status == 200 else "error"
                self.completions.append(
                    Completion(
                        completed_at=completed_at,
                        status_code=response.status,
                        response_time_ms=response_time_ms,
                        status=status,
                    )
                )

                self.pending_requests.pop(request_id, None)

        except asyncio.TimeoutError:
            completed_at = time.time()
            response_time_ms = (completed_at - sent_at) * 1000

            # Update bucket (by sent_at) for graph
            bucket.response_times.append(response_time_ms)

            # Add completion (by completed_at) for current metrics
            self.completions.append(
                Completion(
                    completed_at=completed_at,
                    status_code=None,
                    response_time_ms=response_time_ms,
                    status="timeout",
                )
            )

            self.pending_requests.pop(request_id, None)

        except Exception:
            completed_at = time.time()
            response_time_ms = (completed_at - sent_at) * 1000

            # Update bucket (by sent_at) for graph
            bucket.response_times.append(response_time_ms)

            # Add completion (by completed_at) for current metrics
            self.completions.append(
                Completion(
                    completed_at=completed_at,
                    status_code=None,
                    response_time_ms=response_time_ms,
                    status="error",
                )
            )

            self.pending_requests.pop(request_id, None)

        # Clean up old buckets (keep last 5 minutes)
        cutoff = time.time() - 300
        self.buckets = {s: b for s, b in self.buckets.items() if s >= cutoff}
