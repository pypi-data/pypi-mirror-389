"""Core protocols - provider-agnostic interfaces.

These protocols define the contracts that all implementations must follow.
Implementations should be in separate packages (e.g., market_data_ibkr).
"""

from collections.abc import AsyncIterable, Iterable
from datetime import datetime
from typing import Protocol, TypeVar, runtime_checkable

# Forward references for models (avoid circular imports)
Instrument = TypeVar("Instrument")
Quote = TypeVar("Quote")
Bar = TypeVar("Bar")
Trade = TypeVar("Trade")
OptionSnapshot = TypeVar("OptionSnapshot")


@runtime_checkable
class MarketDataProvider(Protocol):
    """Provider interface for market data.

    Implementations:
    - IBKRProvider (market_data_ibkr package)
    - SyntheticProvider (for testing)
    - ReplayProvider (for backtesting)

    All methods return async iterables of Core DTOs (Quote, Bar, etc.).
    """

    async def stream_quotes(
        self,
        instruments: Iterable["Instrument"],
    ) -> AsyncIterable["Quote"]:
        """Stream real-time quotes for given instruments.

        Args:
            instruments: Instruments to subscribe to

        Yields:
            Quote objects with bid/ask/last prices

        Raises:
            PacingViolation: Rate limit exceeded
            PermissionsMissing: No data permissions
            ConnectionFailed: Cannot connect to provider
        """
        ...

    async def stream_bars(
        self,
        resolution: str,
        instruments: Iterable["Instrument"],
    ) -> AsyncIterable["Bar"]:
        """Stream real-time OHLCV bars.

        Args:
            resolution: Bar resolution (e.g., "1s", "1m", "5m", "1h", "1d")
            instruments: Instruments to subscribe to

        Yields:
            Bar objects with OHLCV data

        Raises:
            PacingViolation: Rate limit exceeded
            PermissionsMissing: No data permissions
            ConnectionFailed: Cannot connect to provider
        """
        ...

    async def stream_trades(
        self,
        instruments: Iterable["Instrument"],
    ) -> AsyncIterable["Trade"]:
        """Stream tick-by-tick trades (optional - not all providers support).

        Args:
            instruments: Instruments to subscribe to

        Yields:
            Trade objects with price/size/timestamp

        Raises:
            PacingViolation: Rate limit exceeded
            PermissionsMissing: No data permissions
            ConnectionFailed: Cannot connect to provider
        """
        ...

    async def request_historical_bars(
        self,
        instrument: "Instrument",
        start: datetime,
        end: datetime,
        resolution: str,
    ) -> AsyncIterable["Bar"]:
        """Request historical bars (bounded/finite stream).

        Args:
            instrument: Single instrument
            start: Start datetime (UTC)
            end: End datetime (UTC)
            resolution: Bar resolution (e.g., "1m", "1h", "1d")

        Yields:
            Bar objects in chronological order

        Raises:
            PacingViolation: Historical data rate limit exceeded
            PermissionsMissing: No historical data permissions
            InvalidInstrument: Unknown instrument
        """
        ...

    async def stream_options(
        self,
        instrument: "Instrument",
        expiry: str | None = None,
        strike_range: tuple[float, float] | None = None,
        moneyness_range: float = 0.2,
    ) -> AsyncIterable["OptionSnapshot"]:
        """Stream options chain snapshots.

        Args:
            instrument: Underlying instrument
            expiry: Optional expiry filter (YYYYMMDD format)
            strike_range: Optional (min_strike, max_strike)
            moneyness_range: Filter by moneyness (e.g., 0.2 = ±20% from spot)

        Yields:
            OptionSnapshot objects with pricing and greeks

        Raises:
            PacingViolation: Options data rate limit exceeded
            PermissionsMissing: No options data permissions
        """
        ...


# Generic pipeline protocols
T = TypeVar("T")
U = TypeVar("U")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)
U_co = TypeVar("U_co", covariant=True)


@runtime_checkable
class Source(Protocol[T_co]):
    """Generic data source protocol.

    Sources produce streams of data. Implementations:
    - ProviderSource (wraps MarketDataProvider)
    - ReplaySource (from historical data)
    - SyntheticSource (generates test data)
    """

    async def stream(self) -> AsyncIterable[T_co]:
        """Produce stream of items.

        Yields:
            Items of type T
        """
        ...

    async def close(self) -> None:
        """Close source and clean up resources."""
        ...


@runtime_checkable
class Transform(Protocol[T, U]):  # type: ignore[misc]
    """Generic data transformation protocol.

    Transforms convert items from type T to type U.
    Implementations:
    - DedupeByKey (T -> T, removes duplicates)
    - ResampleBars (Bar -> Bar, resamples to different resolution)
    - Filter (T -> T, filters items)
    - Map (T -> U, transforms items)
    """

    async def process(self, item: T) -> U | None:
        """Process single item.

        Args:
            item: Input item

        Returns:
            Transformed item, or None to drop
        """
        ...


@runtime_checkable
class Sink(Protocol[T]):
    """Generic data sink protocol.

    Sinks consume items and write them somewhere.
    Implementations (in market_data_store):
    - BarsSink (writes bars to Timescale)
    - QuotesSink (writes quotes to Timescale)
    - OptionsSink (writes options to Timescale)
    """

    async def write(self, items: list[T]) -> None:
        """Write batch of items.

        Args:
            items: Batch of items to write

        Raises:
            SinkError: Write failed
        """
        ...

    async def flush(self) -> None:
        """Flush any buffered data."""
        ...

    async def close(self) -> None:
        """Close sink and clean up resources."""
        ...


@runtime_checkable
class PipelineRunner(Protocol):
    """Pipeline orchestration protocol.

    Runners manage the lifecycle of a pipeline (Source -> Transform -> Sink).
    """

    async def start(self) -> None:
        """Start the pipeline."""
        ...

    async def stop(self, drain: bool = True) -> None:
        """Stop the pipeline.

        Args:
            drain: If True, process remaining items before stopping
        """
        ...

    async def run(self, duration_sec: float | None = None) -> None:
        """Run pipeline for specified duration or until stopped.

        Args:
            duration_sec: Run duration in seconds, or None for indefinite
        """
        ...

    def is_running(self) -> bool:
        """Check if pipeline is running."""
        ...


# ============================================================================
# Registry Protocols (NEW for v1.1.0)
# ============================================================================

from collections.abc import Mapping  # noqa: E402


@runtime_checkable
class ProviderRegistry(Protocol):
    """Registry of available market data providers.

    Implementations should track provider specifications (name, capabilities).
    Actual provider instantiation happens in application layer.

    Example:
        ```python
        class MyRegistry:
            def providers(self) -> Iterable[ProviderSpec]:
                return [ProviderSpec(name="ibkr", module="market_data_ibkr", ...)]

            def get(self, name: str) -> ProviderSpec:
                return self._providers[name]
        ```
    """

    def providers(self) -> Iterable:  # Returns ProviderSpec  # type: ignore[misc]
        """List all registered providers."""
        ...

    def get(self, name: str):  # type: ignore[no-untyped-def]
        """Get provider spec by name. Returns ProviderSpec"""
        ...


@runtime_checkable
class SinkRegistry(Protocol):
    """Registry of available data sinks.

    Implementations should track sink specifications (name, kind, capabilities).

    Example:
        ```python
        class MySinkRegistry:
            def sinks(self) -> Iterable[SinkSpec]:
                return [SinkSpec(name="bars_sink", kind="bars", ...)]

            def get(self, name: str) -> SinkSpec:
                return self._sinks[name]
        ```
    """

    def sinks(self) -> Iterable:  # type: ignore[misc]
        """List all registered sinks. Returns SinkSpec"""
        ...

    def get(self, name: str):  # type: ignore[no-untyped-def]
        """Get sink spec by name. Returns SinkSpec"""
        ...


# ============================================================================
# Feedback Protocols (NEW for v1.1.0)
# ============================================================================


@runtime_checkable
class FeedbackPublisher(Protocol):
    """Publisher for backpressure feedback events.

    Store coordinators implement this to emit FeedbackEvent to Pipeline/Provider.

    Example:
        ```python
        class RedisFeedbackBus:
            async def publish(self, event: FeedbackEvent) -> None:
                await self.redis.publish("feedback_channel", event.model_dump_json())
        ```
    """

    async def publish(self, event) -> None:  # type: ignore[no-untyped-def]
        """Publish a feedback event (event: FeedbackEvent)."""
        ...


@runtime_checkable
class RateController(Protocol):
    """Controller for applying rate adjustments to providers.

    Pipeline implements this to apply RateAdjustment commands to providers.

    Example:
        ```python
        class TokenBucketController:
            async def apply(self, adj: RateAdjustment) -> None:
                self.token_bucket.set_rate(adj.scale)
        ```
    """

    async def apply(self, adj) -> None:  # type: ignore[no-untyped-def]
        """Apply a rate adjustment (adj: RateAdjustment)."""
        ...


# ============================================================================
# Federation Protocols (NEW for v1.1.0)
# ============================================================================


@runtime_checkable
class FederationDirectory(Protocol):
    """Static directory of federation topology and endpoints.

    Provides read-only view of cluster topology and service endpoints.
    Sufficient for MVP federation without dynamic discovery.

    Example:
        ```python
        class StaticDirectory:
            def topology(self) -> ClusterTopology:
                return ClusterTopology(...)

            def endpoints(self) -> Mapping[str, str]:
                return {"orchestrator": "http://orchestrator:8080"}
        ```
    """

    def topology(self):  # type: ignore[no-untyped-def]
        """Get current cluster topology. Returns ClusterTopology"""
        ...

    def endpoints(self) -> Mapping[str, str]:
        """Get service endpoints (logical name → URL)."""
        ...


__all__ = [
    "MarketDataProvider",
    "Source",
    "Transform",
    "Sink",
    "PipelineRunner",
    # NEW for v1.1.0
    "ProviderRegistry",
    "SinkRegistry",
    "FeedbackPublisher",
    "RateController",
    "FederationDirectory",
]
