# healthz

Interactive HTTP health monitoring tool with real-time metrics visualization and per-second granularity.

Monitor your APIs, detect blocking in async services, and find performance bottlenecks with a beautiful terminal UI inspired by btop.

## Features

- 🚀 **Constant-rate load testing** - Send requests at exact intervals (no batching)
- 📊 **Per-second metrics** - True temporal granularity for p95/p99 latency
- 📈 **Real-time graphs** - Symmetrical butterfly chart showing p99/p95 trends
- ⌨️  **Interactive controls** - Adjust rate and window on-the-fly without restart
- 🎯 **Blocking detection** - Track pending requests and timeouts to detect event loop saturation
- 💾 **Export data** - Save per-second aggregated metrics to CSV
- 🎨 **Nord-themed UI** - Beautiful color scheme optimized for terminals

## Installation

```bash
# Install from PyPI
pip install healthz

# Or install from source
git clone https://github.com/Delos-Intelligence/healthz.git
cd healthz
pip install -e .
```

## Usage

### Basic

```bash
# Monitor a health endpoint at 30 requests/second
healthz http://localhost:8000/healthz --rate 30
```

### Advanced

```bash
# POST request with custom headers
healthz http://api.example.com/endpoint \
  --rate 50 \
  --method POST \
  --header "Authorization: Bearer token" \
  --data '{"check": true}'
```

## Interactive Controls

While the TUI is running:

| Key | Action |
|-----|--------|
| `↑` / `+` | Increase request rate (+10 req/s) |
| `↓` / `-` | Decrease request rate (-10 req/s) |
| `w` | Increase time window (+5s) |
| `s` | Decrease time window (-5s) |
| `p` | Pause/resume sending requests |
| `r` | Reset all statistics |
| `e` | Export per-second metrics to CSV |
| `q` | Quit |

## Display

The TUI shows four panels:

1. **Metrics Panel** (top): Request counts, success rate, pending requests with health status indicator
2. **Response Time Stats** (left): Min, Avg, p50, p95, p99, Max latency with color coding
3. **Distribution Histogram** (right): Response time distribution across buckets
4. **Butterfly Chart** (bottom): Symmetrical p99 (top) / p95 (bottom) time-series graph

### Health Status Colors

- 🟢 **Green** (Healthy): Pending < rate
- 🟡 **Yellow** (Degraded): Pending < rate × 3
- 🔴 **Red** (Blocked): Pending ≥ rate × 3

## Use Cases

### Detect Blocking in Async Services

Monitor `/healthz` while load testing other endpoints to detect when your async event loop gets saturated:

```bash
# Terminal 1: Monitor health check
healthz http://localhost:8000/healthz --rate 30

# Terminal 2: Load your API
while true; do
  curl -X POST http://localhost:8000/api/endpoint \
    -H "Content-Type: application/json" \
    -d '{"data": "test"}'
done
```

If the health check starts showing high pending counts or timeouts, your service is blocking!

### Find Resource Limits

Gradually increase the rate to find when your service starts degrading:

1. Start at low rate: `healthz URL --rate 10`
2. Press `↑` repeatedly to increase rate
3. Watch for pending count to rise or p95/p99 to spike
4. That's your service's limit!

### Compare Before/After

Export baseline metrics, make code changes, run again and compare:

```bash
# Before optimization
healthz http://localhost:8000/healthz --rate 50
# Press 'e' to export to healthz_metrics_YYYYMMDD_HHMMSS.csv

# After optimization
healthz http://localhost:8000/healthz --rate 50
# Press 'e' to export again and compare
```

## Architecture

`healthz` uses a per-second bucket architecture for efficient memory usage:

- Each second gets a `SecondBucket` storing aggregated stats (success/timeout/error counts, response times)
- When a response arrives, it updates the bucket for the second the request was **sent** (not completed)
- All displays (metrics, histogram, graph) read from these buckets
- Individual request objects are never stored - only aggregated data
- Old buckets (>5 minutes) are automatically cleaned up

This means you get accurate per-second granularity while using minimal memory.

## Development

```bash
# Clone and install in development mode
git clone https://github.com/Delos-Intelligence/healthz.git
cd healthz
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black healthz/
ruff check healthz/
```

## Requirements

- Python 3.10+
- aiohttp
- textual
- textual-plotext
- click

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
