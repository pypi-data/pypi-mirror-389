"""
Type definitions for Holo Search SDK.

Defines common data types and structures used throughout the SDK.
"""

from dataclasses import dataclass
from typing import Dict, Literal

from typing_extensions import LiteralString


@dataclass
class ConnectionConfig:
    """Configuration for database connections."""

    host: str
    port: int
    database: str
    access_key_id: str
    access_key_secret: str
    schema: str = "public"


# Type aliases used for Vector Search
DistanceType = Literal["Euclidean", "InnerProduct", "Cosine"]
BaseQuantizationType = Literal["sq8", "sq8_uniform", "fp16", "fp32", "rabitq"]
PreciseQuantizationType = Literal["sq8", "sq8_uniform", "fp16", "fp32"]
PreciseIOType = Literal["block_memory_io", "reader_io"]


# Functions for Vector Search
VectorSearchFunction: Dict[DistanceType, LiteralString] = {
    "Euclidean": "approx_euclidean_distance",
    "InnerProduct": "approx_inner_product_distance",
    "Cosine": "approx_cosine_distance",
}
