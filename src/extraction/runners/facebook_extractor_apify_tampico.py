#!/usr/bin/env python3
"""Legacy entrypoint kept for pipeline compatibility."""

from __future__ import annotations

from pathlib import Path

from .facebook_institutional_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(
        main(
            script_name=Path(__file__).name,
            script_path=Path(__file__).resolve(),
            entrypoint_alias="src.extraction.runners.facebook_extractor_apify_tampico",
        )
    )
