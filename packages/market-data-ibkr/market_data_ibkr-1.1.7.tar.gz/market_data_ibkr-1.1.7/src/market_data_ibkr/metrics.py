"""Prometheus metrics for IBKR provider.

Phase 2 metrics for tracking:
- Tick counts per symbol
- Connection uptime
"""

from prometheus_client import Counter, Gauge

# Phase 2 Metrics
ibkr_ticks_total = Counter(
    "ibkr_ticks_total",
    "Total ticks received from IBKR",
    ["symbol"],
)

ibkr_connection_uptime_seconds = Gauge(
    "ibkr_connection_uptime_seconds",
    "IBKR connection uptime in seconds",
)


