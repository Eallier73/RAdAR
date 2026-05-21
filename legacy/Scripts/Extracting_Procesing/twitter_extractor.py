#!/usr/bin/env python3
"""
Wrapper canónico del extractor profesional de X/Twitter para Radar.

La implementación real de automatización vive en
`automation/extractors/twitter_extractor.py`. Este archivo deja un nombre
estable para CLI, runners y futuros orquestadores.
"""

from __future__ import annotations

from pathlib import Path

from automation.extractors.twitter_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name="twitter_extractor.py",
            script_path=Path(__file__).resolve(),
            entrypoint_alias="canonical_wrapper",
        )
    )
