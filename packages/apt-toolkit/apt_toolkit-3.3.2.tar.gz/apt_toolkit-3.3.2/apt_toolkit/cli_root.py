import sys
from typing import Callable, Iterator, Optional

from rich.console import Console

from apt_toolkit import __version__
from apt_toolkit.catalog import get_catalog
from apt_toolkit.cli_new import apt


def launch_interactive_shell(
    console: Optional[Console] = None,
    input_provider: Optional[Callable[[str], str]] = None,
) -> int:
    """Start an interactive shell to explore the APT toolkit capabilities."""
    if not console:
        console = Console()
    if not input_provider:
        input_provider = input

    console.print(f"[bold cyan]APT Toolkit Interactive Console v{__version__}[/bold cyan]")
    console.print("Type 'help' for a list of commands, or 'exit' to quit.")

    catalog = get_catalog()

    while True:
        try:
            command = input_provider("> ")
            if command.lower() == "exit":
                break
            elif command.lower() == "help":
                console.print("[bold]Available Commands:[/bold]")
                for category, details in catalog.items():
                    console.print(f"  [bold]{category}[/bold]")
                    for command_name, description in details.get("commands", {}).items():
                        console.print(f"    {command_name}: {description}")
            else:
                # Basic command parsing and execution
                parts = command.split()
                if not parts:
                    continue
                # This is a very basic implementation. A real implementation would use a proper command parser.
                with console.capture() as capture:
                    result = apt.main(parts, standalone_mode=False)
                console.print(capture.get())

        except (KeyboardInterrupt, EOFError):
            break

    return 0
