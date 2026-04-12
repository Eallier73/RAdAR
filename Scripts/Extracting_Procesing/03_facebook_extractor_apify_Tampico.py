#!/usr/bin/env python3
"""
Wrapper legado del extractor institucional de Facebook.

La implementación real vive en
`automation/extractors/facebook_institutional_extractor_core.py`.
Este archivo se conserva solo por compatibilidad con llamadas históricas.
"""

from __future__ import annotations

from pathlib import Path

from automation.extractors.facebook_institutional_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name="03_facebook_extractor_apify_Tampico.py",
            script_path=Path(__file__).resolve(),
            entrypoint_alias="legacy_wrapper",
        )
    )
