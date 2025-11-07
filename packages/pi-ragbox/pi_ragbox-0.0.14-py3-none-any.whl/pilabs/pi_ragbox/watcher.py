"""File watcher for automatic code reloading in sandbox service."""

import asyncio
import time
from pathlib import Path
from typing import Callable, Awaitable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from rich.console import Console


class DebouncedFileHandler(FileSystemEventHandler):
    """File system event handler with debouncing to group rapid changes."""

    def __init__(
        self,
        callback: Callable[[], Awaitable[None]],
        debounce_seconds: float = 0.5,
        console: Console | None = None,
    ):
        """Initialize the handler.

        Args:
            callback: Async function to call when files change
            debounce_seconds: Time to wait before triggering callback
            console: Rich console for output (optional)
        """
        super().__init__()
        self.callback = callback
        self.debounce_seconds = debounce_seconds
        self.console = console or Console()
        self._last_trigger_time = 0
        self._pending_changes: set[str] = set()
        self._task: asyncio.Task | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the event loop for async callbacks."""
        self._loop = loop

    def _should_watch_file(self, path: str) -> bool:
        """Check if a file should trigger a reload.

        Args:
            path: File path to check

        Returns:
            True if the file should be watched
        """
        path_obj = Path(path)

        # Ignore directories
        if path_obj.is_dir():
            return False

        # Ignore hidden files and directories
        if any(part.startswith('.') for part in path_obj.parts):
            return False

        # Ignore __pycache__ and .pyc files
        if '__pycache__' in path_obj.parts or path_obj.suffix == '.pyc':
            return False

        # Watch Python files and requirements.txt
        if path_obj.suffix == '.py' or path_obj.name == 'requirements.txt':
            return True

        return False

    def _schedule_reload(self, event_path: str) -> None:
        """Schedule a reload after debounce period.

        Args:
            event_path: Path that triggered the event
        """
        current_time = time.time()
        self._pending_changes.add(event_path)

        # If we recently triggered, cancel the existing task
        if self._task and not self._task.done():
            self._task.cancel()

        # Calculate time since last trigger
        time_since_last = current_time - self._last_trigger_time
        delay = max(0, self.debounce_seconds - time_since_last)

        # Schedule the callback
        if self._loop:
            self._task = self._loop.create_task(self._delayed_callback(delay))

    async def _delayed_callback(self, delay: float) -> None:
        """Execute callback after delay.

        Args:
            delay: Seconds to wait before executing
        """
        try:
            await asyncio.sleep(delay)

            # Display changed files
            if self._pending_changes:
                self.console.print(
                    f"[yellow]Files changed:[/yellow] {', '.join(sorted(self._pending_changes))}"
                )
                self._pending_changes.clear()

            # Update last trigger time and call the callback
            self._last_trigger_time = time.time()
            await self.callback()

        except asyncio.CancelledError:
            # Task was cancelled, will be rescheduled
            pass

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification events."""
        if not event.is_directory and self._should_watch_file(event.src_path):
            self._schedule_reload(event.src_path)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file creation events."""
        if not event.is_directory and self._should_watch_file(event.src_path):
            self._schedule_reload(event.src_path)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file deletion events."""
        if not event.is_directory and self._should_watch_file(event.src_path):
            self._schedule_reload(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file move events."""
        if not event.is_directory and self._should_watch_file(event.dest_path):
            self._schedule_reload(event.dest_path)


async def watch_directory(
    path: Path,
    on_change: Callable[[], Awaitable[None]],
    console: Console | None = None,
) -> Observer:
    """Watch a directory for changes and trigger callback.

    Args:
        path: Directory to watch
        on_change: Async callback to trigger on file changes
        console: Rich console for output (optional)

    Returns:
        The watchdog Observer instance
    """
    console = console or Console()
    loop = asyncio.get_event_loop()

    # Create handler and observer
    handler = DebouncedFileHandler(on_change, console=console)
    handler.set_event_loop(loop)

    observer = Observer()
    observer.schedule(handler, str(path), recursive=True)
    observer.start()

    console.print(f"[green]Watching for changes in:[/green] {path}")

    return observer
