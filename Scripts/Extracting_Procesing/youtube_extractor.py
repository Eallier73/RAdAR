#!/usr/bin/env python3
"""
Wrapper canónico del extractor profesional de YouTube para Radar.

La implementación real de automatización vive en
`automation/extractors/youtube_extractor.py`. Este archivo deja un nombre
simétrico con el extractor de medios para CLI y runners.
"""

from __future__ import annotations

from automation.extractors.youtube_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(main())
