# Partcl

Python CLI and library for Partcl EDA tools, providing access to GPU-accelerated timing analysis and circuit optimization.

## Features

- **Timing Analysis**: Run static timing analysis on Verilog designs
- **Remote/Local Modes**: Connect to cloud (Modal) or local (Docker) servers
- **Dual Interface**: Use as CLI or import as Python library
- **Simple API**: Easy-to-use command-line and programmatic interfaces
- **Smart File Handling**: Automatic R2 cloud storage for large files
- **Progress Tracking**: Real-time progress updates for long-running analyses

## Installation

```bash
# Install from PyPI (when available)
pip install partcl

# Install from source
pip install ./partcl-cli

# Install with development dependencies
pip install -e "./partcl-cli[dev]"
```

## Quick Start

### Python Library Usage

```python
import partcl

# First-time setup for cloud mode: Authenticate once
# Run in terminal: partcl login
# This saves your token to ~/.partcl.env

# Local mode (using Docker) - no authentication needed
result = partcl.timing(
    design="design.v",
    sdc="constraints.sdc",
    lib="timing.lib",
    local=True
)

# Cloud mode - automatically uses token from `partcl login`
result = partcl.timing(
    design="design.v",
    sdc="constraints.sdc",
    lib="timing.lib"
)

# Check results
print(f"WNS: {result['wns']} ps")
print(f"Violations: {result['num_violations']}")

if result['num_violations'] == 0:
    print("Design meets timing!")
```

### Command-Line Interface

#### Remote Mode (Default - uses Modal cloud)

```bash
# Authenticate with your Google account (one-time setup)
partcl login

# Run timing analysis
partcl timing \
    --verilog-file design.v \
    --lib-file library.lib \
    --sdc-file constraints.sdc
```

#### Local Mode (Docker container)

```bash
# Start the local server (in another terminal)
docker run --rm -it --gpus all -p 8000:8000 -v /:/host:ro boson-release:latest

# Run timing analysis locally
partcl timing \
    --verilog-file design.v \
    --lib-file library.lib \
    --sdc-file constraints.sdc \
    --local
```

## Python API

### `partcl.timing()`

Run timing analysis programmatically using the Python API.

**Function Signature:**
```python
def timing(
    design: Union[str, Path],
    sdc: Union[str, Path],
    lib: Union[str, Path],
    local: bool = False,
    token: Optional[str] = None,
    url: Optional[str] = None,
    timeout: int = 300,
) -> Dict
```

**Parameters:**
- `design`: Path to Verilog design file (.v)
- `sdc`: Path to Synopsys Design Constraints file (.sdc)
- `lib`: Path to Liberty timing library file (.lib)
- `local`: If True, use local Docker server; if False, use cloud (default: False)
- `token`: JWT authentication token for cloud service (optional, reads from PARTCL_TOKEN env var)
- `url`: Custom API base URL (optional)
- `timeout`: Request timeout in seconds (default: 300)

**Returns:**
Dictionary containing:
- `success` (bool): Whether analysis succeeded
- `wns` (float): Worst Negative Slack in picoseconds
- `tns` (float): Total Negative Slack in picoseconds
- `num_violations` (int): Number of timing violations
- `total_endpoints` (int): Total number of timing endpoints
- `deployment` (str): Deployment type ("local" or "modal")
- `gpu_available` (bool): Whether GPU acceleration was available

**Examples:**

```python
import partcl

# First-time setup: Authenticate with partcl login
# $ partcl login
# (opens browser, saves token to ~/.partcl.env)

# Basic local usage (no authentication needed)
result = partcl.timing("design.v", "constraints.sdc", "timing.lib", local=True)

# Cloud usage - automatically loads token from `partcl login`
result = partcl.timing(
    design="design.v",
    sdc="constraints.sdc",
    lib="timing.lib"
)

# Cloud usage with explicit token (optional)
result = partcl.timing(
    design="design.v",
    sdc="constraints.sdc",
    lib="timing.lib",
    token="eyJhbGc..."
)

# Custom server
result = partcl.timing(
    design="design.v",
    sdc="constraints.sdc",
    lib="timing.lib",
    url="http://my-server:8000",
    token="my-token"
)

# Check for violations
if result['num_violations'] > 0:
    print(f"Design has {result['num_violations']} timing violations")
    print(f"Worst slack: {result['wns']} ps")
```

**File Handling:**
- **Local mode**: Files are read and sent directly to the Docker server
- **Remote mode**: Small files (<10MB) are uploaded directly; large files (>10MB) are uploaded to R2 cloud storage first for efficient handling

**Error Handling:**
```python
from partcl.client.api import APIError, AuthenticationError

try:
    result = partcl.timing("design.v", "constraints.sdc", "timing.lib")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except ValueError as e:
    print(f"Validation error: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except APIError as e:
    print(f"API error: {e}")
```

## CLI Commands

### `login` - Authenticate with Partcl

Authenticate using your Google account via OAuth. This is a one-time setup that saves your authentication token for future use.

```bash
partcl login
```

The command will:
1. Open your browser to sign in with Google
2. Authenticate via OAuth with your Google account
3. Redirect back to the CLI after successful authentication
4. Save your token automatically to `~/.partcl.env`

**Options:**
- `--no-browser`: Don't open browser automatically, display URL instead

**Note:** Your Google account must be linked to your Partcl account for authentication to work.

### `timing` - Run timing analysis

Analyze timing for a digital design using Verilog netlist, Liberty library, and SDC constraints.

**Options:**
- `--verilog-file PATH` (required): Path to Verilog design file (.v)
- `--lib-file PATH` (required): Path to Liberty timing library (.lib)
- `--sdc-file PATH` (required): Path to Synopsys Design Constraints (.sdc)
- `--local`: Use local server instead of cloud (default: false)
- `--token TEXT`: JWT authentication token (env: PARTCL_TOKEN)
- `--url TEXT`: Override API base URL (env: PARTCL_API_URL)
- `--output FORMAT`: Output format: json, table (default: table)

**Examples:**

```bash
# Basic usage with cloud service
partcl timing \
    --verilog-file examples/adder.v \
    --lib-file examples/sky130.lib \
    --sdc-file examples/constraints.sdc

# Use local Docker container
partcl timing \
    --verilog-file examples/adder.v \
    --lib-file examples/sky130.lib \
    --sdc-file examples/constraints.sdc \
    --local

# Custom server URL
partcl timing \
    --verilog-file examples/adder.v \
    --lib-file examples/sky130.lib \
    --sdc-file examples/constraints.sdc \
    --url http://my-server:8000

# JSON output for scripting
partcl timing \
    --verilog-file examples/adder.v \
    --lib-file examples/sky130.lib \
    --sdc-file examples/constraints.sdc \
    --output json
```

## Environment Variables

- `PARTCL_TOKEN`: JWT authentication token for cloud service
- `PARTCL_API_URL`: Override default API URL
- `PARTCL_LOCAL`: Set to "true" to use local mode by default

## Configuration

Create a `.partcl.env` file in your project or home directory:

```env
# Authentication
PARTCL_TOKEN=your-jwt-token-here

# Server configuration
PARTCL_API_URL=https://your-custom-server.com
PARTCL_LOCAL=false

# Output preferences
PARTCL_OUTPUT_FORMAT=table
```

## Docker Deployment

To run the Boson server locally in Docker:

```bash
# Build the Docker image
cd partcl
./scripts/build_docker_local.sh --release

# Run the server
docker run --rm -it \
    --gpus all \
    -p 8000:8000 \
    -e ENABLE_AUTH=false \
    boson-release:latest

# Test the server
curl http://localhost:8000/health
```

## Authentication

The CLI uses Google OAuth authentication for secure access to cloud services:

1. **First-time setup**: Run `partcl login` to authenticate
   ```bash
   partcl login
   # Opens browser → Sign in with Google → Done!
   ```

2. **Token storage**: Your authentication token is automatically saved to `~/.partcl.env`

3. **Manual token setup** (optional): If you have a JWT token from another source
   ```bash
   export PARTCL_TOKEN="your-jwt-token"
   # Or pass via --token flag
   partcl timing --token "your-jwt-token" ...
   ```

4. **For local mode**: Authentication can be disabled when using Docker

## Output Formats

### Table Format (default)
```
Timing Analysis Results
=======================
Worst Negative Slack:  -1234.56 ps
Total Negative Slack:  -5678.90 ps
Timing Violations:     42
Total Endpoints:       1337
```

### JSON Format
```json
{
  "success": true,
  "wns": -1234.56,
  "tns": -5678.90,
  "num_violations": 42,
  "total_endpoints": 1337
}
```

## Development

```bash
# Clone the repository
git clone https://github.com/partcleda/partcl-cli.git
cd partcl-cli

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black partcl
ruff check partcl

# Type checking
mypy partcl
```

## Troubleshooting

### Connection refused error
- For local mode: Ensure Docker container is running
- For remote mode: Check internet connection and token validity

### Authentication error
- Verify your token is valid and not expired
- For local mode: Use `--local` flag or set `ENABLE_AUTH=false` in Docker

### GPU not available
- Ensure Docker is run with `--gpus all` flag
- Check CUDA installation with `nvidia-smi`

## Support

- Documentation: https://docs.partcl.com
- Issues: https://github.com/partcleda/partcl-cli/issues
- Email: support@partcl.com

## License

MIT License - see LICENSE file for details