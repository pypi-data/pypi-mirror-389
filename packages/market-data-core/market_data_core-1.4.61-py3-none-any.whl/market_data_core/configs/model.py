"""Pydantic models for layered, future-proof configuration.

Supports discriminated unions for providers (IBKR, synthetic, etc.), storage targets,
and schedules. Validates references (dataset → provider) at the root level.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

# ============================================================================
# Shared / Common Models
# ============================================================================


class RetryPolicy(BaseModel):
    """Retry policy for providers and jobs."""

    max_attempts: int = 3
    backoff_seconds: int = 10
    jitter: bool = True


class PacingBudget(BaseModel):
    """Provider rate limiting budget."""

    requests_per_minute: int = 40
    burst: int = 10
    cooldown_seconds: int = 60


# ============================================================================
# Providers (discriminated union by 'type')
# ============================================================================


class IBKRProvider(BaseModel):
    """Interactive Brokers provider configuration."""

    type: Literal["ibkr"]
    enabled: bool = True
    client_id: str | None = None
    account: str | None = None
    host: str = "127.0.0.1"
    port: int = 7497
    paper: bool = True
    timezone: str = "America/New_York"
    what_to_show_default: str = "TRADES"
    pacing: PacingBudget = Field(default_factory=PacingBudget)
    retry: RetryPolicy = Field(default_factory=RetryPolicy)


class SyntheticProvider(BaseModel):
    """Synthetic data provider for testing."""

    type: Literal["synthetic"]
    enabled: bool = False
    seed: int | None = None


# Union of all provider types (extensible: add Polygon, Tiingo, etc.)
Provider = IBKRProvider | SyntheticProvider


class Providers(RootModel[dict[str, Provider]]):
    """Map of provider name → provider config."""

    root: dict[str, Provider] = Field(default_factory=dict)


# ============================================================================
# Storage Targets (discriminated union by 'type')
# ============================================================================


class TSDBWrite(BaseModel):
    """TimescaleDB write configuration."""

    batch_size: int = 1000
    upsert_keys: list[str] = Field(default_factory=lambda: ["symbol", "ts", "interval", "provider"])
    deduplicate: bool = True


class RetentionTier(BaseModel):
    """Retention tier for tiered storage policy."""

    name: str
    keep_days: int
    compress_after_days: int


class TSDBRetention(BaseModel):
    """TimescaleDB retention policy."""

    policy: Literal["tiered", "simple"] = "tiered"
    tiers: list[RetentionTier] = Field(default_factory=list)


class TimescaleStorage(BaseModel):
    """TimescaleDB storage target."""

    type: Literal["timescaledb"]
    uri: str
    db_schema: str = Field(default="public", alias="schema")  # Use alias to allow "schema" in YAML
    table_bars: str = "bars"
    write: TSDBWrite = Field(default_factory=TSDBWrite)
    retention: TSDBRetention = Field(default_factory=TSDBRetention)

    model_config = ConfigDict(populate_by_name=True)  # Allow both "schema" and "db_schema"


class S3Storage(BaseModel):
    """S3/lake storage target."""

    type: Literal["s3"]
    bucket: str
    prefix: str = ""
    format: Literal["parquet", "csv"] = "parquet"
    partitioning: list[str] = Field(default_factory=list)
    write_mode: Literal["append", "overwrite"] = "append"


# Union of all storage types
StorageTarget = TimescaleStorage | S3Storage


class StorageConfig(RootModel[dict[str, StorageTarget]]):
    """Map of storage name → storage target."""

    root: dict[str, StorageTarget] = Field(default_factory=dict)


# ============================================================================
# Datasets & Jobs
# ============================================================================


class Adjustments(BaseModel):
    """Price adjustments configuration."""

    splits: bool = True
    dividends: bool = True


class SLA(BaseModel):
    """Service Level Agreement for a dataset."""

    success_rate_min: float = 0.99
    max_latency_ms: int = 7000


class Dataset(BaseModel):
    """Dataset specification (what to fetch)."""

    provider: str  # Reference to providers map
    symbols: list[str] | str  # List or "@watchlists.foo" reference
    interval: str  # "1min", "5min", "1d", etc.
    fields: list[str] = Field(default_factory=lambda: ["open", "high", "low", "close", "volume"])
    adjustments: Adjustments = Field(default_factory=Adjustments)
    calendar: str | None = None  # Reference to calendars map
    timezone: str = "UTC"
    bar_size_hint: str | None = None  # Provider-specific hint (e.g., "5 min" for IBKR)
    sla: SLA | None = None


class Datasets(RootModel[dict[str, Dataset]]):
    """Map of dataset name → dataset config."""

    root: dict[str, Dataset] = Field(default_factory=dict)


class BackfillSpec(BaseModel):
    """Backfill specification for historical data fetch."""

    from_: str = Field(..., alias="from")  # e.g., "now-3y"
    to: str = "now"
    chunk: str = "30d"
    concurrency: int = 1

    class Config:
        populate_by_name = True  # Allow both "from" and "from_"


class CronSchedule(BaseModel):
    """Cron-based schedule."""

    type: Literal["cron"] = "cron"
    expr: str  # Cron expression
    window: dict[str, Any] | None = None  # e.g., align_to_session, skip_holidays


class IntervalSchedule(BaseModel):
    """Interval-based schedule."""

    type: Literal["interval"] = "interval"
    every: str  # e.g., "5m", "1h"


# Union of schedule types
Schedule = CronSchedule | IntervalSchedule


class ExecutionPolicy(BaseModel):
    """Job execution policy."""

    concurrency: int = 1
    rate_limit: dict[str, str] | None = None  # e.g., {"provider_budget_ref": "ibkr_primary"}
    retry: RetryPolicy = Field(default_factory=RetryPolicy)


class Job(BaseModel):
    """Job specification (how/when to run a dataset)."""

    dataset: str  # Reference to datasets map
    mode: Literal["live", "backfill"]
    schedule: Schedule | None = None
    backfill: BackfillSpec | None = None
    execution: ExecutionPolicy = Field(default_factory=ExecutionPolicy)


class Jobs(RootModel[dict[str, Job]]):
    """Map of job name → job config."""

    root: dict[str, Job] = Field(default_factory=dict)


# ============================================================================
# Telemetry & Features
# ============================================================================


class Metrics(BaseModel):
    """Metrics configuration."""

    enabled: bool = True
    port: int = 9090


class Tracing(BaseModel):
    """Distributed tracing configuration."""

    otlp_endpoint: str | None = None
    sample_ratio: float = 0.0


class Telemetry(BaseModel):
    """Telemetry configuration."""

    log_level: Literal["DEBUG", "INFO", "WARN", "ERROR"] = "INFO"
    metrics: Metrics = Field(default_factory=Metrics)
    tracing: Tracing = Field(default_factory=Tracing)


class Features(BaseModel):
    """Feature flags."""

    dry_run: bool = False
    write_enabled: bool = True
    export_enabled: bool = False


# ============================================================================
# Root Configuration
# ============================================================================


class AppConfig(BaseModel):
    """Root application configuration with validation.

    Validates:
    - Dataset references to providers exist
    - Job references to datasets exist

    Includes:
    - Config fingerprint for reproducibility tracking
    """

    version: int = 2
    profile: Literal["dev", "staging", "prod"] = "dev"
    includes: list[str] = Field(default_factory=list)

    providers: Providers = Field(default_factory=Providers)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    datasets: Datasets = Field(default_factory=Datasets)
    jobs: Jobs = Field(default_factory=Jobs)

    telemetry: Telemetry = Field(default_factory=Telemetry)
    features: Features = Field(default_factory=Features)

    # Optional: calendars, watchlists, profiles (merged during loading)
    calendars: dict[str, Any] | None = None
    watchlists: dict[str, list[str]] | None = None
    profiles: dict[str, Any] | None = None

    # Config fingerprint for reproducibility (set by loader)
    fingerprint: str | None = Field(
        default=None, description="SHA-256 hash of config for reproducibility tracking"
    )

    @model_validator(mode="after")
    def validate_refs(self) -> "AppConfig":
        """Validate that dataset → provider and job → dataset references exist."""
        providers_map = self.providers.root
        datasets_map = self.datasets.root
        jobs_map = self.jobs.root

        # Validate dataset → provider
        for ds_name, ds in datasets_map.items():
            if ds.provider not in providers_map:
                raise ValueError(f"Dataset '{ds_name}' references unknown provider '{ds.provider}'")

        # Validate job → dataset
        for job_name, job in jobs_map.items():
            if job.dataset not in datasets_map:
                raise ValueError(f"Job '{job_name}' references unknown dataset '{job.dataset}'")

        return self

    # No field validators needed - RootModel handles dict wrapping automatically
