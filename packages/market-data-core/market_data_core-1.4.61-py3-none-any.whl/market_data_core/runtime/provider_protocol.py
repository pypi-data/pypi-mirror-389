"""Provider protocol and data models for the runtime layer.

Defines the contract that all provider adapters must implement, along with
the canonical Bar data model for OHLCV data.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class Bar:
    """Canonical OHLCV bar representation.

    This is the universal data model for price bars across all providers.
    Immutable by design to prevent accidental mutations.

    Attributes:
        provider: Provider name (e.g., "ibkr_primary", "polygon_1")
        symbol: Symbol/ticker (e.g., "SPY", "AAPL")
        interval: Bar interval (e.g., "1min", "5min", "1d")
        ts: Bar timestamp (UTC)
        open: Opening price
        high: High price
        low: Low price
        close: Closing price
        volume: Trading volume

    Example:
        ```python
        bar = Bar(
            provider="ibkr_primary",
            symbol="SPY",
            interval="5min",
            ts=datetime.utcnow(),
            open=450.0,
            high=451.0,
            low=449.5,
            close=450.5,
            volume=1000000.0
        )
        ```
    """

    provider: str
    symbol: str
    interval: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@runtime_checkable
class Provider(Protocol):
    """Protocol for provider adapters.

    All provider implementations must adhere to this protocol.
    The protocol defines the contract for fetching market data in both
    live and backfill modes.

    Attributes:
        name: Provider instance name (matches config key)

    Methods:
        fetch_live: Fetch current/recent data for a dataset
        backfill: Fetch historical data according to backfill spec

    Note:
        Implementations should:
        - Respect provider budgets and pacing
        - Honor retry policies
        - Yield bars incrementally (don't buffer everything)
        - Log errors but don't crash on partial failures
        - Support idempotent replays (same input → same output)

    Example:
        ```python
        class MyAdapter:
            def __init__(self, name: str, cfg: Any):
                self.name = name
                # Initialize connection, etc.

            def fetch_live(self, dataset: Any, job: Any) -> Iterable[Bar]:
                # Fetch latest bars
                yield Bar(...)

            def backfill(self, dataset: Any, job: Any) -> Iterable[Bar]:
                # Fetch historical bars
                yield Bar(...)
        ```
    """

    name: str

    def fetch_live(self, dataset: Any, job: Any) -> Iterable[Bar]:
        """Fetch live/recent data for the given dataset.

        Called by the scheduler on a cadence (e.g., every 5 minutes).
        Should return bars for the most recent window aligned to dataset.interval.

        Args:
            dataset: Dataset configuration (symbols, interval, etc.)
            job: Job configuration (execution policy, schedule, etc.)

        Yields:
            Bar: OHLCV bars for the requested symbols/interval

        Raises:
            ProviderException: On unrecoverable errors
            PacingViolation: If rate limits are exceeded
        """
        ...

    def backfill(self, dataset: Any, job: Any) -> Iterable[Bar]:
        """Fetch historical data according to backfill specification.

        Called once to fill historical gaps. Should respect job.backfill
        parameters (from, to, chunk) and split large requests appropriately.

        Args:
            dataset: Dataset configuration (symbols, interval, etc.)
            job: Job configuration (backfill spec, execution policy, etc.)

        Yields:
            Bar: OHLCV bars for the requested period

        Raises:
            ProviderException: On unrecoverable errors
            PacingViolation: If rate limits are exceeded
        """
        ...
