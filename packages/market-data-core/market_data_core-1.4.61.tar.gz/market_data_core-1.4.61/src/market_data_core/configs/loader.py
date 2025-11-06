"""Configuration loader with layered includes, env expansion, and profile overlays.

Features:
- Load YAML files with includes (recursive, circular-safe)
- Deep merge of layered configs (later wins)
- Environment variable expansion: ${VAR} or ${VAR:-default}
- Profile overlays (dev/staging/prod)
- Config fingerprinting for reproducibility
- Returns validated AppConfig model
"""

import copy
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

from .model import AppConfig

# Regex for environment variable expansion: ${VAR} or ${VAR:-default}
_ENV_RE = re.compile(r"\$\{([A-Z0-9_]+)(?::-(.+?))?\}")


def _env_expand(val: Any) -> Any:
    """Recursively expand environment variables in strings, lists, and dicts.

    Supports:
    - ${VAR}: required env var
    - ${VAR:-default}: optional env var with default

    Args:
        val: Value to expand (str, list, dict, or primitive)

    Returns:
        Value with environment variables expanded
    """
    if isinstance(val, str):

        def sub(match: re.Match[str]) -> str:
            key, default = match.group(1), match.group(2)
            return os.environ.get(key, default if default is not None else "")

        return _ENV_RE.sub(sub, val)
    if isinstance(val, list):
        return [_env_expand(x) for x in val]
    if isinstance(val, dict):
        return {k: _env_expand(v) for k, v in val.items()}
    return val


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries (overlay wins on conflicts).

    Args:
        base: Base dictionary
        overlay: Overlay dictionary (wins on conflicts)

    Returns:
        Merged dictionary
    """
    result = copy.deepcopy(base)
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file.

    Args:
        path: Path to YAML file

    Returns:
        Parsed YAML as dictionary

    Raises:
        FileNotFoundError: If file doesn't exist
        yaml.YAMLError: If YAML is malformed
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _load_with_includes(base_path: Path, visited: set[Path] | None = None) -> dict[str, Any]:
    """Recursively load YAML with includes, merging in order.

    Includes are processed first (in order), then the base file is merged on top.
    Circular includes are detected and skipped.

    Args:
        base_path: Path to base YAML file
        visited: Set of already-visited paths (for circular detection)

    Returns:
        Merged configuration dictionary
    """
    if visited is None:
        visited = set()

    base_path = base_path.resolve()
    doc = _load_yaml(base_path)
    includes: list[str] = doc.get("includes", [])

    # Start with empty root
    root: dict[str, Any] = {}

    # Process includes first (in order)
    for include_rel in includes:
        include_path = (base_path.parent / include_rel).resolve()

        # Skip if already visited (circular include)
        if include_path in visited:
            continue

        visited.add(include_path)
        root = _deep_merge(root, _load_with_includes(include_path, visited))

    # Merge base document on top of includes
    root = _deep_merge(root, doc)

    return root


def _compute_fingerprint(config_dict: dict[str, Any]) -> str:
    """Compute SHA-256 fingerprint of configuration for reproducibility.

    The fingerprint is deterministic for the same config values, allowing:
    - Tracking which config version produced which data
    - Debugging deployment issues
    - Ensuring reproducible data pipelines

    Args:
        config_dict: Configuration dictionary (after env expansion)

    Returns:
        Hex-encoded SHA-256 hash of the configuration

    Note:
        The fingerprint is computed on the JSON representation to ensure
        consistent ordering and formatting.
    """
    # Sort keys for deterministic output
    canonical = json.dumps(config_dict, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_config(path: str | Path, profile_override: str | None = None) -> AppConfig:
    """Load and validate application configuration.

    Performs the following steps:
    1. Load base YAML file with recursive includes
    2. Apply profile overlay (dev/staging/prod)
    3. Expand environment variables
    4. Compute config fingerprint
    5. Validate with Pydantic model

    Args:
        path: Path to base config file (YAML)
        profile_override: Profile to use (dev/staging/prod). If None, uses
            'profile' key from config or APP_PROFILE env var (default: dev)

    Returns:
        Validated AppConfig instance with fingerprint

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML is malformed
        pydantic.ValidationError: If config doesn't match schema

    Example:
        >>> cfg = load_config("configs/prices.yaml", profile_override="prod")
        >>> print(cfg.profile)
        prod
        >>> print(cfg.fingerprint)
        a7f5c8d9e3b2f4a1...
        >>> print(cfg.providers.root["ibkr_primary"].host)
        127.0.0.1
    """
    path = Path(path).resolve()

    # Step 1: Load with includes
    raw = _load_with_includes(path)

    # Step 2: Determine active profile
    profile = profile_override or raw.get("profile") or os.environ.get("APP_PROFILE", "dev")

    # Step 3: Apply profile overlay
    profiles_map = raw.get("profiles") or {}
    overlay = profiles_map.get(profile) or {}
    merged = _deep_merge(raw, overlay)

    # Update profile in merged config
    merged["profile"] = profile

    # Step 4: Expand environment variables
    expanded = _env_expand(merged)

    # Step 5: Compute fingerprint for reproducibility
    fingerprint = _compute_fingerprint(expanded)
    expanded["fingerprint"] = fingerprint

    # Step 6: Validate with Pydantic
    return AppConfig(**expanded)
