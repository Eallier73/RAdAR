#!/usr/bin/env python3
"""
Entrypoint público recomendado del extractor institucional de Facebook.

La implementación real vive en
`automation/extractors/facebook_institutional_extractor_core.py`.
Este archivo es la ruta CLI que debe usarse en operación normal.
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
