"""FastAPI server for IBKR provider.

This module provides an HTTP interface to the IBKRProvider for use
in the market-data platform infrastructure.

Endpoints:
- GET  /health - Health check endpoint
- GET  /metrics - Prometheus metrics
- POST /api/v1/stream/quotes - Stream quotes (WebSocket or SSE)
- POST /api/v1/stream/bars - Stream bars
- POST /api/v1/historical/bars - Request historical bars
"""

import asyncio
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncIterable

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from market_data_core import Bar, Instrument, Quote
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel

from .provider import IBKRProvider
from .settings import IBKRSettings
from .metrics import ibkr_ticks_total, ibkr_connection_uptime_seconds

# ============================================================================
# Prometheus Metrics
# ============================================================================

REQUESTS_TOTAL = Counter(
    "ibkr_requests_total",
    "Total requests to IBKR service",
    ["endpoint", "method"],
)

ACTIVE_CONNECTIONS = Gauge(
    "ibkr_active_connections", "Number of active IBKR connections"
)

REQUEST_DURATION = Histogram(
    "ibkr_request_duration_seconds",
    "Request duration in seconds",
    ["endpoint"],
)

QUOTES_STREAMED = Counter("ibkr_quotes_streamed_total", "Total quotes streamed")

BARS_STREAMED = Counter("ibkr_bars_streamed_total", "Total bars streamed")

# ============================================================================
# Request/Response Models
# ============================================================================


class StreamQuotesRequest(BaseModel):
    """Request to stream quotes."""

    symbols: list[str]
    exchange: str = "SMART"
    currency: str = "USD"


class StreamBarsRequest(BaseModel):
    """Request to stream bars."""

    symbols: list[str]
    resolution: str = "5s"
    exchange: str = "SMART"
    currency: str = "USD"


class HistoricalBarsRequest(BaseModel):
    """Request for historical bars."""

    symbol: str
    start: datetime
    end: datetime
    resolution: str = "1d"
    exchange: str = "SMART"
    currency: str = "USD"


class TickEvent(BaseModel):
    """Tick event for pipeline ingestion."""

    symbol: str
    price: float
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    connected: bool


# ============================================================================
# Application Lifecycle
# ============================================================================


provider: IBKRProvider | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global provider

    # Startup: Initialize IBKR provider
    logger.info("Starting IBKR service...")

    # Load settings from environment
    # Handle empty strings by using defaults
    port_str = os.getenv("IBKR_GATEWAY_PORT", "4002").strip()
    port = int(port_str) if port_str else 4002
    
    client_id_str = os.getenv("IBKR_CLIENT_ID", "17").strip()
    client_id = int(client_id_str) if client_id_str else 17
    
    settings = IBKRSettings(
        host=os.getenv("IBKR_HOST", "127.0.0.1") or "127.0.0.1",
        port=port,
        client_id=client_id,
    )

    provider = IBKRProvider(settings)

    # Note: We don't connect immediately - connections are made on-demand
    # to avoid holding open connections when not streaming
    logger.info("✓ IBKR service ready")
    ACTIVE_CONNECTIONS.set(0)

    yield

    # Shutdown: Clean up provider
    logger.info("Shutting down IBKR service...")
    if provider:
        try:
            await provider.close()
        except Exception as e:
            logger.warning(f"Error closing provider: {e}")

    logger.info("✓ IBKR service stopped")


# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="IBKR Market Data Provider",
    description="Interactive Brokers provider for market-data-core",
    version="1.1.5",
    lifespan=lifespan,
)


# ============================================================================
# Health & Metrics Endpoints
# ============================================================================


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint.

    Returns connection status and service health.
    """
    REQUESTS_TOTAL.labels(endpoint="/health", method="GET").inc()

    # Check if provider is connected
    connected = False
    if provider and provider.session.ib:
        connected = provider.session.ib.isConnected()

    return HealthResponse(
        status="healthy" if connected or provider is not None else "starting",
        version="1.1.5",
        connected=connected,
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    REQUESTS_TOTAL.labels(endpoint="/metrics", method="GET").inc()
    
    # Update connection uptime metric if provider is connected
    if provider and provider.session.is_connected():
        provider.session.update_uptime_metric()

    # Generate Prometheus metrics
    metrics_output = generate_latest()
    return StreamingResponse(
        iter([metrics_output]),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# ============================================================================
# Market Data Endpoints
# ============================================================================


@app.post("/api/v1/stream/quotes")
async def stream_quotes(request: StreamQuotesRequest):
    """Stream real-time quotes.

    Returns Server-Sent Events (SSE) stream of quotes.

    Note: This is a simplified implementation. For production, consider
    using WebSockets for better bidirectional communication.
    """
    if not provider:
        raise HTTPException(status_code=503, detail="Provider not initialized")

    REQUESTS_TOTAL.labels(endpoint="/api/v1/stream/quotes", method="POST").inc()

    # Convert symbols to instruments
    instruments = [
        Instrument(symbol=sym, exchange=request.exchange, currency=request.currency)
        for sym in request.symbols
    ]

    async def quote_stream() -> AsyncIterable[str]:
        """Generate SSE stream of quotes."""
        try:
            async with provider:
                ACTIVE_CONNECTIONS.inc()
                logger.info(f"Started quote stream for {request.symbols}")

                async for quote in provider.stream_quotes(instruments):
                    QUOTES_STREAMED.inc()

                    # Format as SSE
                    data = (
                        f"data: {quote.model_dump_json()}\n\n"
                    )
                    yield data

        except asyncio.CancelledError:
            logger.info("Quote stream cancelled")
        except Exception as e:
            logger.error(f"Quote stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"
        finally:
            ACTIVE_CONNECTIONS.dec()

    return StreamingResponse(
        quote_stream(),
        media_type="text/event-stream",
    )


@app.post("/api/v1/stream/bars")
async def stream_bars(request: StreamBarsRequest):
    """Stream real-time bars.

    Returns Server-Sent Events (SSE) stream of bars.
    """
    if not provider:
        raise HTTPException(status_code=503, detail="Provider not initialized")

    REQUESTS_TOTAL.labels(endpoint="/api/v1/stream/bars", method="POST").inc()

    # Convert symbols to instruments
    instruments = [
        Instrument(symbol=sym, exchange=request.exchange, currency=request.currency)
        for sym in request.symbols
    ]

    async def bar_stream() -> AsyncIterable[str]:
        """Generate SSE stream of bars."""
        try:
            async with provider:
                ACTIVE_CONNECTIONS.inc()
                logger.info(
                    f"Started bar stream for {request.symbols} @ {request.resolution}"
                )

                async for bar in provider.stream_bars(request.resolution, instruments):
                    BARS_STREAMED.inc()

                    # Format as SSE
                    data = f"data: {bar.model_dump_json()}\n\n"
                    yield data

        except asyncio.CancelledError:
            logger.info("Bar stream cancelled")
        except Exception as e:
            logger.error(f"Bar stream error: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"
        finally:
            ACTIVE_CONNECTIONS.dec()

    return StreamingResponse(
        bar_stream(),
        media_type="text/event-stream",
    )


@app.post("/api/v1/historical/bars")
async def historical_bars(request: HistoricalBarsRequest):
    """Request historical bars.

    Returns JSON array of bars.
    """
    if not provider:
        raise HTTPException(status_code=503, detail="Provider not initialized")

    REQUESTS_TOTAL.labels(endpoint="/api/v1/historical/bars", method="POST").inc()

    instrument = Instrument(
        symbol=request.symbol,
        exchange=request.exchange,
        currency=request.currency,
    )

    bars: list[Bar] = []

    try:
        async with provider:
            ACTIVE_CONNECTIONS.inc()
            logger.info(
                f"Requesting historical bars: {request.symbol} "
                f"{request.start} -> {request.end} @ {request.resolution}"
            )

            async for bar in provider.request_historical_bars(
                instrument=instrument,
                start=request.start,
                end=request.end,
                resolution=request.resolution,
            ):
                bars.append(bar)
                BARS_STREAMED.inc()

            logger.info(f"Retrieved {len(bars)} bars for {request.symbol}")
            return {"bars": [bar.model_dump() for bar in bars]}

    except Exception as e:
        logger.error(f"Historical bars error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        ACTIVE_CONNECTIONS.dec()


# ============================================================================
# Pipeline Ingestion Endpoint (Phase 2)
# ============================================================================


@app.post("/v1/ingest/ibkr/tick")
async def ingest_tick(event: TickEvent):
    """Ingest tick data from IBKR provider or external sources.
    
    This endpoint accepts tick events and forwards them to the pipeline sink.
    Used for Phase 2 pipeline integration.
    
    Args:
        event: Tick event with symbol, price, and timestamp
        
    Returns:
        Status confirmation
        
    Note:
        Currently logs the event. Future integration will forward to
        market_data_pipeline HTTP sink.
    """
    REQUESTS_TOTAL.labels(endpoint="/v1/ingest/ibkr/tick", method="POST").inc()
    
    try:
        logger.info(
            f"[Ingest] Tick received: {event.symbol} @ {event.price} "
            f"({event.timestamp})"
        )
        
        # Track tick in metrics
        ibkr_ticks_total.labels(symbol=event.symbol).inc()
        
        # TODO: Forward to market_data_pipeline HTTP sink
        # Example:
        # async with httpx.AsyncClient() as client:
        #     await client.post(
        #         "http://pipeline:8080/v1/ingest/tick",
        #         json=event.model_dump()
        #     )
        
        return {
            "status": "ok",
            "symbol": event.symbol,
            "message": "Tick ingested successfully",
        }
        
    except Exception as e:
        logger.exception("Tick ingest failed")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "market_data_ibkr.server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8084")),
        log_level="info",
    )

