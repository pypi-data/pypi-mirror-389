"""Integration tests for LNMarkets SDK v3 - tests against real API.

WARNING: These tests make real API calls to testnet4.lnmarkets.com
- They may be rate limited if run too frequently
- Authenticated tests require valid API credentials
- Some tests create and cancel orders on the real exchange

Run with: pytest tests/test_integration_v3.py -v -s
Run authenticated tests: V3_API_KEY=... pytest tests/test_integration_v3.py -v
"""

import asyncio
import os

import pytest
from dotenv import load_dotenv

from lnmarkets_sdk.http.client import APIAuthContext, APIClientConfig, LNMClient
from lnmarkets_sdk.models.account import DepositLightningParams
from lnmarkets_sdk.models.futures_isolated import FuturesOrder

load_dotenv()


# Add delay between tests to avoid rate limiting
@pytest.fixture(autouse=True)
async def rate_limit_delay():
    """Add delay between tests to avoid rate limiting."""
    yield
    await asyncio.sleep(1)  # 1s delay between tests


def create_public_config() -> APIClientConfig:
    """Create config for testnet4."""
    return APIClientConfig(network="testnet4")


def create_auth_config() -> APIClientConfig:
    """Create authenticated config for testnet4."""
    return APIClientConfig(
        network="testnet4",
        authentication=APIAuthContext(
            key=os.environ.get("V3_API_KEY", "test-key"),
            secret=os.environ.get("V3_API_KEY_SECRET", "test-secret"),
            passphrase=os.environ.get("V3_API_KEY_PASSPHRASE", "test-passphrase"),
        ),
    )


class TestBasicsIntegration:
    """Integration tests for basic API endpoints."""

    @pytest.mark.asyncio
    async def test_ping(self):
        """Test ping endpoint against real API."""
        async with LNMClient(create_public_config()) as client:
            result = await client.ping()
            assert "pong" in result

    @pytest.mark.asyncio
    async def test_time(self):
        """Test time endpoint against real API."""
        async with LNMClient(create_public_config()) as client:
            result = await client.request("GET", "/time")
            assert "time" in result
            assert isinstance(result["time"], str)


class TestAccountIntegration:
    """Integration tests for account endpoints (require authentication)."""

    @pytest.mark.skipif(
        not os.environ.get("V3_API_KEY"),
        reason="V3_API_KEY not set in environment",
    )
    @pytest.mark.asyncio
    async def test_get_account(self):
        """Test getting account info from real API."""
        async with LNMClient(create_auth_config()) as client:
            account = await client.account.get_account()
            assert account.balance >= 0
            assert isinstance(account.email, str)
            assert isinstance(account.username, str)
            assert account.fee_tier >= 0
            assert account.id is not None

    @pytest.mark.skipif(
        not os.environ.get("V3_API_KEY"),
        reason="V3_API_KEY not set in environment",
    )
    @pytest.mark.asyncio
    async def test_deposit_lightning(self):
        """Test creating a lightning deposit invoice on real API."""
        async with LNMClient(create_auth_config()) as client:
            params = DepositLightningParams(amount=100_000)
            result = await client.account.deposit_lightning(params)
            assert result.deposit_id is not None
            assert result.payment_request.startswith("ln")


class TestFuturesIntegration:
    """Integration tests for futures endpoints."""

    @pytest.mark.asyncio
    async def test_get_ticker(self):
        """Test getting futures ticker from real API."""
        async with LNMClient(create_public_config()) as client:
            ticker = await client.futures.get_ticker()
            assert ticker.index > 0
            assert ticker.last_price > 0

    @pytest.mark.asyncio
    async def test_get_leaderboard(self):
        """Test getting leaderboard from real API."""
        async with LNMClient(create_public_config()) as client:
            leaderboard = await client.futures.get_leaderboard()
            assert isinstance(leaderboard.daily, list)

    @pytest.mark.asyncio
    async def test_get_candles(self):
        """Test getting candles from real API."""
        from lnmarkets_sdk.models.futures_data import GetCandlesParams

        async with LNMClient(create_public_config()) as client:
            params = GetCandlesParams(
                from_="2023-05-23T09:52:57.863Z", range="1m", limit=1
            )
            candles = await client.futures.get_candles(params)
            assert isinstance(candles, list)
            assert len(candles) > 0
            assert candles[0].open > 0
            assert candles[0].high > 0
            assert candles[0].low > 0
            assert candles[0].close > 0

    @pytest.mark.skipif(
        not os.environ.get("V3_API_KEY"),
        reason="V3_API_KEY not set in environment",
    )
    @pytest.mark.asyncio
    async def test_futures_isolated(self):
        """Test complete futures isolated workflow on real API."""
        async with LNMClient(create_auth_config()) as client:
            # Create a new trade
            params = FuturesOrder(
                type="l",  # limit order
                side="b",  # buy
                price=100_000,
                quantity=1,
                leverage=100,
            )
            trade = await client.futures.isolated.new_trade(params)
            assert trade.id is not None
            assert trade.side == "b"
            assert trade.type == "l"
            assert trade.leverage == 100

            # Get open trades
            open_trades = await client.futures.isolated.get_open_trades()
            assert isinstance(open_trades, list)
            # Our trade should be in the list
            trade_ids = [t.id for t in open_trades]
            assert trade.id in trade_ids

            # Cancel the trade
            from lnmarkets_sdk.models.futures_isolated import CancelTradeParams

            cancel_params = CancelTradeParams(id=trade.id)
            canceled = await client.futures.isolated.cancel(cancel_params)
            assert canceled.id == trade.id
            assert canceled.canceled is True


class TestFuturesCrossIntegration:
    """Integration tests for cross margin futures."""

    @pytest.mark.skipif(
        not os.environ.get("V3_API_KEY"),
        reason="V3_API_KEY not set in environment",
    )
    @pytest.mark.asyncio
    async def test_get_position(self):
        """Test getting cross margin position from real API."""
        async with LNMClient(create_auth_config()) as client:
            position = await client.futures.cross.get_position()
            assert position.margin >= 0
            assert position.leverage > 0

    @pytest.mark.skipif(
        not os.environ.get("V3_API_KEY"),
        reason="V3_API_KEY not set in environment",
    )
    @pytest.mark.asyncio
    async def test_cross_orders(self):
        """Test getting cross margin orders from real API."""
        async with LNMClient(create_auth_config()) as client:
            # Get open orders
            open_orders = await client.futures.cross.get_open_orders()
            assert isinstance(open_orders, list)

            # Get filled orders
            from lnmarkets_sdk.models.futures_cross import GetFilledOrdersParams

            params = GetFilledOrdersParams(limit=5)
            filled_orders = await client.futures.cross.get_filled_orders(params)
            assert isinstance(filled_orders, list)


class TestOracleIntegration:
    """Integration tests for oracle endpoints."""

    @pytest.mark.asyncio
    async def test_get_last_price(self):
        """Test getting last price from real API."""
        async with LNMClient(create_public_config()) as client:
            result = await client.oracle.get_last_price()
            assert result[0].last_price > 0
            assert result[0].time is not None

    @pytest.mark.asyncio
    async def test_get_index(self):
        """Test getting index history from real API."""
        from lnmarkets_sdk.models.oracle import GetIndexParams

        async with LNMClient(create_public_config()) as client:
            params = GetIndexParams(limit=5)
            result = await client.oracle.get_index(params)
            assert isinstance(result, list)
            assert len(result) > 0
            assert result[0].index > 0


class TestSyntheticUSDIntegration:
    """Integration tests for synthetic USD endpoints."""

    @pytest.mark.asyncio
    async def test_get_best_price(self):
        """Test getting best price from real API."""
        async with LNMClient(create_public_config()) as client:
            result = await client.synthetic_usd.get_best_price()
            assert result.ask_price

    @pytest.mark.skipif(
        not os.environ.get("V3_API_KEY"),
        reason="V3_API_KEY not set in environment",
    )
    @pytest.mark.asyncio
    async def test_get_swaps(self):
        """Test getting swaps from real API."""
        from lnmarkets_sdk.models.synthetic_usd import GetSwapsParams

        async with LNMClient(create_auth_config()) as client:
            params = GetSwapsParams(limit=5)
            result = await client.synthetic_usd.get_swaps(params)
            assert isinstance(result, list)
