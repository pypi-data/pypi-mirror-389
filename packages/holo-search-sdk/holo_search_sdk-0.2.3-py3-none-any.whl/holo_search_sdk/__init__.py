"""
Holo Search SDK - A Python SDK for database search operations.

This SDK provides a unified interface for vector search and full-text search.
"""

from importlib.metadata import version

from .client import Client, connect
from .exceptions import (
    ConnectionError,
    HoloSearchError,
    QueryError,
    SqlError,
    TableError,
)
from .types import ConnectionConfig

__version__ = version("holo-search-sdk")
__author__ = "Tiancheng YANG"
__email__ = "yangtiancheng.ytc@alibaba-inc.com"

__all__ = [
    # Core functions
    "connect",
    # Main classes
    "Client",
    "Collection",
    "Query",
    "VectorQuery",
    "TextQuery",
    "HybridQuery",
    "Schema",
    "Field",
    # Types
    "ConnectionConfig",
    # Exceptions
    "HoloSearchError",
    "ConnectionError",
    "QueryError",
    "SqlError",
    "TableError",
]
