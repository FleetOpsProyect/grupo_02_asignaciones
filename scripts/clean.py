#!/usr/bin/env python3
"""Elimina el entorno virtual (.venv) y los archivos de cache del proyecto.

Uso:
    python scripts/clean.py            # elimina
    python scripts/clean.py --dry-run  # solo muestra que se eliminaria

Para volver a crear el entorno despues de limpiar: `uv sync`.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Directorios y archivos sueltos que viven siempre en la raiz del proyecto.
ROOT_DIRS = [".venv", ".pytest_cache", ".mypy_cache", ".ruff_cache", "htmlcov"]
ROOT_FILES = [".coverage", "coverage.xml"]

# Patrones que pueden aparecer repetidos en cualquier subcarpeta del proyecto.
GLOB_DIR_PATTERNS = ["__pycache__", "*.egg-info"]
GLOB_FILE_PATTERNS = ["*.pyc", "*.pyo"]


def remove(path: Path, dry_run: bool) -> None:
    if not path.exists():
        return
    prefix = "[dry-run] " if dry_run else ""
    print(f"{prefix}eliminando {path.relative_to(ROOT)}")
    if dry_run:
        return
    if path.is_dir():
        shutil.rmtree(path, ignore_errors=True)
    else:
        path.unlink(missing_ok=True)


def under_excluded(path: Path, excluded: list[Path]) -> bool:
    return any(excluded_dir in path.parents for excluded_dir in excluded)


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    # Carpetas que ya se eliminan completas: no vale la pena (ni es legible)
    # listar cada __pycache__ que tengan adentro, p.ej. dentro de .venv.
    excluded = [ROOT / name for name in (*ROOT_DIRS, ".git")]

    for name in ROOT_DIRS:
        remove(ROOT / name, dry_run)

    for name in ROOT_FILES:
        remove(ROOT / name, dry_run)

    for pattern in GLOB_DIR_PATTERNS:
        for path in sorted(ROOT.rglob(pattern), key=lambda p: len(p.parts), reverse=True):
            if path.is_dir() and not under_excluded(path, excluded):
                remove(path, dry_run)

    for pattern in GLOB_FILE_PATTERNS:
        for path in ROOT.rglob(pattern):
            if not under_excluded(path, excluded):
                remove(path, dry_run)

    print("Dry-run completo, nada se elimino." if dry_run else "Listo.")


if __name__ == "__main__":
    main()
