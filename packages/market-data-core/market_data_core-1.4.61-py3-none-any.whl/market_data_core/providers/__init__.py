"""Provider adapter implementations.

This package contains concrete implementations of the Provider protocol
for various data providers (IBKR, synthetic, etc.).

Available Adapters:
- IBKRAdapter: Interactive Brokers (stub - requires IBKR client integration)
- SyntheticAdapter: Synthetic data generator for testing

Example:
    ```python
    from market_data_core.providers import IBKRAdapter, SyntheticAdapter
    from market_data_core.configs.model import IBKRProvider, SyntheticProvider

    # Direct instantiation (not recommended - use registry instead)
    ibkr_cfg = IBKRProvider(type="ibkr", host="127.0.0.1", port=7497)
    ibkr = IBKRAdapter("ibkr_primary", ibkr_cfg)

    # Better: Use registry
    from market_data_core.runtime import ProviderRegistry
    registry = ProviderRegistry(cfg.providers)
    provider = registry.resolve("ibkr_primary")
    ```
"""

from .ibkr import IBKRAdapter
from .synthetic import SyntheticAdapter

__all__ = [
    "IBKRAdapter",
    "SyntheticAdapter",
]
