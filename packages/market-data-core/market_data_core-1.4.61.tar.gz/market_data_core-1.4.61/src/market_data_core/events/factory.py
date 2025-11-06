"""Factory functions for creating event bus instances.

Provides convenient helpers for creating event buses based on configuration.
"""

from __future__ import annotations

import os
from typing import Literal

from .adapters import InMemoryBus

try:
    from .adapters import RedisStreamsBus

    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False


def create_event_bus(
    backend: Literal["inmem", "redis"] | None = None,
    redis_url: str | None = None,
    namespace: str | None = None,
    track: str = "v1",
) -> InMemoryBus | RedisStreamsBus:
    """Create an event bus instance based on configuration.

    Args:
        backend: Backend type ("inmem" or "redis"). Defaults to EVENT_BUS_BACKEND env var or "inmem"
        redis_url: Redis connection URL. Defaults to REDIS_URL env var
        namespace: Stream key prefix. Defaults to MD_NAMESPACE env var or "mdp"
        track: Default schema track ("v1" or "v2"). Defaults to SCHEMA_TRACK env var or "v1"

    Returns:
        EventBus instance (InMemoryBus or RedisStreamsBus)

    Raises:
        ValueError: If backend is "redis" but Redis is not available
        ValueError: If backend is "redis" but redis_url is not provided

    Example:
        >>> # Create in-memory bus (for tests)
        >>> bus = create_event_bus(backend="inmem")

        >>> # Create Redis bus (production)
        >>> bus = create_event_bus(
        ...     backend="redis",
        ...     redis_url="redis://localhost:6379/0",
        ...     namespace="prod"
        ... )

        >>> # Auto-detect from environment
        >>> # Set: EVENT_BUS_BACKEND=redis, REDIS_URL=..., MD_NAMESPACE=prod
        >>> bus = create_event_bus()
    """
    # Determine backend from args or env
    backend_name = backend or os.getenv("EVENT_BUS_BACKEND", "inmem")

    # Resolve env vars
    redis_url_resolved = redis_url or os.getenv("REDIS_URL")
    namespace_resolved = namespace or os.getenv("MD_NAMESPACE") or "mdp"
    track = os.getenv("SCHEMA_TRACK", track)

    if backend_name == "inmem":
        return InMemoryBus()

    elif backend_name == "redis":
        if not _REDIS_AVAILABLE:
            raise ValueError(
                "Redis backend requested but redis package is not installed. "
                "Install with: pip install redis"
            )

        if not redis_url_resolved:
            raise ValueError(
                "Redis backend requested but redis_url not provided and REDIS_URL env var not set"
            )

        return RedisStreamsBus(
            redis_url=redis_url_resolved, namespace=namespace_resolved, track=track
        )

    else:
        raise ValueError(f"Unknown backend: {backend}. Must be 'inmem' or 'redis'")


def create_test_bus() -> InMemoryBus:
    """Create an in-memory bus for testing.

    This is a convenience function that always returns InMemoryBus,
    regardless of environment configuration.

    Returns:
        InMemoryBus instance

    Example:
        >>> bus = create_test_bus()
        >>> # Use in tests without worrying about Redis setup
    """
    return InMemoryBus()
