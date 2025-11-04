"""
RAIL Score Python SDK

Official Python client for the RAIL Score API.
"""

from .client import RailScore
from .exceptions import (
    RailScoreError,
    AuthenticationError,
    InsufficientCreditsError,
    ValidationError,
    RateLimitError
)
from .models import (
    RailScoreResponse,
    DimensionScore,
    ComplianceResponse,
    RAGMetrics
)

__version__ = "1.0.0"
__all__ = [
    "RailScore",
    "RailScoreError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "ValidationError",
    "RateLimitError",
    "RailScoreResponse",
    "DimensionScore",
    "ComplianceResponse",
    "RAGMetrics",
]
