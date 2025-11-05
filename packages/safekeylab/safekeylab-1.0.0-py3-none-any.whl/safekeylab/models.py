"""
SafeKey Lab API Models
Data models for API responses
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PIIEntity:
    """Represents a detected PII entity"""
    type: str
    value: str
    start: int
    end: int
    confidence: float
    category: Optional[str] = None

    def __repr__(self):
        return f"PIIEntity(type='{self.type}', value='{self.value}', position=[{self.start}:{self.end}])"


@dataclass
class ProtectResponse:
    """Response from protect endpoint"""
    redacted_text: str
    original_length: int
    redacted_length: int
    pii_count: int
    processing_time_ms: float
    entities: Optional[List[PIIEntity]] = None
    request_id: Optional[str] = None
    dataset_type: Optional[str] = None

    def __init__(self, **kwargs):
        self.redacted_text = kwargs.get("redacted_text", "")
        self.original_length = kwargs.get("original_length", 0)
        self.redacted_length = kwargs.get("redacted_length", 0)
        self.pii_count = kwargs.get("pii_count", 0)
        self.processing_time_ms = kwargs.get("processing_time_ms", 0.0)
        self.request_id = kwargs.get("request_id")
        self.dataset_type = kwargs.get("dataset_type")

        # Parse entities if provided
        entities_data = kwargs.get("entities", [])
        if entities_data:
            self.entities = [
                PIIEntity(
                    type=e.get("type"),
                    value=e.get("value"),
                    start=e.get("start", 0),
                    end=e.get("end", 0),
                    confidence=e.get("confidence", 1.0),
                    category=e.get("category")
                )
                for e in entities_data
            ]
        else:
            self.entities = None

    @property
    def redaction_percentage(self) -> float:
        """Calculate percentage of text that was redacted"""
        if self.original_length == 0:
            return 0.0
        return ((self.original_length - self.redacted_length) / self.original_length) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        result = {
            "redacted_text": self.redacted_text,
            "original_length": self.original_length,
            "redacted_length": self.redacted_length,
            "pii_count": self.pii_count,
            "processing_time_ms": self.processing_time_ms,
            "redaction_percentage": self.redaction_percentage
        }

        if self.request_id:
            result["request_id"] = self.request_id

        if self.dataset_type:
            result["dataset_type"] = self.dataset_type

        if self.entities:
            result["entities"] = [
                {
                    "type": e.type,
                    "value": e.value,
                    "start": e.start,
                    "end": e.end,
                    "confidence": e.confidence,
                    "category": e.category
                }
                for e in self.entities
            ]

        return result


@dataclass
class FileProtectResponse:
    """Response from protect/file endpoint"""
    file_id: str
    file_url: str
    original_filename: str
    processed_filename: str
    file_size_bytes: int
    pii_count: int
    processing_time_ms: float
    file_type: str
    status: str
    entities: Optional[List[PIIEntity]] = None
    request_id: Optional[str] = None
    download_url: Optional[str] = None
    expires_at: Optional[str] = None

    def __init__(self, **kwargs):
        self.file_id = kwargs.get("file_id", "")
        self.file_url = kwargs.get("file_url", "")
        self.original_filename = kwargs.get("original_filename", "")
        self.processed_filename = kwargs.get("processed_filename", "")
        self.file_size_bytes = kwargs.get("file_size_bytes", 0)
        self.pii_count = kwargs.get("pii_count", 0)
        self.processing_time_ms = kwargs.get("processing_time_ms", 0.0)
        self.file_type = kwargs.get("file_type", "")
        self.status = kwargs.get("status", "completed")
        self.request_id = kwargs.get("request_id")
        self.download_url = kwargs.get("download_url", self.file_url)
        self.expires_at = kwargs.get("expires_at")

        # Parse entities if provided
        entities_data = kwargs.get("entities", [])
        if entities_data:
            self.entities = [
                PIIEntity(
                    type=e.get("type"),
                    value=e.get("value"),
                    start=e.get("start", 0),
                    end=e.get("end", 0),
                    confidence=e.get("confidence", 1.0),
                    category=e.get("category")
                )
                for e in entities_data
            ]
        else:
            self.entities = None

    def is_ready(self) -> bool:
        """Check if file processing is complete"""
        return self.status == "completed"

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            "file_id": self.file_id,
            "file_url": self.file_url,
            "download_url": self.download_url,
            "original_filename": self.original_filename,
            "processed_filename": self.processed_filename,
            "file_size_bytes": self.file_size_bytes,
            "pii_count": self.pii_count,
            "processing_time_ms": self.processing_time_ms,
            "file_type": self.file_type,
            "status": self.status,
            "expires_at": self.expires_at
        }


@dataclass
class ComplianceStatus:
    """HIPAA compliance status"""
    hipaa_compliant: bool
    audit_logs_enabled: bool
    encryption_at_rest: bool
    encryption_in_transit: bool
    data_retention_days: int
    last_audit_date: Optional[str] = None
    compliance_score: Optional[float] = None
    certifications: Optional[List[str]] = None

    def __init__(self, **kwargs):
        self.hipaa_compliant = kwargs.get("hipaa_compliant", False)
        self.audit_logs_enabled = kwargs.get("audit_logs_enabled", False)
        self.encryption_at_rest = kwargs.get("encryption_at_rest", True)
        self.encryption_in_transit = kwargs.get("encryption_in_transit", True)
        self.data_retention_days = kwargs.get("data_retention_days", 30)
        self.last_audit_date = kwargs.get("last_audit_date")
        self.compliance_score = kwargs.get("compliance_score")
        self.certifications = kwargs.get("certifications", ["HIPAA", "SOC2"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "hipaa_compliant": self.hipaa_compliant,
            "audit_logs_enabled": self.audit_logs_enabled,
            "encryption_at_rest": self.encryption_at_rest,
            "encryption_in_transit": self.encryption_in_transit,
            "data_retention_days": self.data_retention_days,
            "last_audit_date": self.last_audit_date,
            "compliance_score": self.compliance_score,
            "certifications": self.certifications
        }