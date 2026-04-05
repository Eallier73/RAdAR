#!/usr/bin/env python3
"""
Entry point CLI del extractor profesional de YouTube para Radar.

El flujo reutilizable vive en `youtube_extractor_core.py`. Este archivo se
mantiene como wrapper numerado para preservar compatibilidad operativa con la
estructura historica del proyecto y a la vez exponer una interfaz limpia para
terminal, runners Python y futuros orquestadores.
"""

from __future__ import annotations

from youtube_extractor_core import main


if __name__ == "__main__":
    raise SystemExit(main())
