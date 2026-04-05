#!/usr/bin/env python3
"""
Wrapper canónico del extractor institucional de Facebook para Radar.

La implementación real de automatización vive en
`automation/extractors/facebook_institutional_extractor.py`. Este archivo deja
un nombre estable para CLI, runners y futuros orquestadores.
"""

from __future__ import annotations

from pathlib import Path

from automation.extractors.facebook_institutional_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name="facebook_institutional_extractor.py",
            script_path=Path(__file__).resolve(),
            entrypoint_alias="canonical_wrapper",
        )
    )
