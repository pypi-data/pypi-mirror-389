"""
API client for communicating with Partcl timing analysis servers.
"""

import json
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel, Field


class TimingResult(BaseModel):
    """Response model for timing analysis results."""

    success: bool
    wns: Optional[float] = Field(None, description="Worst Negative Slack in ps")
    tns: Optional[float] = Field(None, description="Total Negative Slack in ps")
    num_violations: Optional[int] = Field(None, description="Number of timing violations")
    total_endpoints: Optional[int] = Field(None, description="Total timing endpoints")
    error: Optional[str] = Field(None, description="Error message if analysis failed")
    error_type: Optional[str] = Field(None, description="Type of error")
    deployment: Optional[str] = Field(None, description="Deployment type (local/modal)")
    gpu_available: Optional[bool] = Field(None, description="Whether GPU was available")


class APIClient:
    """Client for interacting with Partcl API servers."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: Optional[str] = None,
        timeout: int = 300,
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the API server
            token: Optional JWT authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout

        # Create httpx client with default headers
        self.headers = {
            "User-Agent": "partcl-cli/0.1.0",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def health_check(self) -> Dict[str, Any]:
        """
        Check if the server is healthy.

        Returns:
            Health check response

        Raises:
            httpx.RequestError: If the request fails
            httpx.HTTPStatusError: If the server returns an error
        """
        with httpx.Client(timeout=10) as client:
            response = client.get(f"{self.base_url}/health", headers=self.headers)
            response.raise_for_status()
            return response.json()

    def check_local_mode(self) -> bool:
        """
        Check if the server supports local mode (path-based file access).

        Returns:
            True if server supports local mode, False otherwise

        Raises:
            httpx.RequestError: If the request fails
        """
        try:
            health = self.health_check()
            mode = health.get("mode", "remote")
            features = health.get("features", {})

            # Server supports local mode if it reports mode as "local"
            # or if it has the "local_mode" feature enabled
            return mode == "local" or features.get("local_mode", False)
        except Exception:
            # If health check fails, assume remote mode
            return False

    def analyze_timing(
        self,
        verilog_content: bytes,
        lib_content: bytes,
        sdc_content: bytes,
        verilog_filename: str = "design.v",
        lib_filename: str = "library.lib",
        sdc_filename: str = "constraints.sdc",
    ) -> Dict[str, Any]:
        """
        Run timing analysis on the provided files.

        Args:
            verilog_content: Content of the Verilog file
            lib_content: Content of the Liberty library file
            sdc_content: Content of the SDC constraints file
            verilog_filename: Name of the Verilog file (for server logs)
            lib_filename: Name of the Liberty file (for server logs)
            sdc_filename: Name of the SDC file (for server logs)

        Returns:
            Timing analysis results

        Raises:
            httpx.RequestError: If the request fails
            httpx.HTTPStatusError: If the server returns an error
        """
        # Prepare multipart form data
        files = {
            "design_file": (verilog_filename, verilog_content, "application/octet-stream"),
            "lib_file": (lib_filename, lib_content, "application/octet-stream"),
            "sdc_file": (sdc_filename, sdc_content, "application/octet-stream"),
        }

        # Make the request
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/analyze",
                files=files,
                headers=self.headers,
            )

            # Handle authentication errors specially
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Please check your token or use --local mode."
                )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds.")

            # Handle other HTTP errors
            if response.status_code >= 400:
                try:
                    error_detail = response.json().get("detail", str(response.text))
                except:
                    error_detail = response.text
                raise APIError(f"Server error ({response.status_code}): {error_detail}")

            # Parse and return the response
            try:
                return response.json()
            except json.JSONDecodeError:
                raise APIError(f"Invalid response from server: {response.text[:200]}")

    def analyze_timing_local(
        self,
        verilog_path: str,
        lib_path: str,
        sdc_path: str,
    ) -> Dict[str, Any]:
        """
        Run timing analysis using local mode (path-based file access).

        This method sends file paths instead of file content to the server.
        The server must have access to these paths via volume mounts.

        Args:
            verilog_path: Absolute path to the Verilog file
            lib_path: Absolute path to the Liberty library file
            sdc_path: Absolute path to the SDC constraints file

        Returns:
            Timing analysis results

        Raises:
            httpx.RequestError: If the request fails
            httpx.HTTPStatusError: If the server returns an error
            APIError: If paths are not absolute
        """
        # Validate that paths are absolute
        from pathlib import Path

        verilog_p = Path(verilog_path)
        lib_p = Path(lib_path)
        sdc_p = Path(sdc_path)

        if not verilog_p.is_absolute():
            raise APIError(f"Verilog path must be absolute: {verilog_path}")
        if not lib_p.is_absolute():
            raise APIError(f"Library path must be absolute: {lib_path}")
        if not sdc_p.is_absolute():
            raise APIError(f"SDC path must be absolute: {sdc_path}")

        # Validate that files exist
        if not verilog_p.exists():
            raise APIError(f"Verilog file not found: {verilog_path}")
        if not lib_p.exists():
            raise APIError(f"Library file not found: {lib_path}")
        if not sdc_p.exists():
            raise APIError(f"SDC file not found: {sdc_path}")

        # Prepare JSON payload with file paths
        # FastAPI expects nested structure when there are multiple parameters
        payload = {
            "analysis_request": {
                "verilog_path": str(verilog_p.resolve()),
                "lib_path": str(lib_p.resolve()),
                "sdc_path": str(sdc_p.resolve()),
            }
        }

        # Make the request
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/analyze-local",
                json=payload,
                headers=self.headers,
            )

            # Handle authentication errors specially
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Please check your token or use --local mode."
                )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds.")

            # Handle other HTTP errors
            if response.status_code >= 400:
                try:
                    error_detail = response.json().get("detail", str(response.text))
                except:
                    error_detail = response.text
                raise APIError(f"Server error ({response.status_code}): {error_detail}")

            # Parse and return the response
            try:
                return response.json()
            except json.JSONDecodeError:
                raise APIError(f"Invalid response from server: {response.text[:200]}")

    def analyze_timing_r2(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run timing analysis using R2 cloud storage for large files.

        This method is used when files are uploaded to R2 storage instead
        of being sent directly in the request.

        Args:
            payload: Dictionary containing either R2 keys or file content:
                - design: R2 key or file content
                - sdc: R2 key or file content
                - lib: R2 key or file content
                - use_r2: Boolean flag indicating R2 usage

        Returns:
            Timing analysis results

        Raises:
            httpx.RequestError: If the request fails
            httpx.HTTPStatusError: If the server returns an error
        """
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/analyze/r2",
                json=payload,
                headers=self.headers,
            )

            # Handle authentication errors specially
            if response.status_code == 401:
                raise AuthenticationError(
                    "Authentication failed. Please check your token or use --local mode."
                )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise RateLimitError(f"Rate limit exceeded. Retry after {retry_after} seconds.")

            # Handle other HTTP errors
            if response.status_code >= 400:
                try:
                    error_detail = response.json().get("detail", str(response.text))
                except:
                    error_detail = response.text
                raise APIError(f"Server error ({response.status_code}): {error_detail}")

            # Parse and return the response
            try:
                return response.json()
            except json.JSONDecodeError:
                raise APIError(f"Invalid response from server: {response.text[:200]}")

    def debug_upload(
        self,
        verilog_content: bytes,
        lib_content: bytes,
        sdc_content: bytes,
        verilog_filename: str = "design.v",
        lib_filename: str = "library.lib",
        sdc_filename: str = "constraints.sdc",
    ) -> Dict[str, Any]:
        """
        Test file upload without running analysis (debug endpoint).

        Args:
            verilog_content: Content of the Verilog file
            lib_content: Content of the Liberty library file
            sdc_content: Content of the SDC file
            verilog_filename: Name of the Verilog file
            lib_filename: Name of the Liberty file
            sdc_filename: Name of the SDC file

        Returns:
            Debug information including file checksums

        Raises:
            httpx.RequestError: If the request fails
            httpx.HTTPStatusError: If the server returns an error
        """
        # Prepare multipart form data
        files = {
            "design_file": (verilog_filename, verilog_content, "application/octet-stream"),
            "lib_file": (lib_filename, lib_content, "application/octet-stream"),
            "sdc_file": (sdc_filename, sdc_content, "application/octet-stream"),
        }

        # Make the request
        with httpx.Client(timeout=30) as client:
            response = client.post(
                f"{self.base_url}/debug",
                files=files,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()


class APIError(Exception):
    """Base exception for API errors."""

    pass


class AuthenticationError(APIError):
    """Exception raised for authentication failures."""

    pass


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded."""

    pass