"""Helpers to import modules without loading HA integration package."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def import_module_from_path(module_name: str, path: Path) -> ModuleType:
    """Import a module by filename (bypasses package __init__.py)."""
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot import {module_name} from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

