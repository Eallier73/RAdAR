#!/usr/bin/env python3
"""
Entrypoint canónico de automatización para el extractor de YouTube.
"""

from __future__ import annotations

from pathlib import Path

try:
    from .youtube_extractor_core import main
except ImportError:  # pragma: no cover - ejecucion directa del archivo
    from youtube_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name="youtube_extractor.py",
            script_path=Path(__file__).resolve(),
            entrypoint_alias="automation_canonical_entrypoint",
        )
    )
