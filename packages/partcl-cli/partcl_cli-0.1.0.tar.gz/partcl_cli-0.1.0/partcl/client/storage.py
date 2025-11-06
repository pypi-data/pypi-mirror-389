"""
Cloud storage (R2) utilities for large file uploads.

This module handles uploading large files to Cloudflare R2 storage
when they exceed a certain threshold, mimicking the logic from
the partcleda.github.io website.
"""

import os
from pathlib import Path
from typing import Optional, Tuple

import httpx


# File size threshold for R2 upload (10MB)
R2_UPLOAD_THRESHOLD = 10 * 1024 * 1024  # 10 MB in bytes


def should_use_r2(file_size: int) -> bool:
    """
    Determine if a file should be uploaded to R2 based on its size.

    Args:
        file_size: File size in bytes

    Returns:
        True if file should be uploaded to R2, False otherwise
    """
    return file_size > R2_UPLOAD_THRESHOLD


def get_file_size(file_path: Path) -> int:
    """
    Get the size of a file in bytes.

    Args:
        file_path: Path to the file

    Returns:
        File size in bytes
    """
    return file_path.stat().st_size


def upload_to_r2(
    file_path: Path,
    presigned_url: str,
    timeout: int = 300,
) -> bool:
    """
    Upload a file to R2 using a presigned URL.

    Args:
        file_path: Path to the file to upload
        presigned_url: Presigned URL from the API
        timeout: Upload timeout in seconds

    Returns:
        True if upload succeeded, False otherwise

    Raises:
        IOError: If file cannot be read
        httpx.HTTPError: If upload fails
    """
    with open(file_path, "rb") as f:
        file_content = f.read()

    response = httpx.put(
        presigned_url,
        content=file_content,
        timeout=timeout,
    )
    response.raise_for_status()

    return response.status_code == 200


def get_presigned_urls(
    api_base_url: str,
    token: Optional[str],
    filenames: dict[str, str],
    timeout: int = 30,
) -> dict[str, str]:
    """
    Request presigned URLs from the API for large file uploads.

    Args:
        api_base_url: Base URL of the API
        token: JWT authentication token (optional)
        filenames: Dict of file types to filenames (e.g., {"design": "design.v"})
        timeout: Request timeout in seconds

    Returns:
        Dict mapping file types to presigned URLs

    Raises:
        httpx.HTTPError: If API request fails
    """
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = httpx.post(
        f"{api_base_url}/api/storage/presigned-urls",
        json={"filenames": filenames},
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()

    data = response.json()
    return data.get("urls", {})


def prepare_file_upload(
    file_path: Path,
    file_type: str,
    api_base_url: str,
    token: Optional[str] = None,
    timeout: int = 300,
) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Prepare a file for upload, deciding whether to use R2 or direct upload.

    Args:
        file_path: Path to the file
        file_type: Type of file (e.g., "design", "lib", "sdc")
        api_base_url: Base URL of the API
        token: JWT authentication token (optional)
        timeout: Upload timeout in seconds

    Returns:
        Tuple of (r2_url, file_content):
        - If file should use R2: (r2_url, None)
        - If file should be uploaded directly: (None, file_content)

    Raises:
        IOError: If file cannot be read
        httpx.HTTPError: If R2 presigned URL request or upload fails
    """
    file_size = get_file_size(file_path)

    if should_use_r2(file_size):
        # Large file - upload to R2
        presigned_urls = get_presigned_urls(
            api_base_url=api_base_url,
            token=token,
            filenames={file_type: file_path.name},
            timeout=timeout,
        )

        presigned_url = presigned_urls.get(file_type)
        if not presigned_url:
            raise ValueError(f"No presigned URL received for {file_type}")

        # Upload to R2
        upload_to_r2(file_path, presigned_url, timeout=timeout)

        # Return R2 URL (key) to pass to API
        r2_key = f"{file_type}/{file_path.name}"
        return (r2_key, None)
    else:
        # Small file - read content for direct upload
        with open(file_path, "rb") as f:
            content = f.read()
        return (None, content)
