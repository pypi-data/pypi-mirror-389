"""
utils_devops - Lightweight DevOps utilities for automation scripts.

Core modules are always available.
Extra modules are lazy-loaded only when accessed and only if their dependencies are installed.

Example:
    >>> from utils_devops import core, extras
    >>> core.logs.get_logger("test").info("Hello")
    >>> extras.nginx_ops.sync_sites(...)  # lazy-loads nginx_ops if deps exist
"""

from __future__ import annotations

import importlib
import sys
from importlib import import_module
from typing import TYPE_CHECKING, Any

# --- Version & Metadata ---
__version__ = "0.1.5"
__author__ = "Hamed Sheikhan <sh.sheikhan.m@gmail.com>"
__description__ = "Lightweight DevOps utilities for automation scripts"

# --- Console (optional, graceful fallback) ---
try:
    from rich.console import Console
    console = Console()
except Exception:  # pragma: no cover
    console = None  # type: ignore

# --- Core Modules (Always Available) ---
from .core import (
    datetimes,
    envs,
    files,
    logs,
    strings,
    systems,
    script_helpers,
)

# Re-export for convenience
core = type("CoreNamespace", (), {
    "datetimes": datetimes,
    "envs": envs,
    "files": files,
    "logs": logs,
    "strings": strings,
    "systems": systems,
    "script_helpers": script_helpers,
})

if console:
    console.log("[bold green]utils_devops core modules loaded[/bold green]")

# --- Lazy-Loaded Extras ---
class _LazyExtras:
    """
    Dynamically loads extra modules only when accessed.
    Shows helpful install messages if dependencies are missing.
    """

    # Map: attribute_name -> (module_name, pip_extra_name, required_package)
    _registry = {
        "nginx_ops": ("nginx_ops", "nginx", "requests"),
        "docker_ops": ("docker_ops", "docker", "docker"),
        "git_ops": ("git_ops", "git", "gitpython"),
        "ssh_ops": ("ssh_ops", "ssh", "paramiko"),
        "network_ops": ("network_ops", "network", "requests"),
        "interaction": ("interaction", "interaction", "inquirer"),
        "notification": ("notification", "notification", "slack_sdk"),
        "vault_ops": ("vault_ops", "vault", "hvac"),
        "aws_ops": ("aws_ops", "aws", "boto3"),
        "metrics_ops": ("metrics_ops", "metrics", "prometheus_client"),
    }

    def __init__(self):
        self._loaded = {}

    def __getattr__(self, name: str) -> Any:
        if name not in self._registry:
            raise AttributeError(f"utils_devops.extras has no attribute '{name}'")

        if name in self._loaded:
            return self._loaded[name]

        mod_name, extra, req_pkg = self._registry[name]

        try:
            # Import from .extras.<mod_name>
            module = import_module(f".extras.{mod_name}", __package__)
            self._loaded[name] = module
            if console:
                console.log(f"[cyan]Loaded extra module:[/cyan] [bold]{name}[/bold]")
            return module

        except ModuleNotFoundError as e:
            # Provide helpful install command
            install_cmd = f"poetry add {req_pkg}"
            if extra != req_pkg.split(" ")[0]:
                install_cmd = f"poetry install -E {extra}"

            msg = (
                f"[yellow]Extra module '{name}' requires '{req_pkg}'[/yellow]\n"
                f"Install with:\n  [bold cyan]{install_cmd}[/bold cyan]"
            )
            if console:
                console.print(msg)
            else:
                print(msg, file=sys.stderr)

            raise ImportError(f"Missing dependency for extras.{name}: {req_pkg}") from e

    def __dir__(self) -> list[str]:
        return list(self._registry.keys()) + ["help"]

    def help(self) -> None:
        """Show available extra modules and install instructions."""
        from rich.table import Table
        if not console:
            print("Available extras (install with `poetry install -E <name>`):")
            for name in self._registry:
                print(f"  - {name}")
            return

        table = Table(title="utils_devops.extras", show_header=True, header_style="bold magenta")
        table.add_column("Module", style="cyan")
        table.add_column("Install Extras Group", style="green")
        table.add_column("Required Package", style="yellow")

        for name, (_, extra, pkg) in self._registry.items():
            table.add_row(name, extra, pkg)

        console.print(table)

# Instantiate
extras = _LazyExtras()

# --- Top-Level Exports ---
__all__ = [
    "__version__",
    "core",
    "extras",
    # Core re-exports
    "datetimes",
    "envs",
    "files",
    "logs",
    "strings",
    "systems",
    "script_helpers",
]

# --- Optional: CLI Entry Point ---
def _setup_cli() -> None:
    """Internal: register CLI if typer available."""
    try:
        from typer import Typer
        app = Typer(name="utils-devops", help="DevOps automation toolkit")

        @app.command()
        def version() -> None:
            """Show version."""
            print(f"utils_devops {__version__}")

        @app.command()
        def list_extras() -> None:
            """List available extra modules."""
            extras.help()

        # Auto-register CLI from extras if they define `app`
        for name in extras.__dir__():
            mod = getattr(extras, name, None)
            if mod and hasattr(mod, "app") and isinstance(mod.app, Typer):
                app.add_typer(mod.app, name=name.replace("_", "-"))

        app()

    except Exception:
        pass  # CLI not available

# Register console script via pyproject.toml instead