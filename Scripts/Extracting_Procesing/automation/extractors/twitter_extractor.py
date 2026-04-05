#!/usr/bin/env python3
"""
Entrypoint canónico de automatización para el extractor profesional de X/Twitter.
"""

from __future__ import annotations

from pathlib import Path

try:
    from .twitter_extractor_core import main
except ImportError:  # pragma: no cover - ejecucion directa del archivo
    from twitter_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name="twitter_extractor.py",
            script_path=Path(__file__).resolve(),
            entrypoint_alias="automation_canonical_entrypoint",
        )
    )
