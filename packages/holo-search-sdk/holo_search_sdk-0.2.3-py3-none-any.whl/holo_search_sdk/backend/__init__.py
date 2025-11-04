"""
Backend module for Holo Search SDK.

Provides table backend implementations and factory functions.
"""

from .database import HoloDB
from .table import HoloTable

__all__ = ["HoloDB", "HoloTable"]
