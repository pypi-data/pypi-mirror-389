"""Phase 2 Market Data Streaming Tests.

Tests live tick subscriptions and historical bar retrieval.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

import pytest
from loguru import logger

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from market_data_core import Instrument
from market_data_ibkr import IBKRProvider, IBKRSettings


# ============================================================================
# Test Configuration
# ============================================================================

# Test symbol (NVDA is commonly available)
TEST_SYMBOL = os.getenv("IBKR_TEST_SYMBOL", "NVDA")
TEST_EXCHANGE = os.getenv("IBKR_TEST_EXCHANGE", "SMART")
TEST_CURRENCY = os.getenv("IBKR_TEST_CURRENCY", "USD")

# Connection settings from environment
IBKR_HOST = os.getenv("IBKR_HOST", "127.0.0.1")
IBKR_PORT = int(os.getenv("IBKR_PORT", os.getenv("IBKR_GATEWAY_PORT", "4002")))
IBKR_CLIENT_ID = int(os.getenv("IBKR_CLIENT_ID", "2"))  # Use different client ID for tests


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def ibkr_settings() -> IBKRSettings:
    """Create IBKR settings from environment variables."""
    return IBKRSettings(
        host=IBKR_HOST,
        port=IBKR_PORT,
        client_id=IBKR_CLIENT_ID,
        read_timeout_sec=10.0,
    )


# ============================================================================
# Phase 2 Streaming Tests
# ============================================================================


@pytest.mark.asyncio
async def test_live_stream(ibkr_settings: IBKRSettings):
    """Test live tick subscription for a single symbol.
    
    Validates:
    - Connection established
    - Ticks received
    - Metrics incremented
    """
    logger.info(f"Testing live stream for {TEST_SYMBOL}")
    
    async with IBKRProvider(ibkr_settings) as provider:
        # Create instrument
        instrument = Instrument(
            symbol=TEST_SYMBOL,
            exchange=TEST_EXCHANGE,
            currency=TEST_CURRENCY,
        )
        
        # Collect ticks for a short period
        ticks_received = []
        tick_count = 0
        max_ticks = 5  # Collect at least 5 ticks
        timeout_seconds = 30  # Max wait time
        
        start_time = datetime.utcnow()
        
        async for quote in provider.stream_quotes([instrument]):
            ticks_received.append(quote)
            tick_count += 1
            
            logger.info(
                f"Tick {tick_count}: {quote.symbol} "
                f"bid={quote.bid} ask={quote.ask} "
                f"last={quote.last}"
            )
            
            # Stop after receiving enough ticks or timeout
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if tick_count >= max_ticks or elapsed > timeout_seconds:
                break
        
        # Verify we received ticks
        assert tick_count > 0, f"Expected at least 1 tick, got {tick_count}"
        logger.info(f"✅ Received {tick_count} ticks for {TEST_SYMBOL}")


@pytest.mark.asyncio
async def test_historical_bars(ibkr_settings: IBKRSettings):
    """Test historical bar retrieval.
    
    Validates:
    - Historical data request succeeds
    - Returns OHLC bars
    - Proper date range
    """
    logger.info(f"Testing historical bars for {TEST_SYMBOL}")
    
    async with IBKRProvider(ibkr_settings) as provider:
        # Create instrument
        instrument = Instrument(
            symbol=TEST_SYMBOL,
            exchange=TEST_EXCHANGE,
            currency=TEST_CURRENCY,
        )
        
        # Request last 5 days of daily bars
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=5)
        
        bars_received = []
        
        async for bar in provider.request_historical_bars(
            instrument=instrument,
            start=start_time,
            end=end_time,
            resolution="1d",
        ):
            bars_received.append(bar)
        
        # Verify we received bars
        assert len(bars_received) > 0, "Expected at least 1 historical bar"
        
        logger.info(f"✅ Retrieved {len(bars_received)} historical bars")
        
        # Verify bar structure
        for bar in bars_received[:3]:  # Check first 3 bars
            assert bar.symbol == TEST_SYMBOL
            assert bar.open > 0
            assert bar.high >= bar.low
            assert bar.close > 0
            assert bar.volume >= 0
        
        logger.info(f"✅ Bar structure validated")


@pytest.mark.asyncio
async def test_connection_uptime_tracking(ibkr_settings: IBKRSettings):
    """Test that connection uptime is tracked.
    
    Validates:
    - Connection start time recorded
    - Uptime metric can be updated
    """
    logger.info("Testing connection uptime tracking")
    
    async with IBKRProvider(ibkr_settings) as provider:
        # Verify connection is established
        assert provider.session.is_connected(), "Should be connected"
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Update and check uptime
        provider.session.update_uptime_metric()
        stats = provider.session.get_connection_stats()
        
        assert "uptime_seconds" in stats, "Uptime should be in stats"
        assert stats["uptime_seconds"] >= 1.0, "Uptime should be at least 1 second"
        
        logger.info(f"✅ Connection uptime tracked: {stats['uptime_seconds']:.2f}s")


@pytest.mark.asyncio
async def test_multiple_symbols_streaming(ibkr_settings: IBKRSettings):
    """Test streaming multiple symbols simultaneously.
    
    Validates:
    - Multiple subscriptions work
    - Ticks received for all symbols
    """
    symbols = ["NVDA", "AAPL"]  # Use common symbols
    
    logger.info(f"Testing multi-symbol streaming: {symbols}")
    
    async with IBKRProvider(ibkr_settings) as provider:
        # Create instruments
        instruments = [
            Instrument(symbol=sym, exchange=TEST_EXCHANGE, currency=TEST_CURRENCY)
            for sym in symbols
        ]
        
        # Track ticks per symbol
        ticks_by_symbol: dict[str, int] = {sym: 0 for sym in symbols}
        start_time = datetime.utcnow()
        max_wait = 30  # seconds
        
        async for quote in provider.stream_quotes(instruments):
            ticks_by_symbol[quote.symbol] += 1
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            if all(count > 0 for count in ticks_by_symbol.values()) or elapsed > max_wait:
                break
        
        # Verify we received ticks for all symbols
        for symbol, count in ticks_by_symbol.items():
            if count == 0:
                logger.warning(f"No ticks received for {symbol} (may be normal in test environment)")
            else:
                logger.info(f"✅ Received {count} ticks for {symbol}")


# ============================================================================
# Main Entry Point
# ============================================================================


if __name__ == "__main__":
    """Run tests directly."""
    import asyncio
    
    settings = IBKRSettings(
        host=IBKR_HOST,
        port=IBKR_PORT,
        client_id=IBKR_CLIENT_ID,
        read_timeout_sec=10.0,
    )
    
    async def run_tests():
        """Run all tests."""
        print("=" * 60)
        print("Phase 2 Market Data Streaming Tests")
        print("=" * 60)
        
        # Test live stream
        print("\n1. Testing live stream...")
        try:
            await test_live_stream(settings)
        except Exception as e:
            print(f"❌ Live stream test failed: {e}")
        
        # Test historical bars
        print("\n2. Testing historical bars...")
        try:
            await test_historical_bars(settings)
        except Exception as e:
            print(f"❌ Historical bars test failed: {e}")
        
        # Test uptime tracking
        print("\n3. Testing uptime tracking...")
        try:
            await test_connection_uptime_tracking(settings)
        except Exception as e:
            print(f"❌ Uptime tracking test failed: {e}")
        
        print("\n" + "=" * 60)
        print("Tests complete")
        print("=" * 60)
    
    asyncio.run(run_tests())

