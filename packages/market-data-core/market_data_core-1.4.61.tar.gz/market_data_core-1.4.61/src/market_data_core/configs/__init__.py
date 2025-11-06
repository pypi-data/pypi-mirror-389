"""Future-proof configuration system for market data providers.

This module provides a layered, extensible config system that scales from
simple symbol fetching to multi-tenant, multi-provider deployments with:

- Layered configs with includes
- Environment variable resolution (${VAR:-default})
- Profile overlays (dev/staging/prod)
- Discriminated provider unions (IBKR, synthetic, etc.)
- Dataset & job specifications
- Storage routing (DB + lake exports)
- Provider budgets and SLAs

Usage:
    ```python
    from market_data_core.configs import load_config

    # Load with profile override
    cfg = load_config("configs/prices.yaml", profile_override="prod")

    # Access provider config
    ibkr = cfg.providers.root["ibkr_primary"]
    print(ibkr.host, ibkr.port)

    # Access datasets
    dataset = cfg.datasets.root["us_equities_5min"]
    print(dataset.symbols, dataset.interval)
    ```
"""

from .loader import load_config
from .model import (
    AppConfig,
    BackfillSpec,
    CronSchedule,
    Dataset,
    Datasets,
    ExecutionPolicy,
    Features,
    IBKRProvider,
    IntervalSchedule,
    Job,
    Jobs,
    Metrics,
    PacingBudget,
    Provider,
    Providers,
    RetryPolicy,
    S3Storage,
    Schedule,
    StorageConfig,
    StorageTarget,
    SyntheticProvider,
    Telemetry,
    TimescaleStorage,
    Tracing,
)

__all__ = [
    # Loader
    "load_config",
    # Root config
    "AppConfig",
    # Providers
    "Provider",
    "Providers",
    "IBKRProvider",
    "SyntheticProvider",
    "PacingBudget",
    "RetryPolicy",
    # Storage
    "StorageConfig",
    "StorageTarget",
    "TimescaleStorage",
    "S3Storage",
    # Datasets & Jobs
    "Dataset",
    "Datasets",
    "Job",
    "Jobs",
    "Schedule",
    "CronSchedule",
    "IntervalSchedule",
    "BackfillSpec",
    "ExecutionPolicy",
    # Telemetry & Features
    "Telemetry",
    "Metrics",
    "Tracing",
    "Features",
]
