"""Command-line interface for healthz."""

import json
import sys
from typing import Optional

import click

from .tui import HealthzApp


@click.command()
@click.argument("url")
@click.option(
    "--rate",
    "-r",
    default=30,
    type=int,
    help="Requests per second to send (default: 30)",
)
@click.option(
    "--window",
    "-w",
    default=10,
    type=int,
    help="Time window for metrics in seconds (default: 10)",
)
@click.option(
    "--method",
    "-m",
    default="GET",
    type=click.Choice(["GET", "POST", "PUT", "DELETE", "PATCH"], case_sensitive=False),
    help="HTTP method (default: GET)",
)
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="HTTP headers (can be specified multiple times)",
)
@click.option(
    "--data",
    "-d",
    default=None,
    help="Request body data (JSON string)",
)
@click.option(
    "--timeout",
    "-t",
    default=2.0,
    type=float,
    help="Request timeout in seconds (default: 2.0)",
)
@click.version_option(version="0.1.0")
def main(
    url: str,
    rate: int,
    window: int,
    method: str,
    header: tuple[str],
    data: Optional[str],
    timeout: float,
):
    """
    Interactive HTTP health monitoring tool.

    Send requests to URL at a constant rate and display real-time metrics.

    Example:

        healthz http://localhost:8000/healthz --rate 30

        healthz http://api.example.com/endpoint \\
            --rate 50 \\
            --method POST \\
            --header "Authorization: Bearer token" \\
            --data '{"check": true}'
    """
    # Validate inputs
    if rate < 1 or rate > 1000:
        click.echo("Error: Rate must be between 1 and 1000", err=True)
        sys.exit(1)

    if window < 1 or window > 300:
        click.echo("Error: Window must be between 1 and 300 seconds", err=True)
        sys.exit(1)

    if timeout < 0.1 or timeout > 60:
        click.echo("Error: Timeout must be between 0.1 and 60 seconds", err=True)
        sys.exit(1)

    # Parse headers
    headers = {}
    for h in header:
        if ":" not in h:
            click.echo(f"Error: Invalid header format '{h}'. Use 'Name: Value'", err=True)
            sys.exit(1)

        key, value = h.split(":", 1)
        headers[key.strip()] = value.strip()

    # Validate JSON data if provided
    if data:
        try:
            json.loads(data)
        except json.JSONDecodeError as e:
            click.echo(f"Error: Invalid JSON data: {e}", err=True)
            sys.exit(1)

    # Display startup info
    click.echo(f"Starting healthz monitor...")
    click.echo(f"  URL: {url}")
    click.echo(f"  Rate: {rate} req/s")
    click.echo(f"  Window: {window}s")
    click.echo(f"  Method: {method}")
    if headers:
        click.echo(f"  Headers: {len(headers)}")
    if data:
        click.echo(f"  Data: {data[:50]}{'...' if len(data) > 50 else ''}")
    click.echo()
    click.echo("Press 'q' to quit, '?' for help")
    click.echo()

    # Run the TUI
    app = HealthzApp(
        url=url,
        rate=rate,
        window=window,
        method=method.upper(),
        headers=headers,
        data=data,
    )

    try:
        app.run()
    except KeyboardInterrupt:
        click.echo("\nStopping monitor...")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
