#!/usr/bin/env python3
"""
Wrapper historico del extractor canónico de medios en Radar.

La implementación real de automatización vive en
`automation/extractors/media_extractor.py` y
`automation/extractors/media_extractor_core.py`. Este archivo conserva el
nombre histórico `04_medios_extractor.py` para no romper llamados existentes.
"""

from __future__ import annotations

from pathlib import Path

from automation.extractors.media_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name="04_medios_extractor.py",
            script_path=Path(__file__).resolve(),
            entrypoint_alias="legacy_wrapper",
        )
    )
