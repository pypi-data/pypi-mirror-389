"""
Integration tests for the partcl library API (programmatic interface).

These tests call the actual timing analysis API without mocks.
Requires a local Docker server running at localhost:8000.

Run with: pytest tests/test_integration.py -v
"""

from pathlib import Path

import pytest

import partcl
from partcl import timing


# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"
TEST_VERILOG = TEST_DATA_DIR / "test_data.v"
TEST_SDC = TEST_DATA_DIR / "test_constraints.sdc"
TEST_LIB = TEST_DATA_DIR / "sky130_fd_sc_hd__tt_025C_1v80.lib"


def check_server_available():
    """Check if the local Docker server is available."""
    import socket
    try:
        with socket.create_connection(("localhost", 8000), timeout=2):
            return True
    except (socket.timeout, socket.error, ConnectionRefusedError):
        return False


@pytest.fixture(scope="session", autouse=True)
def verify_server():
    """Verify that the Docker server is running before tests."""
    if not check_server_available():
        pytest.fail(
            "Local Docker server is not available at localhost:8000. "
            "Please start the server before running these integration tests."
        )


@pytest.fixture
def test_files():
    """Use real test data files from tests/data directory."""
    if not TEST_VERILOG.exists():
        pytest.fail(f"Test data file not found: {TEST_VERILOG}")
    if not TEST_SDC.exists():
        pytest.fail(f"Test data file not found: {TEST_SDC}")
    if not TEST_LIB.exists():
        pytest.fail(f"Test data file not found: {TEST_LIB}")

    return {
        "verilog": TEST_VERILOG,
        "sdc": TEST_SDC,
        "lib": TEST_LIB,
    }


def test_import_partcl():
    """Test that partcl can be imported and has expected attributes."""
    assert hasattr(partcl, "timing")
    assert hasattr(partcl, "APIClient")
    assert hasattr(partcl, "TimingResult")
    assert hasattr(partcl, "__version__")
    assert callable(partcl.timing)


def test_timing_function_exists():
    """Test that timing function is accessible."""
    assert timing is not None
    assert callable(timing)


def test_timing_basic_local_mode(test_files):
    """Test basic timing analysis in local mode with real API calls."""
    # Call the actual timing API
    result = timing(
        design=test_files["verilog"],
        sdc=test_files["sdc"],
        lib=test_files["lib"],
        local=True,
    )

    # Check basic response structure
    assert isinstance(result, dict)
    assert "success" in result
    assert result["success"] is True

    # Check required fields
    assert "wns" in result
    assert "tns" in result
    assert "num_violations" in result
    assert "total_endpoints" in result

    # Check types
    assert isinstance(result["wns"], (int, float))
    assert isinstance(result["tns"], (int, float))
    assert isinstance(result["num_violations"], int)
    assert isinstance(result["total_endpoints"], int)


def test_timing_consistency_checks(test_files):
    """Test that timing results are internally consistent."""
    result = timing(
        design=test_files["verilog"],
        sdc=test_files["sdc"],
        lib=test_files["lib"],
        local=True,
    )

    # Consistency checks
    # 1. TNS should be non-negative (or 0 if no violations)
    assert result["tns"] >= 0, "TNS should be >= 0"

    # 2. WNS should be non-negative
    assert result["wns"] >= 0, "WNS should be >= 0"

    # 3. Number of violations should be non-negative
    assert result["num_violations"] >= 0, "num_violations should be >= 0"

    # 4. Total endpoints should be positive
    assert result["total_endpoints"] > 0, "total_endpoints should be > 0"

    # 5. If there are violations, WNS should be positive (negative slack)
    if result["num_violations"] > 0:
        assert result["wns"] > 0, "If violations exist, WNS should be > 0"
        assert result["tns"] > 0, "If violations exist, TNS should be > 0"
        # TNS should be at least as large as WNS (it's the sum of all negative slacks)
        assert result["tns"] >= result["wns"], "TNS should be >= WNS"

    # 6. If no violations, both WNS and TNS should be 0
    if result["num_violations"] == 0:
        assert result["wns"] == 0, "If no violations, WNS should be 0"
        assert result["tns"] == 0, "If no violations, TNS should be 0"


def test_timing_with_path_objects(test_files):
    """Test timing function accepts Path objects."""
    result = timing(
        design=test_files["verilog"],  # Already Path objects
        sdc=test_files["sdc"],
        lib=test_files["lib"],
        local=True,
    )

    assert result["success"] is True
    assert "wns" in result


def test_timing_with_string_paths(test_files):
    """Test timing function accepts string paths."""
    result = timing(
        design=str(test_files["verilog"]),
        sdc=str(test_files["sdc"]),
        lib=str(test_files["lib"]),
        local=True,
    )

    assert result["success"] is True
    assert "wns" in result


def test_timing_validates_file_existence():
    """Test that timing function validates file existence."""
    with pytest.raises(FileNotFoundError):
        timing(
            design=Path("nonexistent.v"),
            sdc=Path("nonexistent.sdc"),
            lib=Path("nonexistent.lib"),
            local=True,
        )






def test_timing_timeout_parameter(test_files):
    """Test that timeout parameter is accepted."""
    # Just verify the parameter is accepted, don't wait for timeout
    result = timing(
        design=test_files["verilog"],
        sdc=test_files["sdc"],
        lib=test_files["lib"],
        local=True,
        timeout=300,  # 5 minute timeout
    )

    assert result["success"] is True


def test_timing_deployment_info(test_files):
    """Test that result contains deployment information."""
    result = timing(
        design=test_files["verilog"],
        sdc=test_files["sdc"],
        lib=test_files["lib"],
        local=True,
    )

    # Check for deployment info (may or may not be present)
    # This is informational, not required
    if "deployment" in result:
        assert isinstance(result["deployment"], str)

    if "gpu_available" in result:
        assert isinstance(result["gpu_available"], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
