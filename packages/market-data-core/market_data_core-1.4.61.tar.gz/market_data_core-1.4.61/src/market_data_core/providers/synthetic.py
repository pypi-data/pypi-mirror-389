"""Synthetic data provider adapter for testing.

This adapter generates random but realistic-looking market data for testing
and development purposes. No external connections or API keys required.

Features:
- Deterministic output (same seed → same data)
- Realistic price movements
- Configurable symbols and intervals
- Works immediately (no setup required)
- Useful for testing pipelines, storage, and orchestration
"""

import random
from collections.abc import Iterable
from datetime import datetime, timedelta

from ..configs.model import Dataset, Job
from ..configs.model import SyntheticProvider as SynthConfig
from ..runtime.provider_protocol import Bar, Provider


class SyntheticAdapter(Provider):
    """Synthetic data generator for testing and development.

    Generates random but realistic OHLCV bars with:
    - Deterministic seeding for reproducible tests
    - Reasonable price movements (±5%)
    - Volume variation
    - Support for multiple symbols and intervals

    Example:
        ```python
        from market_data_core.configs.model import SyntheticProvider
        from market_data_core.providers import SyntheticAdapter

        cfg = SyntheticProvider(type="synthetic", seed=42)
        adapter = SyntheticAdapter("synthetic_1", cfg)

        # Generate bars
        dataset = Dataset(
            provider="synthetic_1",
            symbols=["SPY", "AAPL"],
            interval="5min",
            fields=["open", "high", "low", "close", "volume"]
        )

        for bar in adapter.fetch_live(dataset, job):
            print(f"{bar.symbol} @ {bar.ts}: ${bar.close}")
        ```

    Use Cases:
        - Testing pipeline without IBKR credentials
        - Load testing storage systems
        - Developing orchestration logic
        - Integration tests in CI/CD
        - Demos and examples
    """

    def __init__(self, name: str, cfg: SynthConfig):
        """Initialize synthetic adapter.

        Args:
            name: Provider instance name (from config)
            cfg: Synthetic provider configuration (seed, enabled)
        """
        self.name = name
        self.cfg = cfg

        # Seed random generator for deterministic output
        random.seed(cfg.seed if cfg.seed is not None else 42)

    def _gen_bars(
        self,
        symbol: str,
        interval: str,
        _start: datetime,
        end: datetime,
        count: int = 1,
    ) -> Iterable[Bar]:
        """Generate synthetic OHLCV bars.

        Args:
            symbol: Symbol to generate (e.g., "SPY")
            interval: Bar interval (e.g., "5min", "1d")
            start: Start timestamp
            end: End timestamp
            count: Number of bars to generate

        Yields:
            Bar: Synthetic OHLCV bars
        """
        # Base price varies by symbol (simple hash for determinism)
        base_price = 100.0 + (hash(symbol) % 400)

        # Generate bars
        ts = end
        for _ in range(count):
            # Random price movement (±5%)
            movement = 1.0 + (random.random() - 0.5) * 0.1
            price = base_price * movement

            # OHLC with realistic spread
            spread = price * 0.01  # 1% spread
            open_price = price + (random.random() - 0.5) * spread
            high_price = price + random.random() * spread
            low_price = price - random.random() * spread
            close_price = price + (random.random() - 0.5) * spread

            # Ensure high >= close >= low and high >= open >= low
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)

            # Random volume
            volume = 1_000_000 + random.randint(0, 500_000)

            yield Bar(
                provider=self.name,
                symbol=symbol,
                interval=interval,
                ts=ts,
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                close=round(close_price, 2),
                volume=float(volume),
            )

            # Move timestamp back for next bar
            ts = ts - self._parse_interval(interval)

    def _parse_interval(self, interval: str) -> timedelta:
        """Parse interval string to timedelta.

        Args:
            interval: Interval string (e.g., "1min", "5min", "1d")

        Returns:
            timedelta: Corresponding time duration

        Examples:
            >>> self._parse_interval("1min")
            timedelta(minutes=1)
            >>> self._parse_interval("5min")
            timedelta(minutes=5)
            >>> self._parse_interval("1d")
            timedelta(days=1)
        """
        if interval.endswith("min"):
            minutes = int(interval[:-3])
            return timedelta(minutes=minutes)
        elif interval.endswith("h"):
            hours = int(interval[:-1])
            return timedelta(hours=hours)
        elif interval.endswith("d"):
            days = int(interval[:-1])
            return timedelta(days=days)
        else:
            # Default to 1 minute for unknown intervals
            return timedelta(minutes=1)

    def _resolve_symbols(self, symbols: list[str] | str) -> list[str]:
        """Resolve symbol specification to list of symbols.

        Args:
            symbols: Either a list of symbols or a reference like "@watchlists.name"

        Returns:
            List[str]: List of symbol strings

        Note:
            Reference resolution (e.g., "@watchlists.name") should be handled
            by the caller using the full config. For synthetic testing, we
            just return the list as-is or a default list for references.
        """
        if isinstance(symbols, list):
            return symbols
        elif isinstance(symbols, str) and symbols.startswith("@"):
            # For synthetic, return a default test set when references are used
            # In production, caller should resolve references from config
            return ["SPY", "QQQ", "IWM"]
        else:
            return [symbols] if isinstance(symbols, str) else []

    def backfill(self, dataset: Dataset, job: Job) -> Iterable[Bar]:
        """Generate historical synthetic data.

        Args:
            dataset: Dataset configuration (symbols, interval, etc.)
            job: Job configuration with backfill spec

        Yields:
            Bar: Synthetic OHLCV bars for the backfill period

        Example:
            For a 30-day backfill with 5-minute bars:
            - 30 days * 24 hours * 12 bars/hour = 8,640 bars per symbol
        """
        bf = job.backfill
        assert bf, "Backfill job requires backfill spec"

        # Simple time parsing (extend as needed)
        end = datetime.utcnow().replace(second=0, microsecond=0)

        # Parse "now-30d", "now-3y", etc.
        if bf.from_.startswith("now-"):
            duration_str = bf.from_[4:]  # Remove "now-"
            if duration_str.endswith("d"):
                days = int(duration_str[:-1])
                start = end - timedelta(days=days)
            elif duration_str.endswith("y"):
                years = int(duration_str[:-1])
                start = end - timedelta(days=years * 365)
            elif duration_str.endswith("m"):
                months = int(duration_str[:-1])
                start = end - timedelta(days=months * 30)
            else:
                start = end - timedelta(days=30)  # Default
        else:
            start = end - timedelta(days=30)  # Default

        # Calculate number of bars
        interval_delta = self._parse_interval(dataset.interval)
        total_duration = end - start
        num_bars = int(total_duration / interval_delta)

        # Limit to reasonable number for synthetic data
        num_bars = min(num_bars, 10_000)  # Cap at 10k bars per symbol

        # Generate bars for each symbol
        symbols = self._resolve_symbols(dataset.symbols)
        for symbol in symbols:
            yield from self._gen_bars(
                symbol=symbol,
                interval=dataset.interval,
                _start=start,
                end=end,
                count=num_bars,
            )

    def fetch_live(self, dataset: Dataset, _job: Job) -> Iterable[Bar]:
        """Generate live/recent synthetic data.

        Args:
            dataset: Dataset configuration (symbols, interval, etc.)
            job: Job configuration (execution policy, etc.)

        Yields:
            Bar: Synthetic OHLCV bars for the most recent window

        Example:
            For a 5-minute interval, generates 1 bar at current time for each symbol.
        """
        now = datetime.utcnow().replace(second=0, microsecond=0)
        interval_delta = self._parse_interval(dataset.interval)
        start = now - interval_delta

        symbols = self._resolve_symbols(dataset.symbols)
        for symbol in symbols:
            # Generate 1 bar per symbol for "live" mode
            yield from self._gen_bars(
                symbol=symbol,
                interval=dataset.interval,
                _start=start,
                end=now,
                count=1,
            )
