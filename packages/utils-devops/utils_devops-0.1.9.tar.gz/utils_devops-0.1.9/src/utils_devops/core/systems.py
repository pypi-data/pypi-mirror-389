# src/utils_devops/core/systems.py
"""
System Operations Module

This module provides cross-platform utilities for system-level operations, including environment detection, process management, waiting functions, port operations, retry mechanisms, user interactions, command execution, package management, and other OS-related tasks. It supports detection and operations in Docker, Linux (with apt), and Windows (with Chocolatey) environments.

Functions are designed to be lightweight, handle errors gracefully, and use logging from the logger module where appropriate. Cross-platform compatibility is prioritized using libraries like psutil, subprocess, and shutil.

AI Prompt: When implementing or extending this module, focus on cross-platform support (Windows, Linux, Docker detection). Use psutil for process tasks, subprocess for command execution, socket for network checks, and rich for user prompts. Ensure functions log actions and errors. Add docstrings with description and usage for each function. Consider security for password handling and elevate privileges only when necessary. If a function fits better in another module (e.g., files for pure file waits), suggest moving it.

Note: Some functions like wait_for_file might overlap with files.py. If files handles file existence checks, consider moving wait_for_file there and importing it here if needed. For now, included here as per bash examples provided.
"""

from __future__ import annotations

import os
import sys
import platform
import subprocess
import shutil
import time
import socket
import getpass
import ctypes  # For Windows admin check
from typing import Optional, List, Dict, Union, Any
from rich.console import Console
from rich.prompt import Prompt, Confirm

from .logs import get_logger  # Adjust if different

logger = get_logger()
console = Console()

DEFAULT_SYSTEM_TIMEZONE = "Asia/Tehran"  # Change this to your preferred default
_SUDO_PASSWORD: Optional[str] = None

# Public API for IDEs / help()
__all__ = [
    "help",
    # Environment Detection
    "is_windows",
    "is_linux",
    "is_docker",
    "is_root",
    # Process Management
    "check_process_running",
    "kill_process",
    # Waiting Functions
    "wait_for_file",
    "wait_for_port",
    "wait_command_success",
    "retry_cmd",
    # Port Operations
    "check_port_open",
    # User Interaction
    "ask_yes_no",
    "prompt_input",
    "ask_password",
    "confirm_action",
    "ask_choice_list",
    # Command Execution
    "run",
    "exec",
    # Access & Elevation
    "command_exists",
    # Package Management
    "install_chocolatey",
    "install_package",
    "add_apt_repository",
    # Version & Location
    "find_command_location",
    "get_command_version",
    # System Metrics
    "get_cpu_usage",
    "get_memory_info",
    "get_disk_usage",
    # PowerShell (Windows)
    "run_powershell",
    # Utilities
    "list_directory_recursive",
    "readlink_f",
    # Timezone helpers
    "set_system_timezone",
    "get_system_timezone",
    "setup_tehran_timezone",
    # Service Reload
    "reload_service",
    # constants
    "DEFAULT_SYSTEM_TIMEZONE",
]


def help() -> None:
    """Print a brief index of available functions in this module."""
    print(
        """
System Operations Module - AI Function Index
# Environment Detection
is_windows() -> bool: True if running on Windows.
is_linux() -> bool: True if running on Linux.
is_docker() -> bool: True if inside Docker container.
is_root() -> bool: True if running as root/admin.
# Process Management
check_process_running(pattern: str) -> bool: True if process with name/cmdline match exists.
kill_process(pattern: str) -> None: Kill all processes matching pattern, raise if none found.
# Waiting Functions
wait_for_file(file_path: str, timeout: int = 30) -> bool: Wait for file to appear, return True/False.
wait_for_port(host: str = 'localhost', port: int, timeout: int = 30) -> bool: Wait for port to open.
wait_command_success(cmd: str, retries: int = 5, delay: int = 1) -> None: Retry command until success.
retry_cmd: Alias of wait_command_success.
# Port Operations
check_port_open(host: str = 'localhost', port: int) -> bool: True if port is open.
# User Interaction
ask_yes_no(prompt: str = "Confirm (y/n)?") -> bool: Prompt yes/no, return True for yes.
prompt_input(prompt: str = "Enter:") -> str: Prompt for text input.
ask_password(prompt: str = "Password:") -> str: Prompt password (no echo).
confirm_action(action_desc: str) -> None: Warn and confirm before action.
ask_choice_list(prompt: str = "Choose:", options: list[str]) -> str: Select from numbered list.
# Command Execution
run(cmd: Union[str, List[str]], shell: bool = False, cwd: Optional[os.PathLike] = None, env: Optional[Dict[str, str]] = None, no_die: bool = False, dry_run: bool = False, elevated: bool = False, capture: bool = True) -> subprocess.CompletedProcess: Run command with logging, timing, dry-run, sudo support.
# Access & Elevation
command_exists(cmd: str) -> bool: True if command is in PATH.
# Package Management
install_chocolatey() -> None: Install Chocolatey on Windows.
install_package(package_name: str, update_first: bool = True) -> None: Install via apt or choco.
add_apt_repository(repo: str, update_after: bool = True) -> None: Add PPA/repo on Linux.
# Version & Location
find_command_location(cmd: str) -> str | None: Full path to command.
get_command_version(cmd: str) -> str | None: Run --version and return output.
readlink_f(path: str) -> str: Return real (canonical) path, resolving symlinks.
# System Metrics
get_cpu_usage() -> float: Current CPU % usage.
get_memory_info() -> dict: Total/used/free memory stats.
get_disk_usage(path: str = '/') -> dict: Disk usage stats for path.
# PowerShell (Windows)
run_powershell(cmd: str, elevated: bool = False) -> int: Execute PowerShell command.
# Utilities
list_directory_recursive(path: str = '.', detailed: bool = False) -> None: Print ls -alR style tree.
# System Timezone (NEW)
set_system_timezone(tz: Optional[str] = None, confirm: bool = True) -> None: Set OS timezone (default: Asia/Tehran).
get_system_timezone() -> str: Get current OS timezone.
setup_tehran_timezone(confirm: bool = True) -> None: Quick Tehran timezone setup.
DEFAULT_SYSTEM_TIMEZONE = "Asia/Tehran": Configurable default TZ.
# Service Reload
reload_service(service_cmd: Union[list[str], str], test_cmd: Union[list[str], str]) -> bool: Run test_cmd, if success run service_cmd. Log results.
exec(cmd: str|list, elevated: bool = False, show_output: bool = True) -> CompletedProcess:
    Run command, show output in console, log result. String → bash-like, list → safe.
   
run(cmd: str|list, elevated: bool = False, capture: bool = True) -> CompletedProcess:
    Run command safely. String → shell, list → direct. Supports sudo/UAC silently.

"""
    )


# -------------------------------------------------
# Secure sudo / elevation handling
# -------------------------------------------------
def _clear_sudo_cache() -> None:
    """Erase the cached sudo password from memory."""
    global _SUDO_PASSWORD
    _SUDO_PASSWORD = None


def _get_sudo_password(prompt: str = "Enter sudo password: ") -> str:
    """Ask for the sudo password **once per process** – never echoed."""
    global _SUDO_PASSWORD
    if _SUDO_PASSWORD is None:
        _SUDO_PASSWORD = getpass.getpass(prompt)
    return _SUDO_PASSWORD


# ========================
# Command Execution
# ========================


def run(
    cmd: Union[str, List[str]],
    *,
    shell: Optional[bool] = None,
    cwd: Optional[os.PathLike] = None,
    env: Optional[Dict[str, str]] = None,
    no_die: bool = False,
    dry_run: bool = False,
    elevated: bool = False,
    capture: bool = True,
) -> subprocess.CompletedProcess:
    """
    Core run() – now smart about shell.

    Returns:
        subprocess.CompletedProcess
    """
    if shell is None:
        shell = isinstance(cmd, str)

    if isinstance(cmd, (list, tuple)):
        cmd_str = subprocess.list2cmdline(cmd)
        cmd_list: Union[List[str], str] = list(cmd)
    else:
        cmd_str = str(cmd)
        cmd_list = [cmd]

    if dry_run:
        logger.info(f"[DRY-RUN] {cmd_str}")
        return subprocess.CompletedProcess(cmd_list if not shell else cmd_str, 0, stdout="", stderr="")

    stdin_input: Optional[str] = None
    if elevated:
        if is_windows():
            ps = f'Start-Process -Verb RunAs -FilePath powershell -ArgumentList "-Command & {{ {cmd_str} }}" -Wait -PassThru'
            cmd_list = ["powershell", "-NoProfile", "-Command", ps]
            shell = False
        else:
            pw = _get_sudo_password()
            cmd_list = ["sudo", "-S"] + (cmd_list if isinstance(cmd_list, list) else [cmd_str])
            stdin_input = pw + "\n"
            shell = False

    logger.debug(f"Executing: {' '.join(cmd_list) if isinstance(cmd_list, list) else cmd_list}")

    try:
        proc = subprocess.Popen(
            cmd_list if not shell else cmd_str,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=subprocess.PIPE if capture else None,
            stderr=subprocess.PIPE if capture else None,
            stdin=subprocess.PIPE if stdin_input else None,
            text=True,
            shell=shell,
        )

        if stdin_input and proc.stdin:
            proc.stdin.write(stdin_input)
            proc.stdin.flush()
            proc.stdin.close()

        stdout, stderr = proc.communicate()
        rc = proc.returncode

        result = subprocess.CompletedProcess(
            cmd_list if not shell else cmd_str,
            rc,
            stdout=stdout or "",
            stderr=stderr or "",
        )

        if rc == 0:
            logger.info(f"Command succeeded (rc={rc})")
        else:
            logger.error(f"Command failed (rc={rc}) – {stderr.strip() if stderr else ''}")

        if rc != 0 and not no_die:
            raise subprocess.CalledProcessError(rc, cmd_list if not shell else cmd_str, stdout, stderr)

        return result

    finally:
        if elevated and not is_windows():
            _clear_sudo_cache()


# -------------------------------------------------
# Exec helper – shows command + output + logs
# -------------------------------------------------


def exec(
    cmd: Union[str, List[str]],
    *,
    shell: Optional[bool] = None,
    cwd: Optional[os.PathLike] = None,
    env: Optional[Dict[str, str]] = None,
    no_die: bool = False,
    dry_run: bool = False,
    elevated: bool = False,
    capture: bool = True,
    show_output: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run a command and show output.

    - If `cmd` is **str** → runs in shell (like bash)
    - If `cmd` is **list** → runs safely (no shell)
    - `shell=True` only when needed
    """
    # Auto-detect shell mode
    if shell is None:
        shell = isinstance(cmd, str)

    # Forward to run()
    result = run(
        cmd,
        shell=shell,
        cwd=cwd,
        env=env,
        no_die=no_die,
        dry_run=dry_run,
        elevated=elevated,
        capture=capture,
    )

    # Show output
    if not dry_run and show_output:
        cmd_str = cmd if isinstance(cmd, str) else subprocess.list2cmdline(cmd)

        console.print(f"\n[bold cyan]>>> {cmd_str}[/bold cyan]")

        if result.stdout:
            console.print(f"[green]STDOUT:[/green]\n{result.stdout.rstrip()}")

        if result.stderr:
            console.print(f"[red]STDERR:[/red]\n{result.stderr.rstrip()}")

        rc_color = "green" if result.returncode == 0 else "red"
        console.print(f"[{rc_color}]Return code: {result.returncode}[/{rc_color}]\n")

    return result


# ========================
# Section: System Timezone Management
# ========================


def set_system_timezone(tz: Optional[str] = None, confirm: bool = True) -> None:
    """Set OS timezone – default = Asia/Tehran."""
    if tz is None:
        tz = DEFAULT_SYSTEM_TIMEZONE
        logger.info(f"Using default timezone: {tz}")

    if confirm:
        confirm_action(f"change system timezone to {tz}")

    if is_windows():
        win_name = "Iran Standard Time" if tz == "Asia/Tehran" else tz.replace("/", " ")
        cmd = ["tzutil", "/s", win_name]
    else:
        if command_exists("timedatectl"):
            cmd = ["timedatectl", "set-timezone", tz]
        else:
            # Fallback: update /etc/localtime symlink
            cmd = ["ln", "-sf", f"/usr/share/zoneinfo/{tz}", "/etc/localtime"]

    run(cmd, elevated=True)
    logger.info(f"System timezone set to: {tz}")


def get_system_timezone() -> str:
    """Return current OS timezone as string."""
    try:
        if is_windows():
            res = run(["tzutil", "/g"], capture=True)
            return res.stdout.strip().strip('"')
        else:
            if command_exists("timedatectl"):
                res = run(
                    ["timedatectl", "show", "--property=Timezone", "--value"],
                    capture=True,
                )
                return res.stdout.strip()
            else:
                # Fallback
                try:
                    with open("/etc/timezone", "r") as f:
                        return f.read().strip()
                except FileNotFoundError:
                    try:
                        link = os.readlink("/etc/localtime")
                        return link.split("zoneinfo/")[-1]
                    except Exception:
                        return "Unknown"
    except Exception as e:
        logger.warning(f"Failed to read system timezone: {e}")
        return "Unknown"


# ========================
# Section: Quick Default Setup
# ========================


def setup_tehran_timezone(confirm: bool = True) -> None:
    """
    Description: Quick setup for Tehran timezone (Asia/Tehran). Alias for set_system_timezone(default).
    Usage: setup_tehran_timezone(confirm: bool = True) -> None
    """
    set_system_timezone(tz=DEFAULT_SYSTEM_TIMEZONE, confirm=confirm)


# ========================
# Section: Environment Detection
# ========================


def is_windows() -> bool:
    """Description: Checks if the current OS is Windows.
    Usage: is_windows() -> bool
    """
    return platform.system() == "Windows"


def is_linux() -> bool:
    """Description: Checks if the current OS is Linux.
    Usage: is_linux() -> bool
    """
    return platform.system() == "Linux"


def is_docker() -> bool:
    """Description: Checks if running inside a Docker container (Linux only).
    Usage: is_docker() -> bool
    """
    if not is_linux():
        return False
    try:
        with open("/proc/1/cgroup", "r") as f:
            content = f.read()
            return "docker" in content or "/docker/" in content
    except Exception as e:
        logger.debug(f"Failed to check Docker: {e}")
        return False


def is_root() -> bool:
    """Description: Checks if the current process is running as root/admin.
    Usage: is_root() -> bool
    """
    if is_windows():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception as e:
            logger.debug(f"Failed to check admin on Windows: {e}")
            return False
    else:
        return os.getuid() == 0


# ========================
# Section: Process Management
# ========================

import psutil  # Required dependency


def check_process_running(pattern: str) -> bool:
    """Description: Returns True if a process matching the pattern (name or cmdline) is running.
    Usage: check_process_running(pattern: str) -> bool
    """
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        cmdline = " ".join(proc.info.get("cmdline") or [])
        name = proc.info.get("name") or ""
        if pattern in name or pattern in cmdline:
            return True
    return False


def kill_process(pattern: str) -> None:
    """Description: Kills processes matching the pattern (name or cmdline). Raises exception if fails.
    Usage: kill_process(pattern: str) -> None
    """
    killed = False
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        cmdline = " ".join(proc.info.get("cmdline") or [])
        name = proc.info.get("name") or ""
        if pattern in name or pattern in cmdline:
            try:
                proc.kill()
                killed = True
            except psutil.NoSuchProcess:
                pass
            except Exception as e:
                logger.error(f"Failed to kill process {proc.pid}: {e}")
                raise
    if not killed:
        raise ValueError(f"No process matching '{pattern}' found to kill.")


# ========================
# Section: Waiting Functions
# ========================


def wait_for_file(file_path: str, timeout: int = 30) -> bool:
    """Description: Waits for a file to exist, up to timeout seconds. Returns True if appears, False on timeout.
    Usage: wait_for_file(file_path: str, timeout: int = 30) -> bool
    """
    start = time.time()
    while not os.path.exists(file_path):
        if time.time() - start > timeout:
            logger.error(f"Timeout waiting for file: {file_path}")
            return False
        time.sleep(1)
    logger.info(f"File appeared: {file_path}")
    return True


def wait_for_port(host: str = "localhost", port: int = 80, timeout: int = 30) -> bool:
    """Description: Waits for a port to become open, up to timeout seconds. Returns True if open, False on timeout.
    Usage: wait_for_port(host: str = 'localhost', port: int, timeout: int = 30) -> bool
    """
    start = time.time()
    while not check_port_open(host, port):
        if time.time() - start > timeout:
            logger.error(f"Timeout waiting for {host}:{port}")
            return False
        time.sleep(1)
    logger.info(f"Port open: {host}:{port}")
    return True


def wait_command_success(cmd: str, retries: int = 5, delay: int = 1) -> None:
    """Description: Retries a command until it succeeds, up to retries times with delay. Raises exception on failure.
    Usage: wait_command_success(cmd: str, retries: int = 5, delay: int = 1) -> None
    """
    for attempt in range(1, retries + 1):
        try:
            subprocess.check_call(cmd, shell=True)
            logger.info(f"Command succeeded on attempt {attempt}: {cmd}")
            return
        except subprocess.CalledProcessError as e:
            logger.warning(f"Attempt {attempt} failed: {cmd} (rc={e.returncode})")
            time.sleep(delay)
    raise RuntimeError(f"Command failed after {retries} retries: {cmd}")


# Alias for wait_command_success
retry_cmd = wait_command_success


# ========================
# Section: Port Operations
# ========================


def check_port_open(host: str = "localhost", port: int = 80) -> bool:
    """Description: Checks if a port is open on the host.
    Usage: check_port_open(host: str = 'localhost', port: int) -> bool
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    finally:
        sock.close()


# ========================
# Section: User Interaction
# ========================


def ask_yes_no(prompt: str = "Confirm (y/n)?") -> bool:
    """Description: Prompts the user for yes/no input. Returns True for yes, False for no.
    Usage: ask_yes_no(prompt: str = "Confirm (y/n)?") -> bool
    """
    return Confirm.ask(f"[magenta]{prompt}[/magenta]")


def prompt_input(prompt: str = "Enter:") -> str:
    """Description: Prompts the user for input and returns the response.
    Usage: prompt_input(prompt: str = "Enter:") -> str
    """
    return Prompt.ask(f"[magenta]{prompt}[/magenta]")   


def ask_password(prompt: str = "Password:") -> str:
    """Description: Prompts for password input (no echo) and returns it.
    Usage: ask_password(prompt: str = "Password:") -> str
    """
    console.print(f"[magenta]{prompt}[/magenta]", end=" ")
    return getpass.getpass("")


def confirm_action(action_desc: str) -> None:
    """Description: Logs a warning about the action and asks for confirmation. Raises exception if not confirmed.
    Usage: confirm_action(action_desc: str) -> None
    """
    logger.warning(f"About to {action_desc}. Continue?")
    if not ask_yes_no():
        raise RuntimeError("Action cancelled by user.")


def ask_choice_list(prompt: str = "Choose:", options: Optional[List[str]] = None) -> str:
    """Description: Displays a list of options and prompts for choice by number. Returns the chosen option.
    Usage: ask_choice_list(prompt: str = "Choose:", options: list[str]) -> str
    """
    if options is None:
        options = []
    for i, opt in enumerate(options, 1):
        console.print(f"{i}) {opt}")
    choice = Prompt.ask(f"[magenta]{prompt}[/magenta]")
    if choice.isdigit() and 1 <= int(choice) <= len(options):
        return options[int(choice) - 1]
    raise ValueError("Invalid choice.")


# ========================
# Section: Access and Elevation
# ========================


def command_exists(cmd: str) -> bool:
    """Description: Checks if a command is available in PATH.
    Usage: command_exists(cmd: str) -> bool
    """
    return shutil.which(cmd) is not None


# ========================
# Section: Package Management
# ========================


def install_chocolatey() -> None:
    """Description: Installs Chocolatey on Windows if not present.
    Usage: install_chocolatey() -> None
    """
    if not is_windows():
        raise NotImplementedError("Chocolatey is for Windows only.")
    if command_exists("choco"):
        logger.info("Chocolatey already installed.")
        return
    ps_cmd = "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    run(f"powershell -Command \"{ps_cmd}\"", elevated=True)
    logger.info("Chocolatey installed.")


def install_package(package_name: str, update_first: bool = True) -> None:
    """Description: Installs a package using apt (Linux) or Chocolatey (Windows). Updates repositories if update_first.
    Usage: install_package(package_name: str, update_first: bool = True) -> None
    """
    if is_windows():
        install_chocolatey()
        run(f"choco install {package_name} -y", elevated=True)
    elif is_linux():
        if update_first:
            run("apt update", elevated=True)
        run(f"apt install {package_name} -y", elevated=True)
    else:
        raise NotImplementedError("Unsupported OS for package installation.")


def add_apt_repository(repo: str, update_after: bool = True) -> None:
    """Description: Adds an APT repository on Linux (e.g., ppa:user/repo). Updates if update_after.
    Usage: add_apt_repository(repo: str, update_after: bool = True) -> None
    """
    if not is_linux():
        raise NotImplementedError("APT repositories are for Linux only.")
    run(f"add-apt-repository {repo} -y", elevated=True)
    if update_after:
        run("apt update", elevated=True)


# ========================
# Section: Version and Location
# ========================


def find_command_location(cmd: str) -> Optional[str]:
    """Description: Returns the full path to the command if found, else None.
    Usage: find_command_location(cmd: str) -> str | None
    """
    return shutil.which(cmd)


def get_command_version(cmd: str) -> Optional[str]:
    """Description: Returns the version string of the command, or None if fails.
    Usage: get_command_version(cmd: str) -> str | None
    """
    if not command_exists(cmd):
        return None
    try:
        res = run([cmd, "--version"], capture=True)
        return res.stdout.strip()
    except Exception as e:
        logger.debug(f"Failed to get version for {cmd}: {e}")
        return None


def readlink_f(path: str) -> str:
    """Description: Returns the real (canonical) path, resolving all symlinks (like readlink -f).
    Usage: readlink_f(path: str) -> str
    """
    try:
        real_path = os.path.realpath(path)
        logger.debug(f"Resolved path {path} to {real_path}")
        return real_path
    except Exception as e:
        logger.error(f"Failed to resolve path {path}: {e}")
        raise RuntimeError(f"Failed to resolve path {path}: {e}") from e


# ========================
# Section: Other OS Utilities
# ========================


def list_directory_recursive(path: str = ".", detailed: bool = False) -> None:
    """Description: Prints a recursive directory listing, similar to ls -alR. Detailed includes permissions and size.
    Usage: list_directory_recursive(path: str = '.', detailed: bool = False) -> None
    """
    for root, dirs, files in os.walk(path):
        console.print(f"{root}:")
        if detailed:
            total_size = 0
            for name in dirs + files:
                full = os.path.join(root, name)
                try:
                    stat = os.stat(full)
                    mode = oct(stat.st_mode)[-4:]  # Simplified permissions
                    size = stat.st_size
                    total_size += size if os.path.isfile(full) else 0
                    console.print(f"{mode} {size:8} {name}")
                except Exception as e:
                    console.print(f"Error accessing {name}: {e}")
            console.print(f"total {total_size}")
        else:
            for name in dirs + files:
                console.print(name)
        console.print("")


# Additional useful functions from research/thinking:
# System metrics using psutil


def get_cpu_usage() -> float:
    """Description: Returns current CPU usage percentage.
    Usage: get_cpu_usage() -> float
    """
    return psutil.cpu_percent(interval=1)


def get_memory_info() -> Dict[str, Union[int, float]]:
    """Description: Returns memory info as dict (total, available, used, percent).
    Usage: get_memory_info() -> dict (total, available, used, percent)
    """
    mem = psutil.virtual_memory()
    return {"total": mem.total, "available": mem.available, "used": mem.used, "percent": mem.percent}


def get_disk_usage(path: str = "/") -> Dict[str, Union[int, float]]:
    """Description: Returns disk usage for the given path as dict (total, used, free, percent).
    Usage: get_disk_usage(path: str = '/') -> dict (total, used, free, percent)
    """
    disk = psutil.disk_usage(path)
    return {"total": disk.total, "used": disk.used, "free": disk.free, "percent": disk.percent}


# Run PowerShell command (Windows only)


def run_powershell(cmd: str, elevated: bool = False) -> int:
    """Description: Runs a PowerShell command on Windows.
    Usage: run_powershell(cmd: str, elevated: bool = False) -> int (return code)
    """
    if not is_windows():
        raise NotImplementedError("PowerShell is for Windows only.")
    ps_cmd = f"powershell -Command \"{cmd}\""
    res = run(ps_cmd, elevated=elevated)
    return res.returncode


# ========================
# Section: Service Reload
# ========================


def reload_service(service_cmd: Union[List[str], str], test_cmd: Union[List[str], str]) -> bool:
    """Description: Runs test_cmd (e.g., nginx -t), if success runs service_cmd (e.g., nginx -s reload). Logs results. Returns True on success, False otherwise.
    Usage: reload_service(service_cmd: list[str] | str, test_cmd: list[str] | str) -> bool
    """
    logger.info(f"Testing with: {test_cmd}")
    try:
        test_res = run(test_cmd, capture=True, no_die=True)
        if test_res.returncode != 0:
            logger.error(f"Test failed (rc={test_res.returncode}): {test_res.stderr.strip()}")
            return False
        logger.info("Test succeeded.")
        
        logger.info(f"Reloading with: {service_cmd}")
        reload_res = run(service_cmd, elevated=True, capture=True)
        if reload_res.returncode == 0:
            logger.info("Reload succeeded.")
            return True
        else:
            logger.error(f"Reload failed (rc={reload_res.returncode}): {reload_res.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Reload process failed: {e}")
        return False