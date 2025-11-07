"""Authentication flow for pi-ragbox CLI."""

import socket
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import List, Optional, Tuple

from .api import APIClient
from .config import get_base_url, save_credentials, save_default_project


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback."""

    cookies: Optional[dict] = None
    email: Optional[str] = None
    error: Optional[str] = None

    def do_GET(self):
        """Handle GET request with OAuth callback."""
        # Parse query parameters
        parsed_path = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_path.query)

        if "cookies" in params:
            # Cookies are passed as a JSON-encoded string
            import json

            CallbackHandler.cookies = json.loads(params["cookies"][0])
            CallbackHandler.email = params.get("email", [None])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_content = """
                <html>
                <head><title>Authentication Successful</title></head>
                <body style="font-family: system-ui; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f5f5f5;">
                    <div style="text-align: center; background: white; padding: 3rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h1 style="color: #10b981; margin-bottom: 1rem;">&#10003; Authentication Successful!</h1>
                        <p style="color: #6b7280; margin-bottom: 1rem;">You can now close this window and return to your terminal.</p>
                        <p style="color: #9ca3af; font-size: 0.875rem;">pi-ragbox CLI</p>
                    </div>
                </body>
                </html>
                """
            self.wfile.write(html_content.encode("utf-8"))
        elif "error" in params:
            CallbackHandler.error = params["error"][0]
            self.send_response(400)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            html_content = """
                <html>
                <head><title>Authentication Failed</title></head>
                <body style="font-family: system-ui; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; background: #f5f5f5;">
                    <div style="text-align: center; background: white; padding: 3rem; border-radius: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h1 style="color: #ef4444; margin-bottom: 1rem;">&#10007; Authentication Failed</h1>
                        <p style="color: #6b7280; margin-bottom: 1rem;">Please try again or check your terminal for more information.</p>
                        <p style="color: #9ca3af; font-size: 0.875rem;">pi-ragbox CLI</p>
                    </div>
                </body>
                </html>
                """
            self.wfile.write(html_content.encode("utf-8"))
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Invalid callback request")

    def log_message(self, format, *args):
        """Suppress log messages."""
        pass


def find_available_port(start_port: int = 8080, end_port: int = 8180) -> int:
    """Find an available port in the given range.

    Args:
        start_port: Starting port to check
        end_port: Ending port to check

    Returns:
        Available port number

    Raises:
        OSError: If no available port is found
    """
    for port in range(start_port, end_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("localhost", port))
                return port
        except OSError:
            continue
    raise OSError("No available ports found in range")


def start_callback_server(
    port: int, timeout: int = 120
) -> Tuple[Optional[dict], Optional[str], Optional[str]]:
    """Start a local HTTP server to receive the OAuth callback.

    Args:
        port: Port to listen on
        timeout: Timeout in seconds

    Returns:
        Tuple of (cookies, email, error). Cookies and email will be None if error occurred.
    """
    server = HTTPServer(("localhost", port), CallbackHandler)
    server.timeout = timeout

    # Reset class variables
    CallbackHandler.cookies = None
    CallbackHandler.email = None
    CallbackHandler.error = None

    # Handle one request (the callback)
    server.handle_request()

    return CallbackHandler.cookies, CallbackHandler.email, CallbackHandler.error


def open_browser_for_login(callback_port: int) -> bool:
    """Open the user's browser to the login page.

    Args:
        callback_port: The port where the callback server is listening

    Returns:
        True if browser was opened successfully, False otherwise
    """
    base_url = get_base_url()
    callback_url = f"http://localhost:{callback_port}/callback"
    login_url = (
        f"{base_url}/api/auth/cli-login?redirect={urllib.parse.quote(callback_url)}"
    )

    try:
        return webbrowser.open(login_url)
    except:
        return False


def create_project_flow(client: APIClient, existing_projects: List) -> Optional[List]:
    """Poll for new projects after opening browser to create page.

    Args:
        client: API client with valid authentication
        existing_projects: List of existing project dictionaries

    Returns:
        Updated list of projects if new projects were detected, None if cancelled
    """
    # Get existing project IDs
    existing_ids = {project.get("id") for project in existing_projects}

    # Open browser to create page
    create_url = "https://ragbox.withpi.ai/create"
    try:
        webbrowser.open(create_url)
        print(f"\n✓ Opened browser to: {create_url}")
    except Exception as e:
        print(f"\n⚠ Could not open browser: {e}")
        print(f"Please visit: {create_url}")

    print("\nWaiting for new project to be created...")
    print("(Press Ctrl+C to cancel and return to project selection)\n")

    try:
        # Poll for new projects every 3 seconds
        while True:
            time.sleep(3)

            try:
                # Fetch updated project list
                current_projects = client.get_projects()
                current_ids = {project.get("id") for project in current_projects}

                # Check for new projects
                new_ids = current_ids - existing_ids

                if new_ids:
                    # New project(s) detected
                    new_projects = [p for p in current_projects if p.get("id") in new_ids]
                    print(f"✓ Detected {len(new_projects)} new project(s)!")
                    for project in new_projects:
                        print(f"  - {project.get('name', 'Unnamed')} (ID: {project.get('id')})")
                    print()
                    return current_projects

                # Still waiting
                print(".", end="", flush=True)

            except Exception as e:
                print(f"\n⚠ Error checking projects: {e}")
                print("Retrying...")

    except (KeyboardInterrupt, EOFError):
        print("\n\nCancelled project creation.")
        return None


def login_flow() -> Tuple[bool, str]:
    """Execute the login flow.

    Returns:
        Tuple of (success, message)
    """
    try:
        # Find an available port
        port = find_available_port()
    except OSError:
        return False, "Failed to find an available port for callback server"

    # Construct the callback URL that will be shown to the user
    callback_url = f"http://localhost:{port}/callback"
    base_url = get_base_url()
    login_url = (
        f"{base_url}/api/auth/cli-login?redirect={urllib.parse.quote(callback_url)}"
    )

    # Start the callback server in a background thread
    server_thread = threading.Thread(
        target=lambda: start_callback_server(port), daemon=True
    )
    server_thread.start()

    # Try to open the browser
    browser_opened = open_browser_for_login(port)

    if browser_opened:
        print(
            f"Opening browser for authentication...\n\nIf the browser doesn't open, visit:\n{login_url}"
        )
    else:
        print(f"Please visit this URL to authenticate:\n{login_url}")

    # Wait for the server thread to complete (with timeout)
    server_thread.join(timeout=120)

    # Check if we got cookies
    if CallbackHandler.cookies:
        cookies = CallbackHandler.cookies
        email = CallbackHandler.email or "authenticated_user"

        # Validate the cookies by trying to get projects
        try:
            client = APIClient(cookies=cookies)
            projects = client.get_projects()

            # Save credentials first
            save_credentials(cookies, user_email=email)

            # Prompt user to select a default project or create a new one
            while True:
                # Display project list or empty state
                if projects:
                    print(f"\n✓ Found {len(projects)} project(s).")
                    print("\nPlease select a default project:")
                    print("  0. Create a new project")

                    for idx, project in enumerate(projects, 1):
                        project_name = project.get("name", "Unnamed")
                        project_id = project.get("id", "N/A")
                        print(f"  {idx}. {project_name} (ID: {project_id})")
                else:
                    print("\n✓ No existing projects found.")
                    print("\nOptions:")
                    print("  0. Create a new project")

                # Prompt for selection
                try:
                    prompt_text = "\nEnter project number (or press Enter to skip): " if projects else "\nEnter 0 to create a project (or press Enter to skip): "
                    choice = input(prompt_text).strip()

                    if not choice:
                        # User skipped selection
                        print("No default project selected.")
                        break

                    choice_num = int(choice)

                    if choice_num == 0:
                        # User wants to create a new project
                        updated_projects = create_project_flow(client, projects)
                        if updated_projects is not None:
                            # New projects were created, update the list and loop again
                            projects = updated_projects
                            continue
                        else:
                            # User cancelled, return to selection
                            continue

                    if 1 <= choice_num <= len(projects):
                        project_id = projects[choice_num - 1]["id"]
                        project_name = projects[choice_num - 1].get(
                            "name", "Unnamed"
                        )
                        save_default_project(project_id)
                        print(f"✓ Set default project to: {project_name}")
                        break
                    else:
                        max_num = len(projects) if projects else 0
                        print(
                            f"Please enter a number between 0 and {max_num}"
                        )
                except ValueError:
                    print("Please enter a valid number")
                except (KeyboardInterrupt, EOFError):
                    print("\nNo default project selected.")
                    break

            return True, f"Successfully authenticated as {email}!"

        except Exception as e:
            return False, f"Authentication failed: {str(e)}"

    elif CallbackHandler.error:
        return False, f"Authentication failed: {CallbackHandler.error}"

    else:
        return False, "Authentication timed out. Please try again."
