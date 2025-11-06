"""market_data_core - Core contracts for market data system.

This package provides provider-agnostic protocols, models, errors, and settings
that all market data implementations should use.

Core is the foundation - it has NO dependencies on other packages.
Other packages (pipeline, store, ibkr) depend on Core.

Version 1.0.0 - Contracts-only refactor
"""

# ============================================================================
# Protocols (interfaces)
# ============================================================================
# ============================================================================
# Models (DTOs)
# ============================================================================
from ._models import (
    # Portfolio
    AccountSummary,
    # Market Data
    Bar,
    # Contract Resolution
    Contract,
    # Metadata
    EventMeta,
    Health,
    # Instruments
    Instrument,
    MarketDepth,
    # Options
    OptionChain,
    OptionContract,  # Alias for OptionSnapshot
    OptionGreeks,
    OptionSnapshot,
    PortfolioUpdate,
    Position,
    PriceBar,  # Alias for Bar
    Quote,
    Trade,
)

# ============================================================================
# Configuration System (NEW in v1.2.10 - Phase 11.2)
# ============================================================================
from .configs import (
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
    load_config,
)

# ============================================================================
# Errors (canonical exceptions)
# ============================================================================
# ============================================================================
# Error Extensions (NEW in v1.1.0)
# ============================================================================
from .errors import (
    # Non-retryable
    AuthenticationFailed,
    # Pipeline
    BatcherError,
    ConfigurationError,
    # Backward compatibility (deprecated)
    ConnectionException,
    # Retryable
    ConnectionFailed,
    ContractValidationError,
    FarmTransient,
    IBKRPacingError,
    IBKRUnavailable,
    InvalidInstrument,
    # Base
    MarketDataError,
    MarketDataException,
    NonRetryableProviderError,
    PacingViolation,
    PermissionsMissing,
    PipelineError,
    ProviderException,
    RateLimitException,
    # ... existing errors already imported above ...
    # NEW for v1.1.0
    RegistryError,
    RetryableProviderError,
    SinkError,
    SourceError,
    TemporaryUnavailable,
    TransformError,
    # Validation
    ValidationError,
    ValidationException,
)

# ============================================================================
# Federation (NEW in v1.1.0)
# ============================================================================
from .federation import (
    ClusterId,
    ClusterTopology,
    NodeId,
    NodeRole,
    NodeStatus,
    Region,
)

# ============================================================================
# Schema Registry (NEW in v1.2.0 - Phase 11.1)
# ============================================================================
from .models.registry import (
    EnforcementMode,
    SchemaDeprecatedEvent,
    SchemaDriftEvent,
    SchemaPublishedEvent,
    SchemaValidationResult,
)

# ============================================================================
# Protocol Extensions (NEW in v1.1.0)
# ============================================================================
from .protocols import (
    FederationDirectory,
    FeedbackPublisher,
    MarketDataProvider,
    PipelineRunner,
    # ... existing protocols already imported above ...
    # NEW for v1.1.0
    ProviderRegistry,
    RateController,
    Sink,
    SinkRegistry,
    Source,
    Transform,
)

# ============================================================================
# Provider Adapters (NEW in v1.2.10 - Phase 11.2)
# ============================================================================
from .providers import (
    IBKRAdapter,
    SyntheticAdapter,
)

# Note: For runtime layer, import directly:
#   from market_data_core.runtime import Bar, Provider, ProviderRegistry
#   from market_data_core.configs import load_config
# ============================================================================
# Registry (NEW in v1.1.0)
# ============================================================================
from .registry import (
    Capability,
    DriftDetector,
    EnforcementPolicy,
    ProviderSpec,
    RegistryClient,
    SchemaUsageTracker,
    SinkSpec,
    get_enforcement_mode,
    should_enforce_strict,
    should_log_warning,
)

# ============================================================================
# Runtime Layer (NEW in v1.2.10 - Phase 11.2)
# ============================================================================
# Note: Bar and ProviderRegistry have naming conflicts with existing exports
# Access via: from market_data_core.runtime import Bar, ProviderRegistry, Provider
# Or use providers directly: from market_data_core.providers import IBKRAdapter, SyntheticAdapter
# ============================================================================
# Settings (configuration)
# ============================================================================
from .settings import (
    # NEW in v1.1.0
    CompositeSettings,
    CoreSettings,
    ProviderConfig,
    SinkConfig,
    WiringPlan,
    # Backward compatibility functions
    get_database_config,
    get_ibkr_config,
    get_pipeline_config,
)

# ============================================================================
# Telemetry (NEW in v1.1.0)
# ============================================================================
from .telemetry import (
    AuditEnvelope,
    BackpressureLevel,
    ControlAction,
    ControlResult,
    FeedbackEvent,
    HealthComponent,
    HealthState,
    HealthStatus,
    Labels,
    MetricPoint,
    MetricSeries,
    Probe,
    RateAdjustment,
)

# ============================================================================
# Version
# ============================================================================
__version__ = "1.2.35"

# ============================================================================
# Backward Compatibility (deprecated - will be removed in v2.0)
# ============================================================================
try:
    # Re-export pipeline functions if available (deprecated)
    from market_data_pipeline import (
        create_explicit_pipeline,
        create_pipeline,
        ensure_windows_selector_event_loop,
    )

    _has_pipeline_compat = True
except ImportError:
    _has_pipeline_compat = False
    create_pipeline = None  # type: ignore
    create_explicit_pipeline = None  # type: ignore
    ensure_windows_selector_event_loop = None  # type: ignore

# ============================================================================
# Public API
# ============================================================================
__all__ = [
    # Version
    "__version__",
    # Protocols
    "MarketDataProvider",
    "Source",
    "Transform",
    "Sink",
    "PipelineRunner",
    # Protocols - NEW v1.1.0
    "ProviderRegistry",
    "SinkRegistry",
    "FeedbackPublisher",
    "RateController",
    "FederationDirectory",
    # Models - Instruments
    "Instrument",
    # Models - Market Data
    "Bar",
    "PriceBar",
    "Quote",
    "Trade",
    "MarketDepth",
    # Models - Options
    "OptionSnapshot",
    "OptionContract",
    "OptionGreeks",
    "OptionChain",
    # Models - Portfolio
    "Position",
    "AccountSummary",
    "PortfolioUpdate",
    # Models - Metadata
    "EventMeta",
    "Health",
    "Contract",
    # Telemetry - NEW v1.1.0
    "BackpressureLevel",
    "FeedbackEvent",
    "RateAdjustment",
    "HealthState",
    "HealthComponent",
    "HealthStatus",
    "Probe",
    "MetricPoint",
    "MetricSeries",
    "Labels",
    "ControlAction",
    "ControlResult",
    "AuditEnvelope",
    # Federation - NEW v1.1.0
    "ClusterId",
    "NodeId",
    "NodeRole",
    "Region",
    "NodeStatus",
    "ClusterTopology",
    # Registry - NEW v1.1.0
    "Capability",
    "ProviderSpec",
    "SinkSpec",
    # Schema Registry - NEW v1.2.0 (Phase 11.1)
    "EnforcementMode",
    "SchemaPublishedEvent",
    "SchemaDeprecatedEvent",
    "SchemaDriftEvent",
    "SchemaValidationResult",
    "RegistryClient",
    "DriftDetector",
    "EnforcementPolicy",
    "SchemaUsageTracker",
    "get_enforcement_mode",
    "should_enforce_strict",
    "should_log_warning",
    # Errors - Base
    "MarketDataError",
    # Errors - Retryable
    "RetryableProviderError",
    "PacingViolation",
    "FarmTransient",
    "ConnectionFailed",
    "TemporaryUnavailable",
    # Errors - Non-retryable
    "NonRetryableProviderError",
    "PermissionsMissing",
    "InvalidInstrument",
    "ConfigurationError",
    "AuthenticationFailed",
    # Errors - Validation
    "ValidationError",
    # Errors - Pipeline
    "PipelineError",
    "SourceError",
    "TransformError",
    "SinkError",
    "BatcherError",
    # Errors - NEW v1.1.0
    "RegistryError",
    "ContractValidationError",
    # Settings
    "CoreSettings",
    # Settings - NEW v1.1.0
    "CompositeSettings",
    "ProviderConfig",
    "SinkConfig",
    "WiringPlan",
    # Configuration System - NEW v1.2.10 (Phase 11.2)
    "load_config",
    "AppConfig",
    "Provider",
    "Providers",
    "IBKRProvider",
    "SyntheticProvider",
    "PacingBudget",
    "RetryPolicy",
    "StorageConfig",
    "StorageTarget",
    "TimescaleStorage",
    "S3Storage",
    "Dataset",
    "Datasets",
    "Job",
    "Jobs",
    "Schedule",
    "CronSchedule",
    "IntervalSchedule",
    "BackfillSpec",
    "ExecutionPolicy",
    "Telemetry",
    "Metrics",
    "Tracing",
    "Features",
    # Runtime Layer - NEW v1.2.10 (Phase 11.2)
    # Note: Bar and ProviderRegistry already exported above
    # Import via: from market_data_core.runtime import Bar, ProviderRegistry
    # Provider Adapters - NEW v1.2.10 (Phase 11.2)
    "IBKRAdapter",
    "SyntheticAdapter",
]

# Add backward compatibility exports if available
if _has_pipeline_compat:
    __all__.extend(
        [
            "create_pipeline",
            "create_explicit_pipeline",
            "ensure_windows_selector_event_loop",
        ]
    )
