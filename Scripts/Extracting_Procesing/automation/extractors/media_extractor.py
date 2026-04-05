#!/usr/bin/env python3
"""
Entrypoint canónico de automatización para el extractor profesional de medios.
"""

from __future__ import annotations

from pathlib import Path

from .media_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name="media_extractor.py",
            script_path=Path(__file__).resolve(),
            entrypoint_alias="automation_canonical_entrypoint",
        )
    )
