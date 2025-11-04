"""Time-series data tracking and visualization."""

import time
from collections import deque
from dataclasses import dataclass
from typing import Optional


@dataclass
class TimeSeriesPoint:
    """A single point in time series."""

    timestamp: float
    value: float


class TimeSeriesTracker:
    """Tracks time-series data for graphing."""

    def __init__(self, max_age_seconds: int = 60):
        """
        Initialize time series tracker.

        Args:
            max_age_seconds: Maximum age of data points to keep
        """
        self.max_age_seconds = max_age_seconds
        self.points = deque()

    def add_point(self, value: float, timestamp: Optional[float] = None):
        """
        Add a new data point.

        Args:
            value: Value to record
            timestamp: Optional timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()

        self.points.append(TimeSeriesPoint(timestamp=timestamp, value=value))
        self._cleanup_old_points()

    def _cleanup_old_points(self):
        """Remove points older than max_age_seconds."""
        cutoff = time.time() - self.max_age_seconds

        while self.points and self.points[0].timestamp < cutoff:
            self.points.popleft()

    def get_points(self, last_n_seconds: Optional[int] = None) -> list[TimeSeriesPoint]:
        """
        Get data points, optionally filtered by time range.

        Args:
            last_n_seconds: Optional limit to last N seconds

        Returns:
            List of TimeSeriesPoint objects
        """
        self._cleanup_old_points()

        if last_n_seconds is None:
            return list(self.points)

        cutoff = time.time() - last_n_seconds
        return [p for p in self.points if p.timestamp >= cutoff]

    def get_values(self, last_n_seconds: Optional[int] = None) -> list[float]:
        """
        Get just the values.

        Args:
            last_n_seconds: Optional limit to last N seconds

        Returns:
            List of values
        """
        points = self.get_points(last_n_seconds)
        return [p.value for p in points]

    def get_latest(self) -> Optional[float]:
        """Get the most recent value."""
        if not self.points:
            return None
        return self.points[-1].value


class ASCIIChart:
    """Creates ASCII art charts from time-series data."""

    @staticmethod
    def create_spark_line(values: list[float], width: int = 40, height: int = 8) -> list[str]:
        """
        Create a simple spark line chart.

        Args:
            values: List of values to plot
            width: Width of chart in characters
            height: Height of chart in lines

        Returns:
            List of strings representing chart lines
        """
        if not values:
            return [" " * width] * height

        # Normalize values to fit in height
        min_val = min(values)
        max_val = max(values)

        if max_val == min_val:
            # All values the same
            normalized = [height // 2] * len(values)
        else:
            normalized = [
                int((v - min_val) / (max_val - min_val) * (height - 1)) for v in values
            ]

        # Resample to fit width
        if len(normalized) > width:
            step = len(normalized) / width
            normalized = [normalized[int(i * step)] for i in range(width)]
        elif len(normalized) < width:
            # Pad with zeros at the start
            normalized = [0] * (width - len(normalized)) + normalized

        # Create chart lines
        lines = []
        for row in range(height - 1, -1, -1):
            line = ""
            for col_val in normalized:
                if col_val >= row:
                    line += "█"
                elif col_val == row - 1:
                    line += "▄"
                else:
                    line += " "
            lines.append(line)

        return lines

    @staticmethod
    def create_line_chart(
        values: list[float],
        width: int = 50,
        height: int = 10,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
    ) -> list[str]:
        """
        Create a line chart with axes.

        Args:
            values: List of values to plot
            width: Width of chart area
            height: Height of chart area
            min_val: Optional minimum value for Y axis
            max_val: Optional maximum value for Y axis

        Returns:
            List of strings representing chart lines
        """
        if not values:
            return [" " * (width + 10)] * (height + 2)

        # Determine value range
        if min_val is None:
            min_val = min(values)
        if max_val is None:
            max_val = max(values)

        # Create the chart
        lines = []

        # Normalize and resample values
        if max_val == min_val:
            normalized = [height // 2] * len(values)
        else:
            normalized = [
                int((v - min_val) / (max_val - min_val) * (height - 1)) for v in values
            ]

        if len(normalized) > width:
            step = len(normalized) / width
            normalized = [normalized[int(i * step)] for i in range(width)]
        elif len(normalized) < width:
            normalized = [0] * (width - len(normalized)) + normalized

        # Draw chart with Y-axis labels
        for row in range(height - 1, -1, -1):
            # Y-axis label
            if max_val == min_val:
                y_val = max_val
            else:
                y_val = min_val + (max_val - min_val) * (row / (height - 1))

            y_label = f"{y_val:>6.1f} ┤"

            # Chart line
            line = ""
            for col_val in normalized:
                if col_val == row:
                    line += "●"
                elif col_val > row:
                    line += "│"
                else:
                    line += " "

            lines.append(y_label + line)

        # X-axis
        lines.append("       └" + "─" * width)

        return lines
