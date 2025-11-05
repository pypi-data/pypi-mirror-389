"""
SafeKey Lab Python SDK
Healthcare Data Privacy & HIPAA Compliance API

Protect sensitive patient data with enterprise-grade PII detection and redaction.
"""

from .client import SafeKeyLab
from .exceptions import (
    SafeKeyLabError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    APIError
)
from .models import (
    ProtectResponse,
    ComplianceStatus,
    PIIEntity,
    FileProtectResponse
)

__version__ = "1.0.0"
__author__ = "SafeKey Lab"
__email__ = "support@safekeylab.com"

__all__ = [
    "SafeKeyLab",
    "SafeKeyLabError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "APIError",
    "ProtectResponse",
    "ComplianceStatus",
    "PIIEntity",
    "FileProtectResponse",
]