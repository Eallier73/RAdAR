"""Shared utilities used across the canonical source tree."""

from .secrets import (
    check_secrets,
    check_secrets_for_source,
    get_secret,
    load_env,
    require_secret,
    secrets_summary,
    source_secrets_ready,
)
from .runtime_paths import (
    DOT_ENV_PATH,
    MEDIOS_RSS_CACHE_DIR,
    RAW_WEEKLY_ROOT,
    REPO_ROOT,
    STATE_DIR,
    TEXT_WEEKLY_ROOT,
    TWITTER_STATE_PATH,
)

__all__ = [
    # secrets
    "load_env",
    "get_secret",
    "require_secret",
    "check_secrets",
    "check_secrets_for_source",
    "source_secrets_ready",
    "secrets_summary",
    # runtime_paths
    "REPO_ROOT",
    "DOT_ENV_PATH",
    "STATE_DIR",
    "TWITTER_STATE_PATH",
    "MEDIOS_RSS_CACHE_DIR",
    "RAW_WEEKLY_ROOT",
    "TEXT_WEEKLY_ROOT",
]
