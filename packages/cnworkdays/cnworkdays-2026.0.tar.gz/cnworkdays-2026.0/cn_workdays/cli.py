import asyncio
import argparse
import time
from pathlib import Path
from typing import Dict, Type, Union, List, Optional

import marimo
from hypercorn.asyncio import serve
from hypercorn.config import Config
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, IntPrompt
from rich.theme import Theme
from textual.app import App

from cn_workdays.workcalc.workcalc_textual import WorkDayCalApp
from cn_workdays.__version__ import __version__

# Configure rich console with custom theme
console = Console(
    theme=Theme(
        {
            "info": "cyan",
            "warning": "yellow",
            "error": "bold red",
            "success": "bold green",
        }
    )
)

APPS: Dict[str, Dict[str, Union[str, List[str], Type[App]]]] = {
    "holiparse": {
        "name": "Holiday Announcement Parser",
        "description": "Extract Chinese holiday schedules from official State Council announcements",
        "modes": ["web"],
    },
    "workcalc": {
        "name": "Working Day Calculator",
        "description": "Calculate dates based on Chinese holidays and compensatory working days",
        "modes": ["web", "terminal"],
        "textual_app": WorkDayCalApp,
    },
}


def setup_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for command line usage."""
    parser = argparse.ArgumentParser(
        description="CN Workdays - Chinese Working Day Calculator and Holiday Announcement Parser"
    )
    parser.add_argument(
        "--version", "-v", action="version", version=f"cnworkdays {__version__}"
    )

    # Create subparsers for each application
    subparsers = parser.add_subparsers(dest="app", help="Select application")

    # Add subparsers for each app
    for app_id, app_info in APPS.items():
        app_parser = subparsers.add_parser(
            app_id, help=app_info["name"], description=app_info["description"]
        )

        # Create mode subparsers for each app
        mode_subparsers = app_parser.add_subparsers(
            dest="mode", help="Select interface mode", required=False
        )

        # Add mode-specific arguments
        for mode in app_info["modes"]:
            mode_parser = mode_subparsers.add_parser(mode, help=f"Run in {mode} mode")
            if mode == "web":
                mode_parser.add_argument(
                    "--host", default="127.0.0.1", help="Host address to bind to"
                )
                mode_parser.add_argument(
                    "--port", type=int, default=8080, help="Port number to listen on"
                )

    return parser


def display_app_header():
    """Display application header with styling."""
    console.print(
        Panel(
            "cnworkdays helps you accurately manage schedules around Chinese holidays:\n"
            "- Holiday Announcement Parser\n"
            "- Chinese Working Day Calculator",
            title="[bold blue]cnworkdays[/bold blue]",
            border_style="blue",
            title_align="center",
        )
    )


def prompt_app_selection() -> tuple[str, Dict]:
    """Interactive prompt for application selection."""
    console.print("\n[warning]Available Applications:[/warning]")

    app_list = list(APPS.keys())
    for idx, app_id in enumerate(app_list):
        details = APPS[app_id]
        console.print(f"  {idx}. [success]{app_id}[/success]: {details['name']}")
        console.print(f"     ↳ {details['description']}")

    try:
        choice = IntPrompt.ask(
            "\n[info]Select an application[/info]",
            default=0,
            show_default=True,
            show_choices=False,
            choices=[str(idx) for idx in range(len(app_list))],
        )
        return app_list[choice], APPS[app_list[choice]]

    except KeyboardInterrupt:
        pass


def prompt_interface_mode(available_modes: List[str]) -> str:
    """Interactive prompt for interface mode selection."""
    if len(available_modes) == 1:
        return available_modes[0]

    console.print("\n[warning]Available Modes:[/warning]")
    for idx, mode in enumerate(available_modes):
        console.print(f"  {idx}. [success]{mode}[/success]")

    try:
        choice = IntPrompt.ask(
            "\n[info]Choose interface type[/info]",
            default=0,
            choices=[str(idx) for idx in range(len(available_modes))],
            show_default=True,
            show_choices=False,
        )
        return available_modes[choice]
    except KeyboardInterrupt:
        pass


def prompt_web_config() -> tuple[str, int]:
    """Interactive prompt for web configuration."""
    try:
        host = Prompt.ask("Host address", default="127.0.0.1")
        port = IntPrompt.ask("Port number", default=8080)
        return host, port
    except KeyboardInterrupt:
        pass


async def launch_marimo_app(appname: str, host: str, port: int) -> None:
    """Launch a marimo web application with the specified configuration.

    :param appname: Name of the application to launch (must be a key in APPS)
    :param host: Host address to bind to
    :param port: Port number to listen on
    """
    base_path = Path(__file__).parent
    script_path = base_path / appname / f"{appname}_marimo.py"

    app = marimo.create_asgi_app().with_app(path="", root=str(script_path)).build()
    config = Config()
    config.loglevel = "WARNING"
    config.bind = [f"{host}:{port}"]

    console.print(
        Panel(
            f":sparkles: [success]Launching [bold magenta]{APPS[appname]['name']}[/bold magenta][/success]\n"
            f":link: [success]Open in browser[/success]: [link]http://{host}:{port}[/link]",
            title="Web Interface",
            border_style="green",
            title_align="center",
        )
    )

    await serve(app, config, shutdown_trigger=lambda: asyncio.Future())


def launch_textual_app(appname: str) -> None:
    """Launch a Textual terminal application.

    :param appname: Name of the application to launch (must be a key in APPS)
    """
    if "textual_app" not in APPS[appname]:
        console.print(f"[error]Terminal interface not available for {appname}[/error]")
        return

    console.print(
        Panel(
            f":sparkles: [success]Launching [bold magenta]{APPS[appname]['name']}[/bold magenta][/success]",
            title="Terminal Interface",
            border_style="green",
        )
    )
    time.sleep(0.5)
    app = APPS[appname]["textual_app"]()
    app.run()


def run_app(
    app_id: str, mode: str, host: Optional[str] = None, port: Optional[int] = None
) -> None:
    """Run the specified application with given configuration."""
    if mode == "web":
        if host is None or port is None:
            host, port = prompt_web_config()
        try:
            asyncio.run(launch_marimo_app(app_id, host, port))
        except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
            console.print("\n[warning]:wave: Goodbye![/warning]")
    elif mode == "terminal":
        launch_textual_app(app_id)


def interactive_mode() -> None:
    """Run the application in interactive mode with prompts."""
    try:
        app_id, app_details = prompt_app_selection()
        mode = prompt_interface_mode(app_details["modes"])
        run_app(app_id, mode)
    except KeyboardInterrupt:
        console.print("\n[warning]:wave: Goodbye![/warning]")


def main():
    """Main entry point for the application."""
    parser = setup_argument_parser()
    args = parser.parse_args()

    display_app_header()

    try:
        if args.app is None:
            # No command line arguments provided, run in interactive mode
            interactive_mode()
        else:
            # Command line arguments provided
            mode = args.mode or prompt_interface_mode(APPS[args.app]["modes"])
            host = getattr(args, "host", None)
            port = getattr(args, "port", None)
            run_app(args.app, mode, host, port)
    except Exception as e:
        console.print(f"\n[error]Error: {str(e)}[/error]")
        parser.print_help()


if __name__ == "__main__":
    main()
