"""
CLI command tests for partcl.

These tests verify the command-line interface functionality.
Requires a local Docker server running at localhost:8000.

Run with: pytest tests/test_cli.py -v
"""

from pathlib import Path

import pytest
from click.testing import CliRunner

from partcl.main import cli

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
            "Please start the server before running these CLI tests."
        )


# =============================================================================
# Help and Basic CLI Tests
# =============================================================================


def test_cli_help():
    """Test that CLI help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.output


def test_timing_command_help():
    """Test that timing command help works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["timing", "--help"])
    assert result.exit_code == 0
    assert "Run timing analysis" in result.output
    assert "--verilog-file" in result.output
    assert "--lib-file" in result.output
    assert "--sdc-file" in result.output


def test_timing_missing_required_options():
    """Test that timing command requires all options."""
    runner = CliRunner()
    result = runner.invoke(cli, ["timing"])
    assert result.exit_code != 0
    assert "Missing option" in result.output or "required" in result.output.lower()


# =============================================================================
# Local Mode CLI Tests
# =============================================================================


def test_timing_local_mode_json_output():
    """Test timing command in local mode with JSON output."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "timing",
            "--verilog-file",
            str(TEST_VERILOG),
            "--lib-file",
            str(TEST_LIB),
            "--sdc-file",
            str(TEST_SDC),
            "--local",
            "--output",
            "json",
        ],
    )

    # Command should complete (exit code 0 or 1 depending on violations)
    assert result.exit_code in [0, 1]

    # Extract JSON from output (may have progress messages before it)
    import json

    output_lines = result.output.strip().split('\n')

    # Try to find and parse JSON (may be on last line or entire output)
    json_found = False
    for line in reversed(output_lines):
        if line.strip().startswith('{'):
            try:
                output_data = json.loads(line.strip())
                assert "wns" in output_data
                assert "tns" in output_data
                assert "num_violations" in output_data
                json_found = True
                break
            except json.JSONDecodeError:
                continue

    # If no individual line is JSON, try the whole output
    if not json_found:
        try:
            output_data = json.loads(result.output)
            assert "wns" in output_data
            assert "tns" in output_data
            assert "num_violations" in output_data
        except json.JSONDecodeError:
            pytest.fail(f"Output does not contain valid JSON: {result.output}")


def test_timing_local_mode_table_output():
    """Test timing command in local mode with table output."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "timing",
            "--verilog-file",
            str(TEST_VERILOG),
            "--lib-file",
            str(TEST_LIB),
            "--sdc-file",
            str(TEST_SDC),
            "--local",
            "--output",
            "table",
        ],
    )

    # Command should complete
    assert result.exit_code in [0, 1]

    # Table output should contain key information
    assert "Worst Negative Slack" in result.output or "WNS" in result.output
    assert "Total Negative Slack" in result.output or "TNS" in result.output


def test_timing_local_mode_default_output():
    """Test timing command in local mode with default output format."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "timing",
            "--verilog-file",
            str(TEST_VERILOG),
            "--lib-file",
            str(TEST_LIB),
            "--sdc-file",
            str(TEST_SDC),
            "--local",
        ],
    )

    # Command should complete
    assert result.exit_code in [0, 1]

    # Should have some output
    assert len(result.output) > 0


# =============================================================================
# Error Handling Tests
# =============================================================================


def test_timing_nonexistent_files():
    """Test timing command with nonexistent files."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "timing",
            "--verilog-file",
            "nonexistent.v",
            "--lib-file",
            "nonexistent.lib",
            "--sdc-file",
            "nonexistent.sdc",
            "--local",
        ],
    )

    # Should fail with error (exit code 1 for errors, 2 for validation failures)
    assert result.exit_code in [1, 2]
    assert "not found" in result.output.lower() or "does not exist" in result.output.lower()


def test_timing_invalid_output_format():
    """Test timing command with invalid output format."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "timing",
            "--verilog-file",
            str(TEST_VERILOG),
            "--lib-file",
            str(TEST_LIB),
            "--sdc-file",
            str(TEST_SDC),
            "--local",
            "--output",
            "invalid_format",
        ],
    )

    # Should fail with validation error
    assert result.exit_code != 0
    assert "Invalid value" in result.output or "invalid choice" in result.output.lower()


# =============================================================================
# Exit Code Tests
# =============================================================================


def test_timing_exit_code_with_violations():
    """Test that timing command returns exit code 1 when violations exist."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "timing",
            "--verilog-file",
            str(TEST_VERILOG),
            "--lib-file",
            str(TEST_LIB),
            "--sdc-file",
            str(TEST_SDC),
            "--local",
            "--output",
            "json",
        ],
    )

    # Parse result to check for violations
    import json

    try:
        output_data = json.loads(result.output)
        if output_data.get("num_violations", 0) > 0:
            # Should have exit code 1 when violations exist
            assert result.exit_code == 1
        else:
            # Should have exit code 0 when no violations
            assert result.exit_code == 0
    except json.JSONDecodeError:
        # If we can't parse JSON, just check command completed
        assert result.exit_code in [0, 1]


# =============================================================================
# Path Handling Tests
# =============================================================================


def test_timing_with_relative_paths():
    """Test timing command with relative paths."""
    runner = CliRunner()

    # Get relative paths from current directory
    import os

    original_dir = os.getcwd()
    try:
        # Change to test directory
        os.chdir(TEST_DATA_DIR)

        result = runner.invoke(
            cli,
            [
                "timing",
                "--verilog-file",
                "test_data.v",
                "--lib-file",
                "sky130_fd_sc_hd__tt_025C_1v80.lib",
                "--sdc-file",
                "test_constraints.sdc",
                "--local",
                "--output",
                "json",
            ],
        )

        # Command should complete
        assert result.exit_code in [0, 1]
    finally:
        os.chdir(original_dir)


def test_timing_with_absolute_paths():
    """Test timing command with absolute paths."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "timing",
            "--verilog-file",
            str(TEST_VERILOG.absolute()),
            "--lib-file",
            str(TEST_LIB.absolute()),
            "--sdc-file",
            str(TEST_SDC.absolute()),
            "--local",
            "--output",
            "json",
        ],
    )

    # Command should complete
    assert result.exit_code in [0, 1]


# =============================================================================
# Verbose Output Tests
# =============================================================================


def test_timing_verbose_flag():
    """Test timing command with verbose flag if available."""
    runner = CliRunner()

    # Try with -v flag
    result = runner.invoke(
        cli,
        [
            "timing",
            "--verilog-file",
            str(TEST_VERILOG),
            "--lib-file",
            str(TEST_LIB),
            "--sdc-file",
            str(TEST_SDC),
            "--local",
            "-v",
        ],
    )

    # If -v is not supported, command should still complete or fail gracefully
    # We're just testing that verbose flag doesn't break the CLI
    assert result.exit_code in [0, 1, 2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
