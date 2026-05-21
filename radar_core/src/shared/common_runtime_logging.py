from __future__ import annotations

from datetime import datetime
from typing import Any


def _normalize_value(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.6f}"
    text = str(value).strip()
    return text if text else "-"


def log_event(
    component: str,
    level: str,
    message: str,
    **context: Any,
) -> None:
    timestamp = datetime.now().replace(microsecond=0).isoformat(sep=" ")
    prefix = f"[{timestamp}] [{level.upper()}] [{component}]"
    if context:
        context_text = " | ".join(
            f"{key}={_normalize_value(value)}" for key, value in sorted(context.items())
        )
        print(f"{prefix} {message} | {context_text}")
        return
    print(f"{prefix} {message}")
