#!/usr/bin/env python3
"""
Wrapper de compatibilidad para el extractor canónico de medios en Radar.

La implementación profesionalizada vive en `media_extractor.py` y
`media_extractor_core.py`. Este archivo conserva el nombre histórico
`04_medios_extractor.py` para no romper llamados existentes.
"""

from __future__ import annotations

from pathlib import Path

from media_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name="04_medios_extractor.py",
            script_path=Path(__file__).resolve(),
            entrypoint_alias="legacy_wrapper",
        )
    )
