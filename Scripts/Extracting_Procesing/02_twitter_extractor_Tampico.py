#!/usr/bin/env python3
"""
Wrapper historico del extractor profesional de X/Twitter para Radar.

La implementacion real de automatizacion vive en
`automation/extractors/twitter_extractor.py`. Este archivo conserva el nombre
operativo anterior para no romper llamados existentes.
"""

from __future__ import annotations

from pathlib import Path

from automation.extractors.twitter_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name="02_twitter_extractor_Tampico.py",
            script_path=Path(__file__).resolve(),
            entrypoint_alias="legacy_wrapper",
        )
    )
