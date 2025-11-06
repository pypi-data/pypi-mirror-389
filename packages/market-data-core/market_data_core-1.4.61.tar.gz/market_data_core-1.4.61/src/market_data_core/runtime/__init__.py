"""Runtime layer for pluggable providers.

This module provides the protocol and registry for provider adapters,
enabling clean separation between configuration and execution.

The runtime layer allows:
- Provider plugins via Protocol-based contracts
- Lazy adapter instantiation
- Type-safe data models (Bar)
- Clean registry pattern

Example:
    ```python
    from market_data_core.runtime import ProviderRegistry, Bar
    from market_data_core.configs import load_config

    cfg = load_config("configs/prices.yaml")
    registry = ProviderRegistry(cfg.providers)
    
    provider = registry.resolve("ibkr_primary")
    for bar in provider.fetch_live(dataset, job):
        print(f"{bar.symbol} @ {bar.ts}: ${bar.close}")
    ```
"""

from .provider_protocol import Bar, Provider
from .registry import ProviderRegistry

__all__ = [
    "Bar",
    "Provider",
    "ProviderRegistry",
]
