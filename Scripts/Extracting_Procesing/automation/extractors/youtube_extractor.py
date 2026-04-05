#!/usr/bin/env python3
"""
Entrypoint canónico de automatización para el extractor de YouTube.
"""

from __future__ import annotations

from .youtube_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(main())
