"""
Authentication commands for Partcl CLI.

Implements OAuth authentication with Supabase using Google provider.
"""

import base64
import hashlib
import json
import os
import secrets
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse

import click
import httpx
from dotenv import set_key
from rich.console import Console

console = Console()

# Supabase configuration
SUPABASE_PROJECT = "sbopwxcfrjhhslqnkmoo"
SUPABASE_URL = f"https://{SUPABASE_PROJECT}.supabase.co"
CALLBACK_PORT = 8357
CALLBACK_URL = f"http://localhost:{CALLBACK_PORT}/callback"


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP request handler for OAuth callback."""

    result: Optional[dict] = None
    error_message: Optional[str] = None

    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass

    def do_GET(self):
        """Handle GET request from OAuth redirect."""
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/callback":
            # Parse the fragment (Supabase returns tokens in URL fragment after #)
            # Send HTML that extracts the fragment and sends it back
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()

            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Authentication</title>
                <style>
                    body { font-family: system-ui, sans-serif; text-align: center; padding: 50px; }
                    .success { color: #10b981; font-size: 24px; margin-bottom: 20px; }
                    .error { color: #ef4444; font-size: 24px; margin-bottom: 20px; }
                    .message { color: #6b7280; }
                </style>
            </head>
            <body>
                <div id="status">Processing authentication...</div>
                <script>
                    // Extract the fragment from the URL
                    const hash = window.location.hash.substring(1);
                    const params = new URLSearchParams(hash);

                    // Check for access token in fragment
                    const accessToken = params.get('access_token');
                    const refreshToken = params.get('refresh_token');
                    const error = params.get('error');
                    const errorDescription = params.get('error_description');

                    if (accessToken) {
                        // Success - send tokens to our server
                        fetch('/success', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                access_token: accessToken,
                                refresh_token: refreshToken,
                                token_type: params.get('token_type'),
                                expires_in: params.get('expires_in')
                            })
                        }).then(() => {
                            document.getElementById('status').innerHTML =
                                '<div class="success">✓ Authentication Successful</div>' +
                                '<div class="message">You can close this window and return to the CLI.</div>';
                        });
                    } else if (error) {
                        // Error - send error to our server
                        fetch('/error', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                error: error,
                                error_description: errorDescription
                            })
                        }).then(() => {
                            document.getElementById('status').innerHTML =
                                '<div class="error">✗ Authentication Failed</div>' +
                                '<div class="message">' + (errorDescription || error) + '</div>' +
                                '<div class="message" style="margin-top: 20px;">Please return to the CLI and try again.</div>';
                        });
                    } else {
                        // No tokens or error in URL
                        document.getElementById('status').innerHTML =
                            '<div class="error">✗ No authentication data received</div>' +
                            '<div class="message">Please return to the CLI and try again.</div>';
                    }
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())

        elif parsed_url.path == "/success" and self.command == "POST":
            # Handle success callback with tokens
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data)
                self.__class__.result = data
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"OK")
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Error: {e}".encode())

        elif parsed_url.path == "/error" and self.command == "POST":
            # Handle error callback
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data)
                error = data.get("error", "Unknown error")
                error_description = data.get("error_description", "")
                self.__class__.error_message = f"{error}: {error_description}" if error_description else error
                self.send_response(200)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"OK")
            except Exception:
                self.send_response(400)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"Error processing error response")

        else:
            # Not a recognized path
            self.send_response(404)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not found")

    def do_POST(self):
        """Handle POST requests."""
        self.do_GET()  # Reuse GET handler for POST


def start_callback_server() -> HTTPServer:
    """
    Start local HTTP server to receive OAuth callback.

    Returns:
        HTTPServer instance
    """
    # Reset class variables
    OAuthCallbackHandler.result = None
    OAuthCallbackHandler.error_message = None

    # Create server
    server = HTTPServer(("localhost", CALLBACK_PORT), OAuthCallbackHandler)

    # Start server in background thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    return server


def wait_for_callback(server: HTTPServer, timeout: int = 300) -> Optional[dict]:
    """
    Wait for OAuth callback with tokens.

    Args:
        server: HTTPServer instance
        timeout: Maximum wait time in seconds

    Returns:
        Token response if successful, None otherwise
    """
    start_time = time.time()

    with console.status("[cyan]Waiting for authentication...[/cyan]") as status:
        while time.time() - start_time < timeout:
            # Check for success result
            if OAuthCallbackHandler.result:
                server.shutdown()
                return OAuthCallbackHandler.result

            # Check for error
            if OAuthCallbackHandler.error_message:
                server.shutdown()
                console.print(f"[red]Authentication error: {OAuthCallbackHandler.error_message}[/red]")
                return None

            time.sleep(0.5)

    # Timeout
    server.shutdown()
    console.print("[red]Authentication timeout - no response received[/red]")
    return None


def save_token_to_config(access_token: str, refresh_token: Optional[str] = None) -> bool:
    """
    Save authentication tokens to config file.

    Args:
        access_token: JWT access token
        refresh_token: Optional refresh token

    Returns:
        True if successful, False otherwise
    """
    config_path = Path.home() / ".partcl.env"

    try:
        # Create file if it doesn't exist
        if not config_path.exists():
            config_path.touch(mode=0o600)

        # Save access token
        set_key(str(config_path), "PARTCL_TOKEN", access_token)

        # Save refresh token if provided
        if refresh_token:
            set_key(str(config_path), "PARTCL_REFRESH_TOKEN", refresh_token)

        # Ensure proper permissions
        config_path.chmod(0o600)

        return True

    except Exception as e:
        console.print(f"[red]Failed to save token to config: {e}[/red]")
        return False


@click.command()
@click.option(
    "--no-browser",
    is_flag=True,
    help="Don't open browser automatically, display URL instead",
)
def login(no_browser: bool) -> None:
    """
    Authenticate with Partcl using your Google account.

    Opens your browser to sign in with Google.
    The authentication token is automatically saved for future use.

    Note: Make sure you have a Google account linked to your Partcl account.
    """
    console.print("\n[bold cyan]Partcl CLI Authentication[/bold cyan]")
    console.print("This will open your browser to sign in with Google.\n")

    # Start callback server
    try:
        server = start_callback_server()
        console.print(f"[green]✓[/green] Local callback server started on port {CALLBACK_PORT}")
    except Exception as e:
        console.print(f"[red]Failed to start callback server: {e}[/red]")
        console.print("[yellow]Make sure port 8357 is not in use[/yellow]")
        sys.exit(1)

    # Build authorization URL with Google provider
    # Supabase will handle the OAuth flow
    auth_url = (
        f"{SUPABASE_URL}/auth/v1/authorize"
        f"?provider=google"
        f"&redirect_to={CALLBACK_URL}"
    )

    # Open browser or display URL
    if no_browser:
        console.print("\n[yellow]Please visit this URL to authenticate:[/yellow]")
        console.print(f"[cyan]{auth_url}[/cyan]\n")
    else:
        console.print("[cyan]Opening browser for Google authentication...[/cyan]")
        if not webbrowser.open(auth_url):
            console.print("\n[yellow]Could not open browser. Please visit this URL:[/yellow]")
            console.print(f"[cyan]{auth_url}[/cyan]\n")

    console.print("[dim]Sign in with your Google account to continue.[/dim]\n")

    # Wait for callback
    token_response = wait_for_callback(server)

    if not token_response:
        console.print("[red]Authentication failed or timed out[/red]")
        sys.exit(1)

    # Extract tokens
    access_token = token_response.get("access_token")
    refresh_token = token_response.get("refresh_token")

    if not access_token:
        console.print("[red]No access token received[/red]")
        sys.exit(1)

    console.print("[green]✓[/green] Authentication successful")

    # Save tokens
    if save_token_to_config(access_token, refresh_token):
        console.print("[green]✓[/green] Token saved to ~/.partcl.env")
        console.print("\n[bold green]Login successful![/bold green]")
        console.print("You can now use the CLI commands without manual token setup.")
        console.print("\nExample: [cyan]partcl timing -v design.v -l library.lib -s constraints.sdc[/cyan]")
    else:
        console.print("[red]Failed to save token to configuration[/red]")
        console.print("\n[yellow]You can manually set the token:[/yellow]")
        console.print(f"export PARTCL_TOKEN='{access_token}'")
        sys.exit(1)


# For testing purposes
if __name__ == "__main__":
    login()