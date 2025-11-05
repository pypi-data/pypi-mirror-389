"""
SafeKey Lab API Client
Main client for interacting with SafeKey Lab API
"""

import os
import json
import time
from typing import Optional, Dict, Any, List, BinaryIO
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from .exceptions import (
    AuthenticationError,
    RateLimitError,
    ValidationError,
    APIError,
    SafeKeyLabError
)
from .models import (
    ProtectResponse,
    FileProtectResponse,
    ComplianceStatus,
    PIIEntity
)


class SafeKeyLab:
    """
    SafeKey Lab API Client

    Protect healthcare data with enterprise-grade PII detection and redaction.

    Args:
        api_key (str, optional): Your SafeKey Lab API key. If not provided,
                                will look for SAFEKEYLAB_API_KEY environment variable.
        base_url (str, optional): API base URL. Defaults to production API.
        timeout (int, optional): Request timeout in seconds. Defaults to 30.
        max_retries (int, optional): Maximum number of retries for failed requests. Defaults to 3.

    Example:
        >>> from safekeylab import SafeKeyLab
        >>> client = SafeKeyLab(api_key="sk-...")
        >>> response = client.protect(text="Patient John Doe, DOB 01/15/1980")
        >>> print(response.redacted_text)
        Patient [REDACTED], DOB [REDACTED]
    """

    DEFAULT_BASE_URL = "https://api.safekeylab.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.api_key = api_key or os.getenv("SAFEKEYLAB_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key is required. Provide it as a parameter or set SAFEKEYLAB_API_KEY environment variable."
            )

        self.base_url = (base_url or os.getenv("SAFEKEYLAB_API_URL", self.DEFAULT_BASE_URL)).rstrip("/")
        self.timeout = timeout

        # Set up session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"SafeKeyLab-Python-SDK/1.0.0"
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to SafeKey Lab API"""
        url = f"{self.base_url}{endpoint}"

        try:
            # Remove Content-Type header if files are being sent
            headers = dict(self.session.headers)
            if files:
                headers.pop("Content-Type", None)

            response = self.session.request(
                method=method,
                url=url,
                json=data if not files else None,
                data=data if files else None,
                files=files,
                params=params,
                headers=headers,
                timeout=self.timeout
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", 5)
                raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds.")

            # Handle authentication errors
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key.")

            if response.status_code == 403:
                raise AuthenticationError("API key doesn't have permission for this operation.")

            # Handle other errors
            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get("error", {}).get("message", response.text)
                except:
                    error_message = response.text

                if response.status_code == 400:
                    raise ValidationError(error_message)
                else:
                    raise APIError(f"API error ({response.status_code}): {error_message}")

            return response.json()

        except requests.exceptions.Timeout:
            raise SafeKeyLabError(f"Request timed out after {self.timeout} seconds.")
        except requests.exceptions.ConnectionError:
            raise SafeKeyLabError("Failed to connect to SafeKey Lab API.")
        except requests.exceptions.RequestException as e:
            raise SafeKeyLabError(f"Request failed: {str(e)}")

    def protect(
        self,
        text: str,
        dataset_type: Optional[str] = None,
        output_format: Optional[str] = None,
        pii_types: Optional[List[str]] = None,
        custom_redaction: Optional[str] = "[REDACTED]",
        return_entities: bool = False
    ) -> ProtectResponse:
        """
        Protect text by detecting and redacting PII

        Args:
            text (str): The text to process
            dataset_type (str, optional): Dataset type for optimized processing ("mimic", "generic", etc.)
            output_format (str, optional): Output format ("json", "text", "mimic_compatible")
            pii_types (List[str], optional): Specific PII types to detect. If None, detects all.
            custom_redaction (str, optional): Custom redaction text. Defaults to "[REDACTED]"
            return_entities (bool, optional): Return detected entities list. Defaults to False.

        Returns:
            ProtectResponse: Response object containing redacted text and metadata

        Example:
            >>> response = client.protect(
            ...     text="Patient John Doe, MRN 123456",
            ...     dataset_type="mimic",
            ...     return_entities=True
            ... )
            >>> print(response.redacted_text)
            Patient [REDACTED], MRN [REDACTED]
            >>> print(response.entities)
            [PIIEntity(type="NAME", value="John Doe", start=8, end=16)]
        """

        data = {
            "text": text,
            "dataset_type": dataset_type or "generic",
            "output_format": output_format or "json",
            "custom_redaction": custom_redaction,
            "return_entities": return_entities
        }

        if pii_types:
            data["pii_types"] = pii_types

        response_data = self._make_request("POST", "/protect", data=data)
        return ProtectResponse(**response_data)

    def protect_file(
        self,
        file: BinaryIO,
        file_type: str,
        dataset_type: Optional[str] = None,
        redact_metadata: bool = True,
        return_entities: bool = False
    ) -> FileProtectResponse:
        """
        Protect file by detecting and redacting PII

        Args:
            file: File object to process
            file_type (str): Type of file ("pdf", "docx", "txt", "dicom", "hl7", "fhir")
            dataset_type (str, optional): Dataset type for optimized processing
            redact_metadata (bool, optional): Redact metadata in files. Defaults to True.
            return_entities (bool, optional): Return detected entities list

        Returns:
            FileProtectResponse: Response object containing processed file info

        Example:
            >>> with open('medical_record.pdf', 'rb') as f:
            ...     response = client.protect_file(
            ...         file=f,
            ...         file_type='pdf'
            ...     )
            >>> print(response.file_url)
            https://api.safekeylab.com/files/protected/abc123.pdf
        """

        files = {
            "file": file
        }

        data = {
            "file_type": file_type,
            "dataset_type": dataset_type or "generic",
            "redact_metadata": str(redact_metadata).lower(),
            "return_entities": str(return_entities).lower()
        }

        response_data = self._make_request("POST", "/protect/file", data=data, files=files)
        return FileProtectResponse(**response_data)

    def protect_batch(
        self,
        texts: List[str],
        dataset_type: Optional[str] = None,
        parallel: bool = True
    ) -> List[ProtectResponse]:
        """
        Process multiple texts in batch

        Args:
            texts (List[str]): List of texts to process
            dataset_type (str, optional): Dataset type for optimized processing
            parallel (bool, optional): Process in parallel. Defaults to True.

        Returns:
            List[ProtectResponse]: List of response objects

        Example:
            >>> texts = [
            ...     "Patient John Doe",
            ...     "SSN: 123-45-6789"
            ... ]
            >>> responses = client.protect_batch(texts)
        """

        data = {
            "texts": texts,
            "dataset_type": dataset_type or "generic",
            "parallel": parallel
        }

        response_data = self._make_request("POST", "/protect/batch", data=data)
        return [ProtectResponse(**item) for item in response_data["results"]]

    def get_compliance_status(self) -> ComplianceStatus:
        """
        Get HIPAA compliance status for your account

        Returns:
            ComplianceStatus: Compliance status and audit information

        Example:
            >>> status = client.get_compliance_status()
            >>> print(status.hipaa_compliant)
            True
            >>> print(status.audit_logs_enabled)
            True
        """

        response_data = self._make_request("GET", "/compliance/status")
        return ComplianceStatus(**response_data)

    def get_usage_stats(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get API usage statistics

        Args:
            start_date (str, optional): Start date in YYYY-MM-DD format
            end_date (str, optional): End date in YYYY-MM-DD format

        Returns:
            Dict containing usage statistics

        Example:
            >>> stats = client.get_usage_stats(
            ...     start_date="2024-01-01",
            ...     end_date="2024-01-31"
            ... )
            >>> print(stats["total_api_calls"])
            45823
        """

        params = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        return self._make_request("GET", "/stats", params=params)

    def validate_text(
        self,
        text: str,
        strict: bool = True
    ) -> Dict[str, Any]:
        """
        Validate if text contains PII without redacting

        Args:
            text (str): Text to validate
            strict (bool, optional): Use strict validation. Defaults to True.

        Returns:
            Dict containing validation results

        Example:
            >>> result = client.validate_text("John Doe")
            >>> print(result["contains_pii"])
            True
            >>> print(result["pii_count"])
            1
        """

        data = {
            "text": text,
            "strict": strict
        }

        return self._make_request("POST", "/validate", data=data)

    def health_check(self) -> Dict[str, Any]:
        """
        Check API health status

        Returns:
            Dict containing health status

        Example:
            >>> health = client.health_check()
            >>> print(health["status"])
            healthy
        """

        return self._make_request("GET", "/health")

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session"""
        self.session.close()