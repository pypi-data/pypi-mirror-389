"""Interactive TUI using Textual - Nord themed design."""

import asyncio
import csv
import time
from datetime import datetime

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Footer, Header, Static
from textual_plotext import PlotextPlot
from rich.text import Text

from .metrics import MetricsCalculator
from .monitor import HealthMonitor

# Nord color palette
NORD_COLORS = {
    "frost_blue": "#88C0D0",      # Cyan blue
    "frost_teal": "#8FBCBB",      # Teal
    "frost_light": "#81A1C1",     # Light blue
    "frost_dark": "#5E81AC",      # Dark blue
    "aurora_red": "#BF616A",      # Red
    "aurora_orange": "#D08770",   # Orange
    "aurora_yellow": "#EBCB8B",   # Yellow
    "aurora_green": "#A3BE8C",    # Green
    "aurora_purple": "#B48EAD",   # Purple
    "snow_light": "#ECEFF4",      # Light text
    "snow_mid": "#E5E9F0",        # Mid text
    "snow_dark": "#D8DEE9",       # Dark text
}


def get_nord_color(percentage: float, inverse: bool = False) -> str:
    """
    Get Nord color based on percentage.

    Args:
        percentage: Value from 0-100
        inverse: If True, higher percentage = better (for success rate)
                 If False, higher percentage = worse (for latency)
    """
    if inverse:
        # For success rate: higher is better (green → yellow → orange → red)
        if percentage >= 95:
            return NORD_COLORS["aurora_green"]
        elif percentage >= 80:
            return NORD_COLORS["aurora_yellow"]
        elif percentage >= 60:
            return NORD_COLORS["aurora_orange"]
        else:
            return NORD_COLORS["aurora_red"]
    else:
        # For latency/errors: lower is better (green → yellow → orange → red)
        if percentage <= 30:
            return NORD_COLORS["aurora_green"]
        elif percentage <= 60:
            return NORD_COLORS["aurora_yellow"]
        elif percentage <= 80:
            return NORD_COLORS["aurora_orange"]
        else:
            return NORD_COLORS["aurora_red"]


def create_horizontal_bar(value: float, max_value: float, width: int = 40, inverse: bool = False) -> Text:
    """Create a horizontal bar with Nord color gradient.

    Args:
        value: Current value
        max_value: Maximum value for scaling
        width: Bar width in characters
        inverse: If True, higher values are better (e.g., success rate)
    """
    if max_value == 0:
        percentage = 0
    else:
        percentage = min(100, (value / max_value) * 100)

    filled = int((percentage / 100) * width)
    empty = width - filled

    color = get_nord_color(percentage, inverse=inverse)

    bar = Text()
    bar.append("█" * filled, style=color)
    bar.append("░" * empty, style="dim")

    return bar


class CompactMetricsDisplay(Static):
    """Compact metrics display - btop style."""

    def update_metrics(self, metrics: dict, rate: int, window: int, paused: bool, url: str):
        """Update the displayed metrics."""
        # Status indicator with Nord colors
        status_text, status_color = MetricsCalculator.get_health_status(metrics["pending"], rate)

        if status_color == "green":
            status_dot = "●"
            status_style = NORD_COLORS["aurora_green"]
        elif status_color == "yellow":
            status_dot = "●"
            status_style = NORD_COLORS["aurora_yellow"]
        else:
            status_dot = "●"
            status_style = NORD_COLORS["aurora_red"]

        pause_indicator = "[dim]❙❙ PAUSED[/dim]" if paused else ""

        # Build compact display with Nord colors
        text = Text()
        text.append(f"{status_dot} ", style=status_style)
        text.append(f"{url}", style=f"bold {NORD_COLORS['frost_blue']}")
        text.append(f"  |  ", style="dim")
        text.append(f"{rate} req/s", style="bold")
        text.append(f"  |  ", style="dim")
        text.append(f"Window: {window}s", style="dim")

        if paused:
            text.append(f"  |  {pause_indicator}")

        text.append("\n\n")

        # Requests overview with Nord colors
        text.append("Requests  ", style=f"bold {NORD_COLORS['frost_blue']}")
        text.append(f"Sent: ", style="dim")
        text.append(f"{metrics['total_sent']:,}", style="bold")
        text.append(f"  |  ", style="dim")
        text.append(f"Done: ", style="dim")
        text.append(f"{metrics['total_completed']:,}", style="bold")
        text.append(f"  |  ", style="dim")
        text.append(f"Pending: ", style="dim")

        if metrics['pending'] < rate:
            pending_color = NORD_COLORS["aurora_green"]
        elif metrics['pending'] < rate * 3:
            pending_color = NORD_COLORS["aurora_yellow"]
        else:
            pending_color = NORD_COLORS["aurora_red"]
        text.append(f"{metrics['pending']}", style=f"bold {pending_color}")

        text.append("\n\n")

        # Success rate bar (inverse=True because higher is better)
        success_percentage = metrics['success_rate']
        bar = create_horizontal_bar(success_percentage, 100, width=50, inverse=True)

        text.append("Success   ", style=f"bold {NORD_COLORS['aurora_green']}")
        text.append(bar)
        text.append(f"  {success_percentage:.1f}%", style="bold")
        text.append(f" ({metrics['success_count']}/{metrics['total_completed']})", style="dim")

        text.append("\n")

        # Errors and timeouts with Nord colors
        if metrics['error_count'] > 0:
            text.append("Errors    ", style=f"bold {NORD_COLORS['aurora_red']}")
            error_bar = create_horizontal_bar(metrics['error_count'], metrics['total_completed'], width=50)
            text.append(error_bar)
            text.append(f"  {metrics['error_count']}", style=f"bold {NORD_COLORS['aurora_red']}")
            text.append("\n")

        if metrics['timeout_count'] > 0:
            text.append("Timeouts  ", style=f"bold {NORD_COLORS['aurora_yellow']}")
            timeout_bar = create_horizontal_bar(metrics['timeout_count'], metrics['total_completed'], width=50)
            text.append(timeout_bar)
            text.append(f"  {metrics['timeout_count']}", style=f"bold {NORD_COLORS['aurora_yellow']}")

        self.update(text)


class LatencyStatsDisplay(Static):
    """Compact latency statistics."""

    def update_latency(self, metrics: dict, window: int):
        """Update latency stats with Nord color coding."""
        text = Text()
        text.append("Response Time ", style=f"bold {NORD_COLORS['frost_blue']}")
        text.append(f"(last {window}s)", style="dim")
        text.append("\n\n")

        # Define thresholds for coloring (ms) with Nord colors
        def get_latency_color(ms: float) -> str:
            if ms < 100:
                return NORD_COLORS["aurora_green"]
            elif ms < 300:
                return NORD_COLORS["aurora_yellow"]
            elif ms < 500:
                return NORD_COLORS["aurora_orange"]
            else:
                return NORD_COLORS["aurora_red"]

        stats = [
            ("Min", metrics['min']),
            ("Avg", metrics['avg']),
            ("p50", metrics['p50']),
            ("p95", metrics['p95']),
            ("p99", metrics['p99']),
            ("Max", metrics['max']),
        ]

        for label, value in stats:
            color = get_latency_color(value)
            text.append(f"{label:<4} ", style="dim")
            text.append(f"{value:>7.1f}ms", style=color)
            text.append("\n")

        self.update(text)


class HistogramDisplay(Static):
    """Response time histogram with proper gradient colors."""

    def update_histogram(self, response_times: list[float], window: int):
        """Update histogram with Nord color gradient."""
        if not response_times:
            self.update(f"[bold {NORD_COLORS['frost_blue']}]Distribution[/]\n\n[dim]No data yet...[/dim]")
            return

        histogram = MetricsCalculator.create_histogram(response_times)

        text = Text()
        text.append("Distribution ", style=f"bold {NORD_COLORS['frost_blue']}")
        text.append(f"(last {window}s)", style="dim")
        text.append("\n\n")

        for label, count, percentage in histogram:
            # Determine Nord color based on the latency range
            if "0-50" in label:
                bar_color = NORD_COLORS["aurora_green"]  # Very fast
            elif "50-100" in label:
                bar_color = NORD_COLORS["aurora_green"]  # Fast
            elif "100-200" in label:
                bar_color = NORD_COLORS["aurora_yellow"]  # Moderate
            elif "200-500" in label:
                bar_color = NORD_COLORS["aurora_orange"]  # Slow
            elif "500" in label and "1s" in label:
                bar_color = NORD_COLORS["aurora_red"]  # Very slow
            else:  # >1s
                bar_color = NORD_COLORS["aurora_red"]  # Extremely slow

            # Create bar scaled to 100%
            bar_length = int((percentage / 100) * 40)
            bar = Text()
            bar.append("█" * bar_length, style=bar_color)
            bar.append("░" * (40 - bar_length), style="dim")

            text.append(f"{label:<12} ", style="dim")
            text.append(bar)
            text.append(f"  {percentage:>5.1f}%", style="bold")
            text.append(f" ({count})", style="dim")
            text.append("\n")

        self.update(text)


class PlotextChart(PlotextPlot):
    """High-resolution chart using textual-plotext widget."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.max_seen = 100  # Track max value for fixed scale

    def on_mount(self) -> None:
        """Initialize the plot."""
        self.plt.theme("dark")
        self.plt.title("p99 (top) / p95 (bottom)")

    def update_chart(self, metrics: dict, window: int, buckets: dict):
        """Update the plotext chart with per-second bucket metrics."""
        try:
            # Get the plot width (based on terminal size)
            plot_width = self.plt.plot_size()[0]
            seconds_to_show = max(window, plot_width)

            # Build display values from buckets
            current_time = time.time()
            current_second = int(current_time)
            p99_values = []
            p95_values = []

            for i in range(seconds_to_show):
                second = current_second - seconds_to_show + i + 1
                if second in buckets and len(buckets[second].response_times) > 0:
                    times = sorted(buckets[second].response_times)
                    p99 = MetricsCalculator._percentile(times, 99)
                    p95 = MetricsCalculator._percentile(times, 95)
                    p99_values.append(p99)
                    p95_values.append(p95)
                else:
                    # No data for this second yet
                    p99_values.append(0)
                    p95_values.append(0)

            if not p99_values or not p95_values:
                return

            # Update max seen for fixed scale (only from non-zero values)
            non_zero_p99 = [v for v in p99_values if v > 0]
            if non_zero_p99:
                self.max_seen = max(self.max_seen, max(non_zero_p99))

            # Mirror p95 to negative values for symmetrical display
            p95_mirrored = [-v for v in p95_values]

            # Clear and redraw
            self.plt.clear_data()
            self.plt.clear_figure()

            # X-axis: negative time values ending at 0 (now)
            x_values = list(range(-len(p99_values) + 1, 1))

            # Create filled areas that meet at y=0
            # Plot p95 first (bottom, filled from y=0 down)
            self.plt.plot(x_values, p95_mirrored, marker="braille", fillx=True, color="cyan+")
            # Plot p99 second (top, filled from y=0 up)
            self.plt.plot(x_values, p99_values, marker="braille", fillx=True, color="green+")

            self.plt.title(f"p99 (top) / p95 (bottom)")
            # Symmetrical Y-axis
            max_y = self.max_seen * 1.1
            self.plt.ylim(-max_y, max_y)
            self.plt.xlim(-len(p99_values), 0)

            # Y-axis ticks: multiples of 100ms
            y_ticks = list(range(-int(max_y), int(max_y) + 1, 100))
            self.plt.yticks(y_ticks)

            # X-axis ticks: only multiples of 30
            x_ticks = list(range(0, -len(p99_values) - 1, -30))
            self.plt.xticks(x_ticks)
            self.plt.xlabel("seconds ago")
            self.plt.ylabel("latency (ms)")
            self.plt.theme("dark")

            self.refresh()
        except Exception:
            # Silently fail - don't crash the app
            pass


class HealthzApp(App):
    """Textual app for health monitoring - btop inspired."""

    CSS = """
    Screen {
        layout: vertical;
    }

    #metrics {
        border: round #88C0D0;
        padding: 1;
        height: auto;
    }

    #stats-row {
        height: auto;
    }

    #latency {
        border: round #A3BE8C;
        padding: 1;
        width: 1fr;
    }

    #histogram {
        border: round #B48EAD;
        padding: 1;
        width: 2fr;
    }

    #chart {
        border: round #EBCB8B;
        padding: 1;
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("p", "pause", "Pause/Resume"),
        ("r", "reset", "Reset"),
        ("e", "export", "Export"),
        ("up,plus", "increase_rate", "+10 req/s"),
        ("down,minus", "decrease_rate", "-10 req/s"),
        ("w", "increase_window", "+5s window"),
        ("s", "decrease_window", "-5s window"),
    ]

    def __init__(
        self,
        url: str,
        rate: int,
        window: int,
        method: str,
        headers: dict,
        data: str,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.url = url
        self.monitor = HealthMonitor(
            url=url,
            rate=rate,
            window_seconds=window,
            method=method,
            headers=headers,
            data=data,
        )
        self.update_task = None

    def compose(self) -> ComposeResult:
        """Create child widgets with horizontal stats row."""
        yield Header(show_clock=True)
        yield CompactMetricsDisplay(id="metrics")
        with Horizontal(id="stats-row"):
            yield LatencyStatsDisplay(id="latency")
            yield HistogramDisplay(id="histogram")
        yield PlotextChart(id="chart")
        yield Footer()

    async def on_mount(self) -> None:
        """Start monitoring when app mounts."""
        self.title = "healthz monitor"
        self.sub_title = self.url

        # Start the monitor
        asyncio.create_task(self.monitor.start())

        # Start the update loop
        self.update_task = asyncio.create_task(self._update_loop())

    async def _update_loop(self):
        """Periodically update the display with error handling."""
        while True:
            try:
                await asyncio.sleep(0.25)

                metrics = MetricsCalculator.calculate(
                    self.monitor.buckets,
                    len(self.monitor.pending_requests),
                    self.monitor.total_sent,
                    self.monitor.window_seconds,
                )

                # Update all widgets with error handling for each
                try:
                    self.query_one("#metrics", CompactMetricsDisplay).update_metrics(
                        metrics,
                        self.monitor.rate,
                        self.monitor.window_seconds,
                        self.monitor.paused,
                        self.url,
                    )
                except Exception as e:
                    self.notify(f"Metrics update error: {e}", severity="error")

                try:
                    self.query_one("#latency", LatencyStatsDisplay).update_latency(
                        metrics, self.monitor.window_seconds
                    )
                except Exception as e:
                    self.notify(f"Latency update error: {e}", severity="error")

                try:
                    self.query_one("#histogram", HistogramDisplay).update_histogram(
                        metrics["response_times"], self.monitor.window_seconds
                    )
                except Exception as e:
                    self.notify(f"Histogram update error: {e}", severity="error")

                try:
                    self.query_one("#chart", PlotextChart).update_chart(
                        metrics, self.monitor.window_seconds, self.monitor.buckets
                    )
                except Exception as e:
                    self.notify(f"Chart update error: {e}", severity="error")

            except Exception as e:
                self.notify(f"Update loop error: {e}", severity="error")
                await asyncio.sleep(1)  # Back off on error

    def action_pause(self):
        """Pause/resume monitoring."""
        if self.monitor.paused:
            self.monitor.resume()
        else:
            self.monitor.pause()

    def action_reset(self):
        """Reset statistics."""
        self.monitor.reset_stats()
        self.notify("Statistics reset", severity="information")

    def action_export(self):
        """Export per-second aggregated metrics to CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"healthz_metrics_{timestamp}.csv"

        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["second", "success_count", "timeout_count", "error_count", "p50", "p95", "p99", "avg"])

            for second in sorted(self.monitor.buckets.keys()):
                bucket = self.monitor.buckets[second]
                if len(bucket.response_times) > 0:
                    times = sorted(bucket.response_times)
                    p50 = MetricsCalculator._percentile(times, 50)
                    p95 = MetricsCalculator._percentile(times, 95)
                    p99 = MetricsCalculator._percentile(times, 99)
                    avg = sum(times) / len(times)
                else:
                    p50 = p95 = p99 = avg = 0

                writer.writerow([
                    second,
                    bucket.success_count,
                    bucket.timeout_count,
                    bucket.error_count,
                    f"{p50:.2f}",
                    f"{p95:.2f}",
                    f"{p99:.2f}",
                    f"{avg:.2f}",
                ])

        self.notify(f"Exported to {filename}", severity="information")

    def action_increase_rate(self):
        """Increase request rate."""
        self.monitor.set_rate(self.monitor.rate + 10)
        self.notify(f"Rate: {self.monitor.rate} req/s", severity="information")

    def action_decrease_rate(self):
        """Decrease request rate."""
        self.monitor.set_rate(self.monitor.rate - 10)
        self.notify(f"Rate: {self.monitor.rate} req/s", severity="information")

    def action_increase_window(self):
        """Increase time window."""
        self.monitor.set_window(self.monitor.window_seconds + 5)
        self.notify(f"Window: {self.monitor.window_seconds}s", severity="information")

    def action_decrease_window(self):
        """Decrease time window."""
        self.monitor.set_window(self.monitor.window_seconds - 5)
        self.notify(f"Window: {self.monitor.window_seconds}s", severity="information")

    async def action_quit(self):
        """Quit the app."""
        await self.monitor.stop()
        self.exit()
