"""Provider registry for lazy adapter instantiation.

The registry resolves provider names from configuration to actual
adapter instances, handling instantiation lazily and caching adapters
for reuse within a session.
"""

from ..configs.model import Providers
from .provider_protocol import Provider


class ProviderRegistry:
    """Registry for resolving provider names to adapter instances.

    The registry:
    - Lazily instantiates adapters on first access
    - Caches adapters for the session lifetime
    - Supports pluggable provider types via discriminated unions
    - Raises clear errors for unknown provider types

    Example:
        ```python
        from market_data_core.configs import load_config
        from market_data_core.runtime import ProviderRegistry

        cfg = load_config("configs/prices.yaml")
        registry = ProviderRegistry(cfg.providers)

        # Lazy instantiation - adapter created on first access
        ibkr = registry.resolve("ibkr_primary")
        synthetic = registry.resolve("synthetic_1")

        # Cached - returns same instance
        ibkr2 = registry.resolve("ibkr_primary")
        assert ibkr is ibkr2
        ```

    Note:
        The registry uses dynamic imports to avoid circular dependencies.
        Provider adapters are imported only when first resolved.
    """

    def __init__(self, prov_cfg: Providers):
        """Initialize registry with provider configurations.

        Args:
            prov_cfg: Providers configuration from AppConfig
        """
        self._cfg = prov_cfg.root
        self._adapters: dict[str, Provider] = {}

    def resolve(self, key: str) -> Provider:
        """Resolve a provider name to an adapter instance.

        Args:
            key: Provider name from configuration (e.g., "ibkr_primary")

        Returns:
            Provider: Adapter instance implementing the Provider protocol

        Raises:
            KeyError: If provider name not found in configuration
            ValueError: If provider type is unknown/unsupported
            ImportError: If provider adapter module cannot be imported

        Example:
            ```python
            provider = registry.resolve("ibkr_primary")
            bars = provider.fetch_live(dataset, job)
            ```
        """
        # Return cached adapter if already instantiated
        if key in self._adapters:
            return self._adapters[key]

        # Check provider exists in config
        if key not in self._cfg:
            raise KeyError(
                f"Provider '{key}' not found in configuration. "
                f"Available providers: {', '.join(self._cfg.keys())}"
            )

        cfg = self._cfg[key]

        # Instantiate adapter based on provider type
        # Dynamic imports to avoid circular dependencies
        if cfg.type == "ibkr":
            from ..providers.ibkr import IBKRAdapter

            self._adapters[key] = IBKRAdapter(key, cfg)
        elif cfg.type == "synthetic":
            from ..providers.synthetic import SyntheticAdapter

            self._adapters[key] = SyntheticAdapter(key, cfg)
        else:
            raise ValueError(
                f"Unknown provider type: {cfg.type}. "
                f"Supported types: ibkr, synthetic. "
                f"Add new provider types by extending the Provider union in configs/model.py"
            )

        return self._adapters[key]

    def get_all(self) -> dict[str, Provider]:
        """Get all configured providers (instantiates any not yet cached).

        Returns:
            Dict[str, Provider]: Map of provider name → adapter instance

        Example:
            ```python
            for name, provider in registry.get_all().items():
                print(f"{name}: {provider.__class__.__name__}")
            ```
        """
        for key in self._cfg.keys():
            self.resolve(key)  # Ensure all are instantiated
        return self._adapters.copy()

    def clear_cache(self) -> None:
        """Clear the adapter cache.

        Useful for testing or when provider configurations change at runtime.
        Next resolve() call will create fresh adapter instances.

        Warning:
            Existing adapter instances will continue to work but may have
            stale configuration. Use with caution.
        """
        self._adapters.clear()
