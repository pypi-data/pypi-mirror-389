"""Main entry point for the pi-ragbox CLI."""

import asyncio
import importlib.util
import io
import json
import shutil
import signal
import uuid
import webbrowser
import zipfile
from pathlib import Path
from typing import Any, Optional

import typer
import websockets
from datasets import Dataset, load_dataset
from pilabs.indexing_model import IndexDocument
from pilabs.indexer import PiRagBoxIndexer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .api import APIClient, APIError, AuthenticationError
from .auth import login_flow
from .watcher import watch_directory
from .config import (
    clear_credentials,
    get_config_option,
    get_default_project,
    load_credentials,
    save_default_project,
    set_config_option,
)

app = typer.Typer(
    name="pi-ragbox",
    help="Pi-RagBox CLI tool for managing and interacting with your RAG system",
    add_completion=False,
)

console = Console()


@app.command()
def login():
    """
    Authenticate with pi-ragbox.

    Opens a browser window for Google OAuth authentication and stores
    credentials locally for future API calls.
    """
    with console.status("[bold green]Starting authentication flow..."):
        pass

    success, message = login_flow()

    if success:
        rprint(f"[bold green]✓[/bold green] {message}")
        rprint(
            "\n[dim]You can now run 'pi-ragbox init ~/ragbox' to initialize a new workspace.[/dim]"
        )
    else:
        rprint(f"[bold red]✗[/bold red] {message}")
        raise typer.Exit(code=1)


@app.command()
def logout():
    """
    Remove stored authentication credentials.
    """
    clear_credentials()
    rprint("[bold green]✓[/bold green] Successfully logged out")


@app.command()
def projects():
    """
    List all projects for the authenticated user.
    """
    try:
        client = APIClient()
        projects_list = client.get_projects()

        if not projects_list:
            rprint("[yellow]No projects found.[/yellow]")
            return

        # Create a table for displaying projects
        table = Table(title="Your Projects", show_header=True, header_style="bold cyan")
        table.add_column("Project ID", style="dim")
        table.add_column("Name", style="bold")
        table.add_column("Corpus IDs", style="dim")

        for project in projects_list:
            corpus_ids = (
                ", ".join(project.get("corpusIds", []))
                if project.get("corpusIds")
                else "None"
            )
            table.add_row(
                project.get("id", "N/A"), project.get("name", "Unnamed"), corpus_ids
            )

        console.print(table)

    except AuthenticationError as e:
        rprint(f"[bold red]✗[/bold red] {str(e)}")
        rprint("\n[dim]Run 'pi-ragbox login' to authenticate.[/dim]")
        raise typer.Exit(code=1)
    except APIError as e:
        rprint(f"[bold red]✗[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def whoami():
    """
    Display information about the currently authenticated user.
    """
    creds = load_credentials()

    if not creds:
        rprint("[yellow]Not logged in.[/yellow]")
        rprint("\n[dim]Run 'pi-ragbox login' to authenticate.[/dim]")
        raise typer.Exit(code=1)

    rprint(f"[bold]Logged in as:[/bold] {creds.get('user_email', 'Unknown')}")

    if "expires_at" in creds:
        import datetime

        expiry = datetime.datetime.fromtimestamp(creds["expires_at"])
        rprint(f"[dim]Token expires:[/dim] {expiry.strftime('%Y-%m-%d %H:%M:%S')}")


@app.command()
def version():
    """Display the version of pi-ragbox."""
    from . import __version__

    typer.echo(f"pi-ragbox version: {__version__}")


@app.command()
def index(
    hf_dataset: str = typer.Option(
        "withpi/nlweb_allsites",
        "--hf-dataset",
        help="Full name of the Hugging Face dataset to index (owner/name).",
    ),
    corpus: str = typer.Option(
        "nlweb",
        "--corpus",
        help="Corpus name that will store the indexed documents.",
    ),
    id_column: Optional[str] = typer.Option(
        None, "--id", help="Optional column to use as the document identifier."
    ),
    text_column: str = typer.Option(
        "schema_object",
        "--text",
        help="Column that contains the document text.",
    ),
    embedding_column: Optional[str] = typer.Option(
        None,
        "--embedding",
        help="Optional column that contains pre-computed embeddings.",
    ),
    embedding_dim: Optional[int] = typer.Option(
        None,
        "--embedding-dim",
        min=1,
        help="Optional embedding dimension override for the indexer.",
    ),
    embedding_model: Optional[str] = typer.Option(
        None,
        "--embedding-model",
        help="Optional embedding model override for the indexer.",
    ),
):
    """
    Index a Hugging Face dataset into the configured OpenSearch instance.
    """
    rprint(f"[bold green]Loading HF dataset:[/bold green] {hf_dataset}")
    ds: Dataset = load_dataset(hf_dataset, split="train")  # type: ignore

    documents = [
        IndexDocument(
            id=str(example[id_column]) if id_column else None,  # type: ignore
            text=str(example[text_column]),  # type: ignore
            embedding=example[embedding_column] if embedding_column else None,  # type: ignore
        )
        for example in ds
    ]

    if embedding_model == "pi-embedding":
        if embedding_dim is None:
            raise typer.BadParameter(
                "--embedding-dim is required when --embedding-model is set to pi-embedding",
                param_hint="--embedding-dim",
            )
        if embedding_dim != 256:
            raise typer.BadParameter(
                "--embedding-dim must be 256 when --embedding-model is pi-embedding",
                param_hint="--embedding-dim",
            )

    index_config: dict[str, Any] | None = None
    if embedding_dim is not None or embedding_model is not None:
        index_config = {}
        if embedding_dim is not None:
            index_config["dimensions"] = embedding_dim
        if embedding_model is not None:
            index_config["model"] = embedding_model

    async def _run() -> None:
        async with PiRagBoxIndexer() as indexer:
            await indexer.index_corpus(
                documents=documents,
                corpus_name=corpus,
                config=index_config,
            )
            corpora = await indexer.list_corpora()
            rprint(
                "[bold green]Indexing complete.[/bold green] "
                f"Available corpora:\n * {'\n * '.join(corpora)}"
            )

    asyncio.run(_run())


@app.command()
def set(
    key: str = typer.Argument(..., help="Configuration key to set"),
    value: str = typer.Argument(..., help="Value to set for the configuration key"),
):
    """
    Set a configuration option.

    Example:
        pi-ragbox set my_option my_value
    """
    try:
        set_config_option(key, value)
        rprint(
            f"[bold green]✓[/bold green] Set [cyan]{key}[/cyan] = [bold]{value}[/bold]"
        )

    except Exception as e:
        rprint(f"[bold red]✗[/bold red] Failed to set config: {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def get(key: str = typer.Argument(..., help="Configuration key to retrieve")):
    """
    Get a configuration option value.

    Example:
        pi-ragbox get my_option
    """
    value = get_config_option(key)

    if value is not None:
        rprint(f"[cyan]{key}[/cyan] = [bold]{value}[/bold]")
    else:
        rprint(f"[yellow]{key}[/yellow] is not set")
        raise typer.Exit(code=1)


@app.command(name="set-project")
def set_project():
    """
    Change the default project for your pi-ragbox session.

    Lists all available projects and prompts you to select a new default.
    """
    try:
        # Get current credentials
        creds = load_credentials()
        if not creds:
            rprint("[bold red]✗[/bold red] Not logged in")
            rprint("\n[dim]Run 'pi-ragbox login' to authenticate.[/dim]")
            raise typer.Exit(code=1)

        # Fetch projects
        client = APIClient()
        projects = client.get_projects()

        if not projects:
            rprint("[yellow]No projects found.[/yellow]")
            raise typer.Exit(code=0)

        # Display current default
        current_default = get_default_project()
        if current_default:
            rprint(
                f"[dim]Current default project:[/dim] [cyan]{current_default}[/cyan]\n"
            )

        # Create a table for displaying projects
        table = Table(
            title="Available Projects", show_header=True, header_style="bold cyan"
        )
        table.add_column("#", style="dim", width=4)
        table.add_column("Project Name", style="bold")
        table.add_column("Project ID", style="dim")

        for idx, project in enumerate(projects, 1):
            project_name = project.get("name", "Unnamed")
            project_id = project.get("id", "N/A")

            # Highlight current default
            if project_id == current_default:
                project_name = f"→ {project_name}"

            table.add_row(str(idx), project_name, project_id)

        console.print(table)
        rprint()

        # Prompt for selection
        while True:
            try:
                choice = typer.prompt("Enter project number", type=int)

                if 1 <= choice <= len(projects):
                    selected_project = projects[choice - 1]
                    project_id = selected_project["id"]
                    project_name = selected_project.get("name", "Unnamed")

                    save_default_project(project_id)
                    rprint(
                        f"\n[bold green]✓[/bold green] Default project set to: [bold]{project_name}[/bold]"
                    )
                    rprint(f"[dim]  Project ID:[/dim] {project_id}")
                    break
                else:
                    rprint(
                        f"[bold red]✗[/bold red] Please enter a number between 1 and {len(projects)}"
                    )

            except typer.Abort:
                rprint("\n[yellow]Cancelled.[/yellow]")
                raise typer.Exit(code=0)
            except ValueError:
                rprint("[bold red]✗[/bold red] Please enter a valid number")

    except AuthenticationError:
        rprint("[bold red]✗[/bold red] Authentication failed")
        rprint("\n[dim]Run 'pi-ragbox login' to authenticate.[/dim]")
        raise typer.Exit(code=1)
    except APIError as e:
        rprint(f"[bold red]✗[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command()
def init(
    path: str = typer.Argument(
        ..., help="Path where the Ragbox workspace will be created"
    )
):
    """
    Initialize a new Ragbox workspace with starter flow templates.

    Creates a pi_flows directory with template files that you can customize
    and deploy to Modal.

    Example:
        pi-ragbox init ~/my-ragbox-flows
    """
    spec = importlib.util.find_spec("pilabs.pi_ragbox")
    if not spec or not spec.origin:
        rprint("[bold red]✗[/bold red] Could not find pi_ragbox package")
        rprint("\n[dim]Please ensure pilabs is installed.[/dim]")
        raise typer.Exit(code=1)

    # Expand and resolve the target path
    target_path = Path(path).expanduser().resolve()
    pi_flows_dir = target_path / "pi_flows"

    # Check if pi_flows already exists
    if pi_flows_dir.exists():
        rprint(f"[bold yellow]⚠[/bold yellow] Directory already exists: {pi_flows_dir}")
        confirm = typer.confirm("Do you want to overwrite it?", default=False)
        if not confirm:
            rprint("[dim]Cancelled.[/dim]")
            raise typer.Exit(code=0)

    # Find the builtin_flows directory in the installed package
    package_path = Path(spec.origin).parent.parent
    source_dir = package_path / "search_service" / "builtin_flows" / "pi_flows"

    if not source_dir.exists():
        rprint(f"[bold red]✗[/bold red] Source directory not found: {source_dir}")
        rprint("\n[dim]Please ensure search-service is properly installed.[/dim]")
        raise typer.Exit(code=1)

    # Files to copy
    files_to_copy = ["__init__.py", "search_simple.py", "requirements.txt"]

    for file_name in files_to_copy:
        source_file = source_dir / file_name
        if not source_file.exists():
            rprint(f"[bold red]✗[/bold red] Source file not found: {source_file}")
            raise typer.Exit(code=1)

    # Create the directory structure
    try:
        pi_flows_dir.mkdir(parents=True, exist_ok=True)
        rprint(f"[bold green]✓[/bold green] Created directory: {pi_flows_dir}")
    except Exception as e:
        rprint(f"[bold red]✗[/bold red] Failed to create directory: {str(e)}")
        raise typer.Exit(code=1)

    # Copy the template files
    try:
        for file_name in files_to_copy:
            source_file = source_dir / file_name
            dest_file = pi_flows_dir / file_name
            shutil.copy2(source_file, dest_file)
            rprint(f"[bold green]✓[/bold green] Copied {file_name}")

    except Exception as e:
        rprint(f"[bold red]✗[/bold red] Failed to copy files: {str(e)}")
        raise typer.Exit(code=1)

    # Display success message with next steps
    rprint()
    success_panel = Panel(
        f"[bold green]Initialized Ragbox workspace at:[/bold green]\n"
        f"[cyan]{target_path}[/cyan]\n\n"
        f"[bold]Created structure:[/bold]\n"
        f"  {target_path}/\n"
        f"  └── pi_flows/\n"
        f"      ├── __init__.py\n"
        f"      └── requirements.txt\n"
        f"      └── search_simple.py\n\n"
        f"[bold]Next steps:[/bold]\n"
        f"  1. Review and customize your flow in pi_flows/search_simple.py\n"
        f"  2. (if needed) Add package dependencies to pi_flows/requirements.txt\n"
        f"  3. Serve:\n"
        f"     [cyan]pi-ragbox serve {target_path}[/cyan]",
        title="[bold green]Workspace Initialized[/bold green]",
        border_style="green",
        padding=(1, 2),
    )
    console.print(success_panel)


def create_directory_zip(directory_path: Path) -> bytes:
    """Create a zip file from a directory and return it as bytes.

    The contents of the directory will be at the root of the archive,
    without including the directory name itself.
    """
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in directory_path.rglob("*"):
            if file_path.is_file():
                # Get relative path from the directory itself (not its parent)
                arcname = file_path.relative_to(directory_path)
                zip_file.write(file_path, arcname=str(arcname))

    return zip_buffer.getvalue()

async def upload_code(
    websocket,
    python_path: Path,
    ready_queue: asyncio.Queue,
) -> bool:
    """
    Upload code to the sandbox service via WebSocket.

    Args:
        websocket: Active WebSocket connection
        python_path: Path to the code directory to upload
        app_id: Application ID for auto-execution
        ready_queue: Queue to receive "ready" message from main loop
        is_reload: Whether this is a reload (affects messaging)

    Returns:
        True if upload succeeded, False otherwise
    """
    rprint(f"[dim]Uploading from {python_path}...[/dim]")

    try:
        zip_data = create_directory_zip(python_path)
    except Exception as e:
        rprint(f"[bold red]✗[/bold red] Failed to create zip: {str(e)}")
        return False

    try:
        upload_cmd = {
            "type": "upload",
            "size": len(zip_data),
        }
        await websocket.send(json.dumps(upload_cmd))

        # Wait for ready response from the main message loop
        try:
            ready_msg = await asyncio.wait_for(ready_queue.get(), timeout=10.0)
            if ready_msg.get("type") != "ready":
                rprint(f"[bold red]✗[/bold red] Unexpected response: {ready_msg}")
                return False
        except asyncio.TimeoutError:
            rprint("[bold red]✗[/bold red] Timeout waiting for ready response")
            return False

        # Send zip data
        await websocket.send(zip_data)
        rprint(
            "[bold green]→[/bold green] Code uploaded...\n"
        )

        return True

    except Exception as e:
        rprint(f"[bold red]✗[/bold red] Upload failed: {str(e)}")
        return False


async def websocket_message_loop(
    websocket,
    ready_queue: asyncio.Queue,
    shutdown_requested: asyncio.Event,
    console: Console,
) -> int:
    """
    Main WebSocket message processing loop.

    Reads messages from the WebSocket and handles them appropriately:
    - "ready" messages are placed in the queue for upload_code()
    - stdout/stderr are printed to console
    - exit messages return the exit code
    - errors return code 1

    Args:
        websocket: Active WebSocket connection
        ready_queue: Queue for "ready" messages to be consumed by upload_code
        shutdown_requested: Event to signal shutdown
        console: Rich console for output

    Returns:
        Exit code from the process
    """
    exit_code = 0
    while not shutdown_requested.is_set():
        try:
            # Wait for message with timeout to check shutdown flag
            msg_str = await asyncio.wait_for(websocket.recv(), timeout=0.5)
            msg = json.loads(msg_str)
            msg_type = msg.get("type")

            if msg_type == "ready":
                # Put ready message into queue for upload_code
                await ready_queue.put(msg)
            elif msg_type == "uploaded":
                # Already notified by upload_code, skip
                pass
            elif msg_type == "stdout":
                # Print stdout directly to terminal
                console.print(msg.get("data", ""))
            elif msg_type == "stderr":
                # Print stderr in yellow
                console.print(f"[yellow]{msg.get('data', '')}[/yellow]")
            elif msg_type == "exit":
                exit_code = msg.get("code", 0)
                rprint(f"\n[dim]Process exited with code {exit_code}[/dim]")
                break
            elif msg_type == "error":
                rprint(f"[bold red]✗[/bold red] Error: {msg.get('error')}")
                return 1

        except asyncio.TimeoutError:
            # Timeout is normal, just checking shutdown flag
            continue
        except websockets.exceptions.ConnectionClosed:
            rprint("\n[yellow]Connection closed by server[/yellow]")
            break

    return exit_code


async def run_via_sandbox_service(
    app_id: str,
    python_path: Path,
    sandbox_url: str = "wss://sandbox-service.withpi.ai/ws",
) -> int:
    """
    Connect to sandbox-service via WebSocket, upload code, and stream output.
    Watches for file changes and automatically reloads.

    Returns the exit code of the process.
    """
    # Set up signal handler for graceful shutdown
    shutdown_requested = asyncio.Event()

    def signal_handler(signum, frame):
        shutdown_requested.set()

    signal.signal(signal.SIGINT, signal_handler)

    observer = None
    message_loop_task = None
    try:
        async with websockets.connect(sandbox_url) as websocket:
            # Receive welcome message
            _ = await websocket.recv()
            rprint("[dim]Connected to sandbox service[/dim]\n")

            # Queue for "ready" messages to be consumed by upload_code
            ready_queue: asyncio.Queue = asyncio.Queue()

            # Start the WebSocket message loop as a background task
            message_loop_task = asyncio.create_task(
                websocket_message_loop(websocket, ready_queue, shutdown_requested, console)
            )

            try:
                # Perform initial upload (message loop is now running to handle "ready")
                if not await upload_code(websocket, python_path, ready_queue):
                    return 1
                
                execute_cmd = {
                    "type": "execute",
                    "app_id": app_id,
                }
                await websocket.send(json.dumps(execute_cmd))

                # Set up file watcher for automatic reloading
                async def on_file_change():
                    """Callback when files change - re-upload code."""
                    await upload_code(websocket, python_path, ready_queue)

                observer = await watch_directory(python_path, on_file_change, console)

                # Wait for the message loop to complete (until exit or shutdown)
                exit_code = await message_loop_task

                # If shutdown was requested, send stop command
                if shutdown_requested.is_set():
                    rprint("\n[yellow]Shutting down...[/yellow]")
                    try:
                        stop_cmd = {"type": "stop"}
                        await websocket.send(json.dumps(stop_cmd))
                        # Note: We don't wait for response as message_loop_task already finished
                    except websockets.exceptions.ConnectionClosed:
                        pass

                    return 130  # Standard exit code for SIGINT

                return exit_code

            finally:
                # Stop the file watcher
                if observer:
                    observer.stop()
                    observer.join()

                # Cancel message loop task if it's still running
                if message_loop_task and not message_loop_task.done():
                    message_loop_task.cancel()
                    try:
                        await message_loop_task
                    except asyncio.CancelledError:
                        pass

    except ConnectionRefusedError:
        rprint(
            f"[bold red]✗[/bold red] Could not connect to sandbox service at {sandbox_url}"
        )
        rprint("\n[dim]Make sure the sandbox-service is running:[/dim]")
        rprint("[dim]  cd sandbox-service && ./sandbox-service[/dim]")
        return 1
    except Exception as e:
        rprint(f"[bold red]✗[/bold red] Unexpected error: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


@app.command()
def serve(
    python_path: str = typer.Argument(
        ..., help="Path to prepend to PYTHONPATH for custom pi_flows"
    ),
    sandbox_url: str = typer.Option(
        "wss://sandbox-service.withpi.ai/ws",
        "--sandbox-url",
        help="WebSocket URL of the sandbox service",
    ),
):
    """
    Launch a stack with custom configuration.

    Example:
        pi-ragbox serve /path/to/custom/flows
    """
    # Check for default project and validate it exists
    default_project_id = get_default_project()
    if not default_project_id:
        rprint("[bold red]✗[/bold red] No default project configured")
        rprint(
            "\n[dim]Please run 'pi-ragbox login' to authenticate and select a default project.[/dim]"
        )
        raise typer.Exit(code=1)

    # Validate the project exists
    try:
        client = APIClient()
        projects = client.get_projects()

        project_exists = any(p.get("id") == default_project_id for p in projects)

        if not project_exists:
            rprint(
                f"[bold red]✗[/bold red] Default project '{default_project_id}' not found"
            )
            rprint("\n[dim]Available projects:[/dim]")
            for project in projects:
                rprint(
                    f"  • {project.get('name', 'Unnamed')} (ID: {project.get('id', 'N/A')})"
                )
            rprint(
                "\n[dim]Run 'pi-ragbox set-project' to change your default project.[/dim]"
            )
            raise typer.Exit(code=1)

    except AuthenticationError:
        rprint("[bold red]✗[/bold red] Not authenticated")
        rprint("\n[dim]Run 'pi-ragbox login' to authenticate.[/dim]")
        raise typer.Exit(code=1)
    except APIError as e:
        rprint(f"[bold red]✗[/bold red] Failed to validate project: {str(e)}")
        raise typer.Exit(code=1)

    # Validate python_path exists
    python_path_obj = Path(python_path).resolve()
    if not python_path_obj.exists():
        rprint(f"[bold red]✗[/bold red] Python path does not exist: {python_path}")
        raise typer.Exit(code=1)

    # Construct the application URL
    app_id = uuid.uuid4().hex
    modal_url = f"https://pilabs-ragbox--{app_id}-fastapi-app-dev.modal.run"
    app_url = f"https://ragbox.withpi.ai/project/{default_project_id}?dev={modal_url}"

    # Display what we're doing
    rprint(
        f"[bold cyan]→[/bold cyan] Launching Modal stack for app ID: [bold]{app_id}[/bold]"
    )
    rprint(f"[dim]  Project:[/dim] {default_project_id}")
    rprint(f"[dim]  Python path:[/dim] {python_path}")
    rprint()

    # Display the application URL prominently
    url_panel = Panel(
        f"[bold cyan]{app_url}[/bold cyan]\n\n[dim]Opening in browser...[/dim]",
        title="[bold green]Your Application URL[/bold green]",
        border_style="green",
        padding=(1, 2),
    )
    console.print(url_panel)
    rprint()

    # Open browser
    try:
        webbrowser.open(app_url)
    except Exception as e:
        rprint(f"[yellow]⚠[/yellow] Could not open browser: {str(e)}")
        rprint("[dim]Please open the URL manually.[/dim]\n")

    exit_code = asyncio.run(run_via_sandbox_service(app_id, python_path_obj, sandbox_url))

    if exit_code != 0:
        raise typer.Exit(code=exit_code)


def main():
    """Main entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
