#!/usr/bin/env python3
"""
Wrapper historico del extractor profesional de YouTube para Radar.

La implementacion real de automatizacion vive en
`automation/extractors/youtube_extractor.py`. Este archivo conserva el nombre
operativo anterior para no romper llamados existentes.
"""

from __future__ import annotations

from pathlib import Path

from automation.extractors.youtube_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name="01_youtube_extractor_Tampico.py",
            script_path=Path(__file__).resolve(),
            entrypoint_alias="legacy_wrapper",
        )
    )
