"""
High-level Python API for Partcl EDA tools.

This module provides a convenient Python interface for timing analysis
that can be imported and used programmatically.
"""

import os
from pathlib import Path
from typing import Dict, Optional, Union

from dotenv import load_dotenv

from partcl.client.api import APIClient, TimingResult
from partcl.client.storage import prepare_file_upload
from partcl.utils.validation import validate_file


def _load_auth_token() -> Optional[str]:
    """
    Load authentication token from saved configuration.

    Checks for token in the following order:
    1. PARTCL_TOKEN environment variable (already loaded)
    2. ~/.partcl.env file (saved by `partcl login`)
    3. ./.partcl.env file (project-specific config)

    Returns:
        JWT token if found, None otherwise
    """
    # First check if already in environment
    token = os.getenv("PARTCL_TOKEN")
    if token:
        return token

    # Load from ~/.partcl.env (saved by partcl login)
    home_config = Path.home() / ".partcl.env"
    if home_config.exists():
        load_dotenv(home_config)
        token = os.getenv("PARTCL_TOKEN")
        if token:
            return token

    # Load from ./.partcl.env (project config)
    project_config = Path(".partcl.env")
    if project_config.exists():
        load_dotenv(project_config)
        token = os.getenv("PARTCL_TOKEN")
        if token:
            return token

    return None


def timing(
    design: Union[str, Path],
    sdc: Union[str, Path],
    lib: Union[str, Path],
    local: bool = False,
    token: Optional[str] = None,
    url: Optional[str] = None,
    timeout: int = 300,
) -> Dict:
    """
    Run timing analysis on a digital design.

    This is the main programmatic interface for Partcl timing analysis.
    It accepts file paths and automatically handles validation, file upload
    (using R2 for large files in remote mode), and result retrieval.

    Authentication:
        For cloud mode, you must first authenticate using the CLI:
            $ partcl login

        This saves your token to ~/.partcl.env, which is automatically loaded.
        You can also pass a token explicitly or set the PARTCL_TOKEN environment variable.

    Args:
        design: Path to Verilog design file (.v)
        sdc: Path to Synopsys Design Constraints file (.sdc)
        lib: Path to Liberty timing library file (.lib)
        local: If True, use local Docker server; if False, use cloud (default: False)
        token: JWT authentication token for cloud service (optional)
               If not provided, automatically loads from:
               1. PARTCL_TOKEN environment variable
               2. ~/.partcl.env (saved by `partcl login`)
               3. ./.partcl.env (project-specific config)
        url: Custom API base URL (optional, reads from PARTCL_API_URL env var)
        timeout: Request timeout in seconds (default: 300)

    Returns:
        Dictionary containing timing analysis results with keys:
        - success (bool): Whether analysis succeeded
        - wns (float): Worst Negative Slack in picoseconds
        - tns (float): Total Negative Slack in picoseconds
        - num_violations (int): Number of timing violations
        - total_endpoints (int): Total number of timing endpoints
        - deployment (str): Deployment type ("local" or "modal")
        - gpu_available (bool): Whether GPU acceleration was available

    Raises:
        ValueError: If file validation fails or authentication token is missing for cloud mode
        FileNotFoundError: If any input file doesn't exist
        IOError: If file cannot be read
        APIError: If API request fails
        AuthenticationError: If authentication fails (cloud mode)
        RateLimitError: If rate limit is exceeded (cloud mode)

    Examples:
        >>> import partcl
        >>>
        >>> # First, authenticate (one-time setup for cloud mode)
        >>> # Run in terminal: partcl login
        >>>
        >>> # Local mode (using Docker) - no authentication needed
        >>> result = partcl.timing(
        ...     design="design.v",
        ...     sdc="constraints.sdc",
        ...     lib="timing.lib",
        ...     local=True
        ... )
        >>>
        >>> # Cloud mode - automatically uses token from `partcl login`
        >>> result = partcl.timing(
        ...     design="design.v",
        ...     sdc="constraints.sdc",
        ...     lib="timing.lib"
        ... )
        >>>
        >>> # Cloud mode with explicit token (optional)
        >>> result = partcl.timing(
        ...     design="design.v",
        ...     sdc="constraints.sdc",
        ...     lib="timing.lib",
        ...     token="your-jwt-token"
        ... )
        >>>
        >>> # Check results
        >>> print(f"WNS: {result['wns']} ps")
        >>> print(f"Violations: {result['num_violations']}")
        >>>
        >>> if result['num_violations'] == 0:
        ...     print("Design meets timing!")
        ... else:
        ...     print(f"Design has {result['num_violations']} violations")
    """
    # Convert to Path objects
    design_path = Path(design)
    sdc_path = Path(sdc)
    lib_path = Path(lib)

    # Validate input files
    validate_file(design_path, ".v")
    validate_file(sdc_path, ".sdc")
    validate_file(lib_path, ".lib")

    # Get token from saved config if not provided
    if token is None:
        token = _load_auth_token()

    # Determine API URL
    if url:
        api_url = url
    elif local:
        api_url = "http://localhost:8000"
    else:
        # Default cloud URL
        api_url = os.getenv(
            "PARTCL_API_URL",
            "https://partcl--boson-eda-processor-web.modal.run"
        )

    # Check authentication for cloud mode
    if not local and not token:
        raise ValueError(
            "Authentication token required for cloud mode. "
            "Please run 'partcl login' first, or set PARTCL_TOKEN environment variable, "
            "or pass token parameter explicitly."
        )

    # Create API client
    client = APIClient(base_url=api_url, token=token, timeout=timeout)

    # In local mode, pass file paths directly
    # In remote mode, use smart upload logic (R2 for large files)
    if local:
        # Local mode: read files and upload directly
        verilog_content = design_path.read_bytes()
        lib_content = lib_path.read_bytes()
        sdc_content = sdc_path.read_bytes()

        result = client.analyze_timing(
            verilog_content=verilog_content,
            lib_content=lib_content,
            sdc_content=sdc_content,
            verilog_filename=design_path.name,
            lib_filename=lib_path.name,
            sdc_filename=sdc_path.name,
        )
    else:
        # Remote mode: use R2 for large files
        design_r2, design_content = prepare_file_upload(
            design_path, "design", api_url, token, timeout
        )
        sdc_r2, sdc_content = prepare_file_upload(
            sdc_path, "sdc", api_url, token, timeout
        )
        lib_r2, lib_content = prepare_file_upload(
            lib_path, "lib", api_url, token, timeout
        )

        # If any files were uploaded to R2, use the R2 endpoint
        if design_r2 or sdc_r2 or lib_r2:
            # Create payload with R2 keys or content
            payload = {
                "design": design_r2 if design_r2 else design_content.decode('latin-1'),
                "sdc": sdc_r2 if sdc_r2 else sdc_content.decode('latin-1'),
                "lib": lib_r2 if lib_r2 else lib_content.decode('latin-1'),
                "use_r2": True,
            }
            result = client.analyze_timing_r2(payload)
        else:
            # All files are small, use direct upload
            result = client.analyze_timing(
                verilog_content=design_content,
                lib_content=lib_content,
                sdc_content=sdc_content,
                verilog_filename=design_path.name,
                lib_filename=lib_path.name,
                sdc_filename=sdc_path.name,
            )

    return result


__all__ = ["timing"]
