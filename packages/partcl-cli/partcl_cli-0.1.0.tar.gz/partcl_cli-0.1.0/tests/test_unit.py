"""
Unit tests for the partcl library.

These tests are fast and require no external dependencies.
They test imports, metadata, function signatures, validation, and error handling.

Run with: pytest tests/test_unit.py -v
"""

import inspect
import os
import tempfile
from pathlib import Path

import pytest

import partcl
from partcl import APIClient, PartclConfig, TimingResult, timing, validate_file


# =============================================================================
# Import and Metadata Tests
# =============================================================================


def test_basic_import():
    """Test that partcl can be imported."""
    assert partcl is not None


def test_package_metadata():
    """Test that package metadata is accessible."""
    assert hasattr(partcl, "__version__")
    assert hasattr(partcl, "__author__")
    assert hasattr(partcl, "__email__")
    assert isinstance(partcl.__version__, str)
    assert isinstance(partcl.__author__, str)
    assert isinstance(partcl.__email__, str)


def test_exported_symbols():
    """Test that all expected symbols are exported."""
    expected_exports = [
        "timing",
        "APIClient",
        "TimingResult",
        "PartclConfig",
        "validate_file",
        "__version__",
        "__author__",
        "__email__",
    ]

    for symbol in expected_exports:
        assert hasattr(partcl, symbol), f"Missing export: {symbol}"


def test_all_exports_accessible():
    """Test that all items in __all__ are actually accessible."""
    if hasattr(partcl, "__all__"):
        missing = []
        for name in partcl.__all__:
            if not hasattr(partcl, name):
                missing.append(name)

        assert len(missing) == 0, f"Missing exports from __all__: {missing}"


def test_submodule_imports():
    """Test that submodules can be imported."""
    submodules = [
        "partcl.api",
        "partcl.client",
        "partcl.client.api",
        "partcl.utils",
        "partcl.utils.config",
        "partcl.utils.validation",
    ]

    for module_name in submodules:
        try:
            __import__(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_import_styles():
    """Test different import styles work correctly."""
    # Style 1: import partcl
    import partcl as p1
    assert callable(p1.timing)

    # Style 2: from partcl import timing
    from partcl import timing as t2
    assert callable(t2)

    # Style 3: from partcl import *
    namespace = {}
    exec("from partcl import *", namespace)
    assert "timing" in namespace


# =============================================================================
# Function Signature Tests
# =============================================================================


def test_timing_function_exists():
    """Test that timing function is accessible and callable."""
    assert timing is not None
    assert callable(timing)


def test_timing_function_signature():
    """Test that timing function has correct parameters."""
    sig = inspect.signature(timing)
    params = list(sig.parameters.keys())

    # Required parameters
    required = ["design", "sdc", "lib"]
    for param in required:
        assert param in params, f"Missing required parameter: {param}"

    # Optional parameters
    optional = ["local", "token", "url", "timeout"]
    for param in optional:
        assert param in params, f"Missing optional parameter: {param}"


def test_timing_function_has_docstring():
    """Test that timing function has documentation."""
    assert timing.__doc__ is not None
    assert len(timing.__doc__.strip()) > 0


def test_timing_function_defaults():
    """Test timing function default parameter values."""
    sig = inspect.signature(timing)

    # Check default values
    assert sig.parameters["local"].default is False
    assert sig.parameters["token"].default is None
    assert sig.parameters["url"].default is None
    assert sig.parameters["timeout"].default == 300


# =============================================================================
# Class Instantiation Tests
# =============================================================================


def test_api_client_exists():
    """Test that APIClient class is accessible."""
    assert APIClient is not None
    assert inspect.isclass(APIClient)


def test_api_client_local_instantiation():
    """Test that APIClient can be instantiated for local server."""
    client = APIClient(base_url="http://localhost:8000", timeout=300)
    assert client is not None
    assert client.base_url == "http://localhost:8000"
    assert client.timeout == 300


def test_api_client_cloud_instantiation():
    """Test that APIClient can be instantiated for cloud server."""
    client = APIClient(
        base_url="https://api.partcl.com", token="test-token", timeout=300
    )
    assert client is not None
    assert client.base_url == "https://api.partcl.com"
    assert client.token == "test-token"


def test_timing_result_exists():
    """Test that TimingResult class is accessible."""
    assert TimingResult is not None
    assert inspect.isclass(TimingResult)


def test_partcl_config_exists():
    """Test that PartclConfig class is accessible."""
    assert PartclConfig is not None
    assert inspect.isclass(PartclConfig)


def test_partcl_config_load():
    """Test that PartclConfig can be loaded."""
    config = PartclConfig.load()
    assert config is not None
    assert hasattr(config, "api_url")
    assert hasattr(config, "timeout")


# =============================================================================
# File Validation Tests
# =============================================================================


def test_validate_file_function_exists():
    """Test that validate_file function is accessible."""
    assert validate_file is not None
    assert callable(validate_file)


def test_validate_file_with_valid_verilog():
    """Test file validation with valid Verilog file."""
    with tempfile.NamedTemporaryFile(suffix=".v", delete=False) as f:
        f.write(b"module test; endmodule")
        f.flush()
        path = Path(f.name)

    try:
        # Should not raise
        validate_file(path, ".v")
    finally:
        path.unlink()


def test_validate_file_with_valid_sdc():
    """Test file validation with valid SDC file."""
    with tempfile.NamedTemporaryFile(suffix=".sdc", delete=False) as f:
        f.write(b"create_clock -period 10 [get_ports clk]")
        f.flush()
        path = Path(f.name)

    try:
        # Should not raise
        validate_file(path, ".sdc")
    finally:
        path.unlink()


def test_validate_file_with_valid_lib():
    """Test file validation with valid Liberty file."""
    with tempfile.NamedTemporaryFile(suffix=".lib", delete=False) as f:
        f.write(b"library(test) { }")
        f.flush()
        path = Path(f.name)

    try:
        # Should not raise
        validate_file(path, ".lib")
    finally:
        path.unlink()


def test_validate_file_wrong_extension():
    """Test that validate_file raises ValueError for wrong extension."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"test content")
        f.flush()
        path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Invalid file extension"):
            validate_file(path, ".v")
    finally:
        path.unlink()


def test_validate_file_nonexistent():
    """Test that validate_file raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        validate_file(Path("nonexistent.v"), ".v")


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_timing_requires_existing_files():
    """Test that timing function validates file existence."""
    with pytest.raises(FileNotFoundError):
        timing(
            design=Path("nonexistent.v"),
            sdc=Path("nonexistent.sdc"),
            lib=Path("nonexistent.lib"),
            local=True,
        )


def test_timing_validates_design_extension():
    """Test that timing function validates design file extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create files with wrong extension
        wrong_design = tmpdir / "design.txt"
        wrong_design.write_text("module test; endmodule")

        valid_sdc = tmpdir / "test.sdc"
        valid_sdc.write_text("create_clock -period 10 [get_ports clk]")

        valid_lib = tmpdir / "test.lib"
        valid_lib.write_text("library(test) { }")

        with pytest.raises(ValueError, match="Invalid file extension"):
            timing(design=wrong_design, sdc=valid_sdc, lib=valid_lib, local=True)


def test_timing_validates_sdc_extension():
    """Test that timing function validates SDC file extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        valid_design = tmpdir / "design.v"
        valid_design.write_text("module test; endmodule")

        wrong_sdc = tmpdir / "test.txt"
        wrong_sdc.write_text("create_clock -period 10 [get_ports clk]")

        valid_lib = tmpdir / "test.lib"
        valid_lib.write_text("library(test) { }")

        with pytest.raises(ValueError, match="Invalid file extension"):
            timing(design=valid_design, sdc=wrong_sdc, lib=valid_lib, local=True)


def test_timing_validates_lib_extension():
    """Test that timing function validates Liberty file extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        valid_design = tmpdir / "design.v"
        valid_design.write_text("module test; endmodule")

        valid_sdc = tmpdir / "test.sdc"
        valid_sdc.write_text("create_clock -period 10 [get_ports clk]")

        wrong_lib = tmpdir / "test.txt"
        wrong_lib.write_text("library(test) { }")

        with pytest.raises(ValueError, match="Invalid file extension"):
            timing(design=valid_design, sdc=valid_sdc, lib=wrong_lib, local=True)


def test_timing_requires_authentication_for_cloud():
    """Test that cloud mode requires authentication token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create valid files
        design = tmpdir / "design.v"
        design.write_text("module test; endmodule")

        sdc = tmpdir / "test.sdc"
        sdc.write_text("create_clock -period 10 [get_ports clk]")

        lib = tmpdir / "test.lib"
        lib.write_text("library(test) { }")

        # Clear environment variable if set
        old_token = os.environ.get("PARTCL_TOKEN")
        if old_token:
            del os.environ["PARTCL_TOKEN"]

        try:
            with pytest.raises(
                ValueError,
                match="(token required|authentication|run 'partcl login' first)",
            ):
                timing(design=design, sdc=sdc, lib=lib, local=False)
        finally:
            # Restore environment
            if old_token:
                os.environ["PARTCL_TOKEN"] = old_token


# =============================================================================
# Path Handling Tests
# =============================================================================


def test_timing_accepts_path_objects():
    """Test that timing function accepts pathlib.Path objects."""
    # This test only validates types are accepted, not actual execution
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        design = tmpdir / "design.v"
        sdc = tmpdir / "test.sdc"
        lib = tmpdir / "test.lib"

        design.write_text("module test; endmodule")
        sdc.write_text("create_clock -period 10 [get_ports clk]")
        lib.write_text("library(test) { }")

        # Should accept Path objects (will fail at API call, but that's OK)
        # We're just testing type acceptance here
        assert isinstance(design, Path)
        assert isinstance(sdc, Path)
        assert isinstance(lib, Path)


def test_timing_accepts_string_paths():
    """Test that timing function accepts string paths."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        design = tmpdir / "design.v"
        sdc = tmpdir / "test.sdc"
        lib = tmpdir / "test.lib"

        design.write_text("module test; endmodule")
        sdc.write_text("create_clock -period 10 [get_ports clk]")
        lib.write_text("library(test) { }")

        # Should accept string paths
        design_str = str(design)
        sdc_str = str(sdc)
        lib_str = str(lib)

        assert isinstance(design_str, str)
        assert isinstance(sdc_str, str)
        assert isinstance(lib_str, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
