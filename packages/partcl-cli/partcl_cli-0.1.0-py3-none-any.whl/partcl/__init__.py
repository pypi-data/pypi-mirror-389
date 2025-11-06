"""Partcl - Python CLI and library for Partcl EDA tools."""

from __future__ import annotations

from ._version import __version__
from .api import timing
from .client.api import APIClient, TimingResult
from .utils.config import PartclConfig
from .utils.validation import validate_file

__all__ = [
    "timing",
    "APIClient",
    "TimingResult",
    "PartclConfig",
    "validate_file",
    "__version__",
]

__author__ = "Partcl Team"
__email__ = "support@partcl.com"
