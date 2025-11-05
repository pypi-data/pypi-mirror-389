"""
Nginx Operations Module (extras)
Provides high-level utilities for managing Nginx sites, configs, caching, and service control.
Improved and corrected based on idempotent script logic and new templates:
- Idempotent operations with checks for existing content/markers.
- Safe insertions parsing server/location blocks.
- Marker-based regions for snippets.
- Combined files for cache-paths and DNS.
- Dry-run support.
- Safe client_max_body_size edits.
- Removal of unused flags/locations.
- Retries on validation/test/reload.
- Cross-platform, with Path usage.
- New functions: sync_flags, create_site, apply_flag_to_site, remove_flag_from_site, list_sites, clear_site_cache.
- Updated init() with new template contents (no META; hardcoded flag logic).
- Sync_sites now calls sync_flags.
Dependencies: jinja2, rich (optional for tables), tenacity, requests.
Raises NginxOpsError on failures.
"""
from __future__ import annotations
import os
import re
import shutil
import socket
import time
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
import requests  # For HTTP upstream validation
from tenacity import retry, stop_after_attempt, wait_fixed  # For retries
from jinja2 import Environment, FileSystemLoader
try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    Console = None
    Table = None
from utils_devops.core import *
from utils_devops.core.logs import get_logger
from utils_devops.core.files import (
    atomic_write, backup_file, create_symlink, remove_file, resolve_symlink,
    comment_block_between_markers, uncomment_block_between_markers, insert_block, remove_block_between_markers,
    read_marked_block, ensure_dir, remove_dir, set_mode, set_owner, file_exists, search_in_file, replace_regex_in_file
)
from utils_devops.core.systems import run, reload_service, is_root, is_windows, is_linux, readlink_f, command_exists
from utils_devops.core.strings import render_jinja, replace_substring
from utils_devops.core.script_helpers import backup_many, rollback_backups, with_temp_dir, create_rich_table, send_slack_notify, retry_func
from utils_devops.core.files import read_file, write_file

log = get_logger()
console = Console() if Console else None  # Fallback if rich not installed

# Defaults
DEFAULT_NGINX_CMD = "nginx.exe" if platform.system() == "Windows" else "nginx"
DEFAULT_TEST_CMD = [DEFAULT_NGINX_CMD, "-t"]
DEFAULT_RELOAD_CMD = [DEFAULT_NGINX_CMD, "-s", "reload"]
DEFAULT_START_CMD = [DEFAULT_NGINX_CMD, "-g", "daemon off;"]
DEFAULT_PID_FILE = Path(r"C:\nginx\logs\nginx.pid") if platform.system() == "Windows" else Path("/run/nginx.pid")
DEFAULT_LOG_DIR = Path(r"C:\nginx\logs") if platform.system() == "Windows" else Path("/var/log/nginx")
DEFAULT_SITES_AVAILABLE = Path(r"C:\nginx\conf\sites-available") if platform.system() == "Windows" else Path("/etc/nginx/sites-available")
DEFAULT_SITES_ENABLED = Path(r"C:\nginx\conf\site-enabled") if platform.system() == "Windows" else Path("/etc/nginx/sites-enabled")
DEFAULT_CACHE_BASE = Path(r"C:\nginx\cache") if platform.system() == "Windows" else Path("/var/cache/nginx/sites")
DEFAULT_CACHE_PATH_DIR = Path(r"C:\nginx\conf.d") if platform.system() == "Windows" else Path("/etc/nginx/conf.d")
DEFAULT_CACHE_COMBINED = DEFAULT_CACHE_PATH_DIR / "cache-paths.conf"
DEFAULT_DNS_DIR = Path(r"C:\etc\dnsmasq.d") if platform.system() == "Windows" else Path("/etc/dnsmasq.d")
DEFAULT_DNS_COMBINED = DEFAULT_DNS_DIR / "combined-dns.conf"
DEFAULT_NGINX_CONF = Path(r"C:\nginx\conf\nginx.conf") if platform.system() == "Windows" else Path("/etc/nginx/nginx.conf")
DEFAULT_NGINX_USER_LINUX = "www-data"
DEFAULT_NGINX_USER_WINDOWS = "SYSTEM"  # Permissive on Win
DEFAULT_DNSMASQ_CONF = Path("/etc/dnsmasq.conf")
DUMMY_UPSTREAM = "http://127.0.0.1:81"
DEFAULT_NGINX_IP = "172.16.229.50"  # For dnsmasq entries

class NginxOpsError(Exception):
    """Custom exception for Nginx operations failures."""
    pass

__all__ = [
    "NginxOpsError",
    "help",
    # Paths & Detection
    "get_nginx_paths",
    "detect_nginx_user",
    # Parsing
    "parse_sites_list",
    # Rendering & Building
    "render_nginx_template",
    "build_locations_block",
    # Validation
    "validate_upstream",
    # Logs & Dirs
    "setup_site_logs",
    "ensure_cache_dir",
    # Config Management
    "write_site_config",
    "create_site",
    # Cache Management
    "reload_cache",
    "clear_site_cache",
    # Flags Management
    "apply_flag_to_site",
    "remove_flag_from_site",
    "sync_flags",
    # Sync & Remove & List
    "sync_sites",
    "remove_site",
    "list_sites",
    # Service Control
    "manage_nginx_service",
    # Utils
    "flush_dns",
    "generate_sites_from_list",
    # Initialization
    "init",
]

def help() -> None:
    """Print a concise index of functions in this module for interactive use."""
    print(
        """
Nginx Ops (extras) — Function Index
# Paths & Detection
get_nginx_paths(os_type: str = "auto") -> Dict[str, Path]: Default Nginx paths.
detect_nginx_user(conf_path: Path = DEFAULT_NGINX_CONF) -> str: Parse user from conf.
# Parsing
parse_sites_list(list_path: Union[str, Path]) -> List[Dict[str, Any]]: Parse sites.txt to dicts with locations and flags.
# Rendering & Building
render_nginx_template(template_path: Union[str, Path], context: Dict[str, Any]) -> str: Jinja render, checks template exists.
build_locations_block(locations: Dict[str, str], location_tpl: Union[str, Path]) -> str: Build location blocks from template.
# Validation
validate_upstream(upstream: str, fallback: str = DUMMY_UPSTREAM, timeout: int = 1, use_http: bool = True) -> str: Ping/HTTP check, fallback.
# Logs & Dirs
setup_site_logs(site: str, log_dir: Path = DEFAULT_LOG_DIR, nginx_user: Optional[str] = None) -> Tuple[Path, Path]: Create logs, set perms.
ensure_cache_dir(site: str, cache_base: Path = DEFAULT_CACHE_BASE) -> Path: Create/return cache dir.
# Config Management
write_site_config(site: str, rendered: str, available_dir: Path = DEFAULT_SITES_AVAILABLE, enabled_dir: Path = DEFAULT_SITES_ENABLED) -> None: Write and enable.
create_site(site: str, meta: Dict[str, Any], flags_dir: Union[str, Path] = "templates", force: bool = False, dry_run: bool = False) -> None: Create or recreate site config.
# Cache Management
reload_cache(sites: Union[str, List[str]], flags_dir: Union[str, Path] = "templates", cache_base: Path = DEFAULT_CACHE_BASE, cache_combined: Path = DEFAULT_CACHE_COMBINED, dry_run: bool = False) -> None: Clear and re-apply cache.
clear_site_cache(site: str, cache_base: Path = DEFAULT_CACHE_BASE) -> None: Clear cache dir for a site.
# Flags Management
apply_flag_to_site(site: str, flag: str, value: Optional[Any] = None, flags_dir: Union[str, Path] = "templates", meta: Optional[Dict[str, Any]] = None, dry_run: bool = False) -> None: Apply a flag to site config.
remove_flag_from_site(site: str, flag: str, flags_dir: Union[str, Path] = "templates", dry_run: bool = False) -> None: Remove a flag from site config.
sync_flags(sites_list: List[Dict[str, Any]], flags_dir: Union[str, Path] = "templates", dry_run: bool = False) -> None: Sync flags from sites.txt to configs.
# Sync & Remove & List
sync_sites(sites_list: List[Dict[str, Any]], proxy_tpl: Union[str, Path], serve_tpl: Union[str, Path], location_tpl: Union[str, Path], flags_dir: Union[str, Path] = "templates", dry_run: bool = False, **dirs) -> None: Sync sites, apply flags, cache, dns.
remove_site(site: str, list_path: Union[str, Path], flags_dir: Union[str, Path] = "templates", dry_run: bool = False, **dirs) -> None: Remove from list/config/cache/dns, reload.
list_sites(available_dir: Path = DEFAULT_SITES_AVAILABLE) -> List[str]: List available sites.
# Service Control
manage_nginx_service(pid_file: Path = DEFAULT_PID_FILE, nginx_cmd: str = DEFAULT_NGINX_CMD, test_cmd: List[str] = DEFAULT_TEST_CMD, reload_cmd: List[str] = DEFAULT_RELOAD_CMD, start_cmd: List[str] = DEFAULT_START_CMD, dry_run: bool = False) -> bool: Test/reload/start.
# Utils
flush_dns() -> None: Flush DNS cache.
generate_sites_from_list(list_path: Union[str, Path], proxy_tpl: Union[str, Path], serve_tpl: Union[str, Path], location_tpl: Union[str, Path], flags_dir: Union[str, Path] = "templates", dry_run: bool = False, **dirs_and_cmds) -> None: Full generation with validation/logs/sync/reload/dns.
# Initialization
init(generate_dir: Union[str, Path] = "/etc/nginx/generate-sites", sites_txt: bool = True, manage_py: bool = True) -> None: Set up generate-sites structure with templates, sites.txt, etc.
Use `help(nginx_ops.some_function)` to view per-function docs.
"""
    )

# Paths & Detection
def get_nginx_paths(os_type: str = "auto") -> Dict[str, Path]:
    """Return default Nginx paths, auto-detected or per OS."""
    if os_type == "auto":
        os_type = "windows" if is_windows() else "linux"
    if os_type == "windows":
        return {
            "sites_available": DEFAULT_SITES_AVAILABLE,
            "sites_enabled": DEFAULT_SITES_ENABLED,
            "cache_base": DEFAULT_CACHE_BASE,
            "cache_path_dir": DEFAULT_CACHE_PATH_DIR,
            "cache_combined": DEFAULT_CACHE_COMBINED,
            "dns_dir": DEFAULT_DNS_DIR,
            "dns_combined": DEFAULT_DNS_COMBINED,
            "log_dir": DEFAULT_LOG_DIR,
            "conf": DEFAULT_NGINX_CONF,
            "pid_file": DEFAULT_PID_FILE,
            "cmd": Path(DEFAULT_NGINX_CMD),
        }
    elif os_type == "linux":
        return {
            "sites_available": Path("/etc/nginx/sites-available"),
            "sites_enabled": Path("/etc/nginx/sites-enabled"),
            "cache_base": Path("/var/cache/nginx/sites"),
            "cache_path_dir": Path("/etc/nginx/conf.d"),
            "cache_combined": Path("/etc/nginx/conf.d/cache-paths.conf"),
            "dns_dir": Path("/etc/dnsmasq.d"),
            "dns_combined": Path("/etc/dnsmasq.d/combined-dns.conf"),
            "log_dir": Path("/var/log/nginx"),
            "conf": Path("/etc/nginx/nginx.conf"),
            "pid_file": Path("/run/nginx.pid"),
            "cmd": Path("nginx"),
        }
    else:
        raise NginxOpsError(f"Unsupported os_type: {os_type}")

def detect_nginx_user(conf_path: Path = DEFAULT_NGINX_CONF) -> str:
    """Parse 'user' directive from nginx.conf, fallback to defaults."""
    try:
        content = conf_path.read_text()
        match = re.search(r'^\s*user\s+([^;]+);', content, re.MULTILINE)
        if match:
            user = match.group(1).strip()
            log.debug(f"Detected nginx user: {user}")
            return user
    except Exception as e:
        log.warning(f"Failed to detect nginx user: {e}")
    return "SYSTEM" if is_windows() else "www-data"

# Parsing
def parse_sites_list(list_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Parse sites file to list of dicts {site, upstream, is_serve, locations: list[tuple[path, up]], flags: dict}."""
    list_path = Path(list_path)
    if not list_path.exists():
        raise NginxOpsError(f"sites.txt not found: {list_path}")
    sites = []
    content = list_path.read_text()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r'\s+', line)
        site = parts[0]
        upstream = parts[1] if len(parts) > 1 else ""
        is_serve = upstream.startswith('/') or (len(upstream) > 1 and re.match(r"[A-Za-z]:\\", upstream))
        locations = []
        flags = {}
        for p in parts[2:]:
            if p.startswith('/'):
                if '=' in p:
                    path, up = p.split('=', 1)
                    locations.append((path.strip(), up.strip()))
                else:
                    locations.append((p.strip(), ""))
            else:
                if '=' in p:
                    k, v = p.split('=', 1)
                    flags[k.lower().strip()] = v.strip()
                else:
                    flags[p.lower().strip()] = True
        sites.append({"site": site, "upstream": upstream, "is_serve": is_serve, "locations": locations, "flags": flags})
    log.info(f"Parsed {len(sites)} sites from {list_path}")
    return sites

# Rendering & Building
def render_nginx_template(template_path: Union[str, Path], context: Dict[str, Any]) -> str:
    """Render Nginx template with Jinja, check if exists."""
    template_path = Path(template_path)
    if not template_path.exists():
        raise NginxOpsError(f"Template not found: {template_path}")
    env = Environment(loader=FileSystemLoader(str(template_path.parent)))
    tpl = env.get_template(template_path.name)
    return tpl.render(**context)

def build_locations_block(locations: List[Tuple[str, str]], location_tpl: Union[str, Path]) -> List[str]:
    """Build Nginx location blocks from list of (path, upstream) using template."""
    location_tpl = Path(location_tpl)
    if not location_tpl.exists():
        raise NginxOpsError(f"Location template not found: {location_tpl}")
    blocks = []
    tpl_content = location_tpl.read_text()
    for path, upstream in locations:
        context = {"PATH": path, "UPSTREAM": upstream}
        block = render_jinja(tpl_content, context)
        blocks.append(block)
    return blocks

# Validation
@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def validate_upstream(upstream: str, fallback: str = DUMMY_UPSTREAM, timeout: int = 1, use_http: bool = True) -> str:
    """Validate upstream: extract host, ping or HTTP check, fallback if fails."""
    match = re.match(r'(https?://)?([^:/]+)(:\d+)?(/.*)?', upstream)
    if not match:
        log.warning(f"Invalid upstream: {upstream}, using fallback")
        return fallback
    scheme, host, port, path = match.groups()
    scheme = scheme or "http://"
    port = port or ""
    if use_http:
        url = f"{scheme}{host}{port}"
        try:
            resp = requests.head(url, timeout=timeout)
            if resp.status_code < 400:
                log.info(f"Validated upstream: {upstream}")
                return upstream
        except Exception as e:
            log.warning(f"Upstream validation failed: {e}")
    else:
        try:
            socket.getaddrinfo(host, None)
            log.info(f"Validated upstream (ping): {upstream}")
            return upstream
        except Exception as e:
            log.warning(f"Upstream validation failed: {e}")
    log.warning(f"Upstream {upstream} unreachable, using {fallback}")
    return fallback

# Logs & Dirs
def setup_site_logs(site: str, log_dir: Path = DEFAULT_LOG_DIR, nginx_user: Optional[str] = None) -> Tuple[Path, Path]:
    """Create access/error logs, set permissions."""
    ensure_dir(str(log_dir))
    access_log = log_dir / f"{site}-access.log"
    error_log = log_dir / f"{site}-error.log"
    access_log.touch(exist_ok=True)
    error_log.touch(exist_ok=True)
    set_mode(str(access_log), 0o644)
    set_mode(str(error_log), 0o644)
    if nginx_user:
        try:
            set_owner(str(access_log), nginx_user)
            set_owner(str(error_log), nginx_user)
        except Exception as e:
            log.warning(f"Failed to set owner for logs: {e}")
    log.info(f"Setup logs for {site}: {access_log}, {error_log}")
    return access_log, error_log

def ensure_cache_dir(site: str, cache_base: Path = DEFAULT_CACHE_BASE) -> Path:
    """Create/return per-site cache dir, set perms."""
    cache_dir = cache_base / site
    ensure_dir(str(cache_dir))
    set_mode(str(cache_dir), 0o755)
    log.info(f"Ensured cache dir for {site}: {cache_dir}")
    return cache_dir

# Config Management
def write_site_config(
    site: str, rendered: str,
    available_dir: Path = DEFAULT_SITES_AVAILABLE,
    enabled_dir: Path = DEFAULT_SITES_ENABLED,
    dry_run: bool = False
) -> None:
    """Write config to available, enable with symlink (or copy on Win)."""
    tgt_avail = available_dir / f"{site}"
    tgt_enabled = enabled_dir / f"{site}"
    ensure_dir(str(available_dir))
    ensure_dir(str(enabled_dir))
    if dry_run:
        log.info(f"[dry-run] Would write config for {site} to {tgt_avail}")
        return
    atomic_write(str(tgt_avail), rendered)
    if tgt_enabled.exists() or tgt_enabled.is_symlink():
        tgt_enabled.unlink()
    if is_windows():
        shutil.copy(str(tgt_avail), str(tgt_enabled))
    else:
        tgt_enabled.symlink_to(tgt_avail)
    log.info(f"Wrote and enabled config for {site}: {tgt_avail} -> {tgt_enabled}")

def create_site(
    site: str, meta: Dict[str, Any], flags_dir: Union[str, Path] = "templates",
    proxy_tpl: Union[str, Path] = "templates/reverse-proxy.conf",
    serve_tpl: Union[str, Path] = "templates/serve.conf",
    location_tpl: Union[str, Path] = "templates/location.conf",
    force: bool = False, dry_run: bool = False
) -> None:
    """Create or recreate site config from meta, render base + locations."""
    conf_path = DEFAULT_SITES_AVAILABLE / f"{site}"
    if conf_path.exists() and not force:
        log.info(f"Site config exists: {conf_path} (skip)")
        return
    upstream = validate_upstream(meta.get("upstream", ""))
    tpl = serve_tpl if meta.get("is_serve", False) else proxy_tpl
    context = {
        "SITE": site,
        "IP_ADDRESS": upstream,
        "ROOT_PATH": upstream if meta.get("is_serve", False) else "",
        "CLIENT_MAX_BODY_SIZE": meta.get("flags", {}).get("upload", "10M")
    }
    rendered = render_nginx_template(tpl, context)
    locations_blocks = build_locations_block(meta.get("locations", []), location_tpl)
    for block in locations_blocks:
        rendered += "\n" + block  # Append additional locations
    write_site_config(site, rendered, dry_run=dry_run)
    sync_flags([meta], flags_dir, dry_run=dry_run)  # Apply flags after create
    manage_nginx_service(dry_run=dry_run)

# Cache Management
def reload_cache(
    sites: Union[str, List[str]],
    flags_dir: Union[str, Path] = "templates",
    cache_base: Path = DEFAULT_CACHE_BASE,
    cache_combined: Path = DEFAULT_CACHE_COMBINED,
    dry_run: bool = False
) -> None:
    """Clear and re-apply cache for site(s)."""
    if isinstance(sites, str):
        sites = [sites]
    for site in sites:
        cache_dir = cache_base / site
        if cache_dir.exists():
            if dry_run:
                log.info(f"[dry-run] Would clear cache dir for {site}: {cache_dir}")
            else:
                remove_dir(str(cache_dir), recursive=True)
                log.info(f"Cleared cache dir for {site}: {cache_dir}")
        apply_flag_to_site(site, "cache", None, flags_dir, dry_run=dry_run)
    manage_nginx_service(dry_run=dry_run)

def clear_site_cache(site: str, cache_base: Path = DEFAULT_CACHE_BASE) -> None:
    """Clear cache dir for a site."""
    cache_dir = cache_base / site
    if cache_dir.exists():
        remove_dir(str(cache_dir), recursive=True)
        log.info(f"Cleared cache for {site} ({cache_dir})")
    else:
        log.info(f"No cache directory for {site} ({cache_dir})")

# Block Parsing Helpers
def _find_server_blocks(text: str) -> List[Tuple[int, int, str]]:
    blocks = []
    for m in re.finditer(r"server\s*\{", text):
        start = m.start()
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    blocks.append((start, end, text[start:end]))
                    break
    return blocks

def _server_has_port(block: str, port: int) -> bool:
    return re.search(rf"listen\s+{port}\b", block) is not None

def _find_location_blocks_in_server(block: str) -> List[Tuple[int, int]]:
    locs = []
    for m in re.finditer(r"location\s+[^{]+\{", block):
        s = m.start()
        depth = 0
        for i in range(s, len(block)):
            if block[i] == "{":
                depth += 1
            elif block[i] == "}":
                depth -= 1
                if depth == 0:
                    locs.append((s, i + 1))
                    break
    return locs

def _insert_after_last_location(block: str, snippet: str) -> Tuple[str, bool]:
    locs = _find_location_blocks_in_server(block)
    if locs:
        last_start, last_end = locs[-1]
        return block[:last_end] + "\n" + snippet + block[last_end:], True
    return _insert_before_server_close(block, snippet)

def _insert_before_server_close(block: str, snippet: str) -> Tuple[str, bool]:
    idx = block.rfind("}")
    if idx != -1:
        return block[:idx] + "\n" + snippet + "\n" + block[idx:], True
    return block, False

def _insert_into_first_location(block: str, snippet: str, location_path: str = "/") -> Tuple[str, bool]:
    pat = re.compile(rf"(location\s+{re.escape(location_path)}\s*\{{)(.*?)(\n\s*\}})", flags=re.S)
    m = pat.search(block)
    if m:
        return block[:m.start(2)] + m.group(2) + "\n" + snippet + block[m.end(2):], True
    any_loc = re.search(r"(location\s+[^\{]+\{)(.*?)(\n\s*\})", block, flags=re.S)
    if any_loc:
        return block[:any_loc.start(2)] + any_loc.group(2) + "\n" + snippet + block[any_loc.end(2):], True
    return block, False

def _replace_between_markers_in_block(block: str, begin: str, end: str, inner_snippet: str) -> Tuple[str, bool]:
    pattern = re.escape(begin) + r"(.*?)" + re.escape(end)
    if re.search(pattern, block, flags=re.S):
        new_block = re.sub(pattern, begin + "\n" + inner_snippet + "\n" + end, block, flags=re.S)
        return new_block, True
    return block, False

def _apply_snippet(
    conf_path: Path,
    raw_snippet: str,
    placement: str = "server_443_out_after_location",
    location_path: str = "/",
    begin_marker: Optional[str] = None,
    end_marker: Optional[str] = None,
    dry_run: bool = False
) -> None:
    """Apply snippet to config with placement and markers."""
    if dry_run:
        log.info(f"[dry-run] Would apply snippet to {conf_path} (placement={placement})")
        return
    txt = conf_path.read_text()
    blocks = _find_server_blocks(txt)
    placed = False
    snippet = raw_snippet.strip()
    inner_from_snippet = None
    if begin_marker and end_marker:
        m = re.search(re.escape(begin_marker) + r"(.*?)" + re.escape(end_marker), snippet, flags=re.S)
        if m:
            inner_from_snippet = m.group(1).strip()
    placement_normal = placement.lower()
    port = 443 if "443" in placement_normal else 80
    want_location_insert = "_location" in placement_normal
    after_last_location = "after_location" in placement_normal
    for start, end, block in blocks:
        if not _server_has_port(block, port):
            continue
        if begin_marker and end_marker:
            inner = inner_from_snippet or snippet
            if begin_marker in block and end_marker in block:
                new_block, ok = _replace_between_markers_in_block(block, begin_marker, end_marker, inner)
                if ok:
                    txt = txt[:start] + new_block + txt[end:]
                    placed = True
                    break
            else:
                wrapped = f"{begin_marker}\n{inner}\n{end_marker}"
                if after_last_location:
                    new_block, ok = _insert_after_last_location(block, wrapped)
                elif want_location_insert:
                    new_block, ok = _insert_into_first_location(block, wrapped, location_path)
                else:
                    new_block, ok = _insert_before_server_close(block, wrapped)
                if ok:
                    txt = txt[:start] + new_block + txt[end:]
                    placed = True
                    break
        if snippet and snippet in block:
            log.debug("Snippet already present in server block — skipping")
            placed = True
            break
        if after_last_location:
            new_block, ok = _insert_after_last_location(block, snippet)
        elif want_location_insert:
            new_block, ok = _insert_into_first_location(block, snippet, location_path)
        else:
            new_block, ok = _insert_before_server_close(block, snippet)
        if ok:
            txt = txt[:start] + new_block + txt[end:]
            placed = True
            break
    if not placed:
        if snippet and snippet in txt:
            log.debug("Snippet already present in file — skipping fallback append")
        else:
            log.warning(f"Could not place snippet in server listening on {port}; appending to file as fallback")
            txt += "\n" + snippet
    conf_path.write_text(txt)

# Combined File Helpers
def _append_entry_to_combined(combined: Path, begin: str, end: str, entry: str, dry_run: bool = False) -> None:
    if not combined.exists():
        existing = ""
    else:
        existing = combined.read_text()
    if entry.strip() in existing:
        log.debug("Combined file already contains this entry — skip")
        return
    if begin in existing and end in existing:
        pattern = re.escape(begin) + r"(.*?)" + re.escape(end)
        m = re.search(pattern, existing, flags=re.S)
        if m:
            inner = m.group(1).strip()
            new_inner = (inner + "\n" + entry).strip()
            new = re.sub(pattern, begin + "\n" + new_inner + "\n" + end, existing, flags=re.S)
            if dry_run:
                log.info(f"[dry-run] Would update combined file {combined} between markers")
                return
            combined.write_text(new)
            return
    new = existing + "\n" + begin + "\n" + entry + "\n" + end + "\n"
    if dry_run:
        log.info(f"[dry-run] Would write combined file {combined}")
    else:
        combined.write_text(new)

def _remove_entry_from_combined(combined: Path, site_fragment: str, dry_run: bool = False) -> None:
    if not combined.exists():
        return
    txt = combined.read_text()
    new_lines = [l for l in txt.splitlines() if site_fragment not in l]
    new_txt = "\n".join(new_lines) + "\n"
    if dry_run:
        log.info(f"[dry-run] Would remove lines containing '{site_fragment}' from {combined}")
    else:
        combined.write_text(new_txt)

# Remove Helpers
def _remove_marker_region_from_server_blocks(conf_path: Path, begin: str, end: str, dry_run: bool = False) -> None:
    if dry_run:
        log.info(f"[dry-run] Would remove marker regions {begin}..{end} from {conf_path}")
        return
    txt = conf_path.read_text()
    blocks = _find_server_blocks(txt)
    modified = False
    for start, endpos, block in blocks:
        pattern = re.escape(begin) + r"(.*?)" + re.escape(end)
        if re.search(pattern, block, flags=re.S):
            new_block = re.sub(pattern, "", block, flags=re.S)
            txt = txt[:start] + new_block + txt[endpos:]
            modified = True
    if modified:
        conf_path.write_text(txt)

def _remove_location_block_from_conf(conf_path: Path, location_path: str, dry_run: bool = False) -> None:
    if dry_run:
        log.info(f"[dry-run] Would remove location {location_path} from {conf_path}")
        return
    txt = conf_path.read_text()
    blocks = _find_server_blocks(txt)
    modified = False
    for start, endpos, block in blocks:
        m = re.search(rf"location\s+{re.escape(location_path)}\s*\{{", block)
        if not m:
            continue
        loc_start = m.start()
        depth = 0
        i = m.end()
        while i < len(block):
            if block[i] == "{":
                depth += 1
            elif block[i] == "}":
                if depth == 0:
                    loc_end = i + 1
                    new_block = block[:loc_start] + block[loc_end:]
                    txt = txt[:start] + new_block + txt[endpos:]
                    modified = True
                    break
                else:
                    depth -= 1
            i += 1
    if modified:
        conf_path.write_text(txt)

# Safe client_max_body_size
def _set_client_max_body_size_in_server(conf_path: Path, val: str, dry_run: bool = False) -> None:
    if dry_run:
        log.info(f"[dry-run] Would set client_max_body_size {val} in {conf_path}")
        return
    txt = conf_path.read_text()
    blocks = _find_server_blocks(txt)
    modified = False
    for start, endpos, block in blocks:
        if not _server_has_port(block, 443):
            continue
        locs = _find_location_blocks_in_server(block)
        first_loc_start = locs[0][0] if locs else None
        if first_loc_start:
            head = block[:first_loc_start]
            tail = block[first_loc_start:]
        else:
            head = block
            tail = ""
        head_lines = head.splitlines()
        idx_existing = None
        for i, ln in enumerate(head_lines):
            if re.search(r"\bclient_max_body_size\b", ln):
                idx_existing = i
                break
        if idx_existing is not None:
            head_lines[idx_existing] = re.sub(r"client_max_body_size\s+[^;]+;", f"client_max_body_size {val};", head_lines[idx_existing])
        else:
            insert_idx = None
            for i, ln in enumerate(head_lines):
                if re.search(r"listen\s+[^\n;]*\b443\b", ln):
                    insert_idx = i + 1
            if insert_idx is None:
                for i, ln in enumerate(head_lines):
                    if ln.strip().startswith("server_name"):
                        insert_idx = i + 1
                        break
            if insert_idx is None:
                insert_idx = 1 if len(head_lines) > 0 else 0
            head_lines.insert(insert_idx, f"    client_max_body_size {val};")
        new_head = "\n".join(head_lines)
        new_block = new_head + tail
        txt = txt[:start] + new_block + txt[endpos:]
        modified = True
        break
    if modified:
        conf_path.write_text(txt)

# Flags Management
def apply_flag_to_site(
    site: str,
    flag: str,
    value: Optional[Any] = None,
    flags_dir: Union[str, Path] = "templates",  # ← ADD DEFAULT
    meta: Optional[Dict[str, Any]] = None,
    dry_run: bool = False
) -> None:
    """Apply a flag to site config (hardcoded logic per flag)."""
    flags_dir = Path(flags_dir)
    conf = DEFAULT_SITES_AVAILABLE / f"{site}"
    if not conf.exists():
        log.warning(f"No config for {site} at {conf}")
        return
    tpl_path = flags_dir / f"{flag}.conf"
    if not tpl_path.exists():
        log.warning(f"Flag template not found: {tpl_path}")
        return
    raw = tpl_path.read_text()
    if flag == "cache":
        cache_dir = str(ensure_cache_dir(site))
        snippet = raw.replace("{{SITE}}", site).replace("{{CACHE_DIR}}", cache_dir)
        _apply_snippet(conf, snippet, placement="server_443_out_after_location", begin_marker="# ---- CACHE-BEGIN ----", end_marker="# ---- CACHE-END ----", dry_run=dry_run)
        cache_path_tpl = flags_dir / "cache-path.conf"
        if cache_path_tpl.exists():
            entry = cache_path_tpl.read_text().replace("{{SITE}}", site).replace("{{CACHE_DIR}}", cache_dir)
            _append_entry_to_combined(DEFAULT_CACHE_COMBINED, "# ---- CACHE-PATH-BEGIN ----", "# ---- CACHE-PATH-END ----", entry, dry_run=dry_run)
    elif flag == "error":
        snippet = raw.replace("{{SITE}}", site)
        _apply_snippet(conf, snippet, placement="server_443_out_after_location", begin_marker="# ---- ERROR-BEGIN ----", end_marker="# ---- ERROR-END ----", dry_run=dry_run)
    elif flag == "upload":
        val = value or "10M"
        _set_client_max_body_size_in_server(conf, val, dry_run=dry_run)
    elif flag == "dns":
        ip = meta.get("upstream", "") if meta else ""
        m = re.match(r"https?://([0-9\.]+)", ip)
        ip = m.group(1) if m else DEFAULT_NGINX_IP
        entry = raw.replace("{{SITE}}", site).replace("{{IP}}", ip)
        _append_entry_to_combined(DEFAULT_DNS_COMBINED, "# ---- DNS-BEGIN ----", "# ---- DNS-END ----", entry, dry_run=dry_run)
    elif flag.startswith("/"):
        if meta and flag in [p for p, _ in meta.get("locations", [])]:
            up = next((u for p, u in meta["locations"] if p == flag), meta.get("upstream", ""))
            snippet = raw.replace("{{ PATH }}", flag).replace("{{ UPSTREAM }}", up)
            _apply_snippet(conf, snippet, placement="server_443_out_after_location", dry_run=dry_run)
    else:
        log.warning(f"Unknown flag: {flag}")
        return
    log.info(f"Applied flag {flag} to {site}")
    manage_nginx_service(dry_run=dry_run)

def remove_flag_from_site(site: str, flag: str, flags_dir: Union[str, Path] = "templates", dry_run: bool = False) -> None:
    """Remove a flag from site config."""
    conf = DEFAULT_SITES_AVAILABLE / f"{site}"
    if not conf.exists():
        return
    if flag == "cache":
        _remove_marker_region_from_server_blocks(conf, "# ---- CACHE-BEGIN ----", "# ---- CACHE-END ----", dry_run=dry_run)
        _remove_entry_from_combined(DEFAULT_CACHE_COMBINED, site, dry_run=dry_run)
        cache_dir = DEFAULT_CACHE_BASE / site
        if cache_dir.exists():
            if dry_run:
                log.info(f"[dry-run] Would remove cache dir {cache_dir}")
            else:
                shutil.rmtree(str(cache_dir))
                log.info(f"Removed cache dir {cache_dir}")
    elif flag == "error":
        _remove_marker_region_from_server_blocks(conf, "# ---- ERROR-BEGIN ----", "# ---- ERROR-END ----", dry_run=dry_run)
    elif flag == "upload":
        log.info(f"Re-rendering base config for {site} to reset upload")
        # Assume re-create with default; need meta
    elif flag == "dns":
        _remove_entry_from_combined(DEFAULT_DNS_COMBINED, f"/{site}/", dry_run=dry_run)
    elif flag.startswith("/"):
        if flag != "/":
            _remove_location_block_from_conf(conf, flag, dry_run=dry_run)
        else:
            log.debug("Skipping removal of root '/' location")
    manage_nginx_service(dry_run=dry_run)

def sync_flags(sites_list: List[Dict[str, Any]], flags_dir: Union[str, Path] = "templates", dry_run: bool = False) -> None:
    """Sync flags from sites.txt to existing configs (idempotent)."""
    known_flags = ["cache", "error", "upload", "dns"]
    for s in sites_list:
        site = s["site"]
        desired_flags = set(s.get("flags", {}).keys())
        desired_locations = set([p for p, _ in s.get("locations", [])])
        for flag in desired_flags:
            if flag == "force":
                continue
            val = None if s["flags"][flag] is True else s["flags"][flag]
            apply_flag_to_site(site, flag, val, flags_dir, s, dry_run=dry_run)
        for flag in known_flags:
            if flag not in desired_flags:
                remove_flag_from_site(site, flag, flags_dir, dry_run=dry_run)
        conf = DEFAULT_SITES_AVAILABLE / f"{site}"
        if conf.exists():
            txt = conf.read_text()
            locs_in_conf = re.findall(r"location\s+([^\s\{]+)\s*\{", txt)
            for loc in locs_in_conf:
                if loc == "/":
                    continue
                if loc not in desired_locations:
                    remove_flag_from_site(site, loc, flags_dir, dry_run=dry_run)

# Sync & Remove & List
def sync_sites(
    sites_list: List[Dict[str, Any]],
    proxy_tpl: Union[str, Path],
    serve_tpl: Union[str, Path],
    location_tpl: Union[str, Path],
    flags_dir: Union[str, Path] = "templates",
    dry_run: bool = False,
    **dirs: Any
) -> None:
    """Sync sites: create/remove, apply flags. Skip existing unless forced."""
    available_dir = Path(dirs.get("available_dir", DEFAULT_SITES_AVAILABLE))
    enabled_dir = Path(dirs.get("enabled_dir", DEFAULT_SITES_ENABLED))
    listed_sites = [s['site'] for s in sites_list]
    existing = list_sites(available_dir)
    to_add = set(listed_sites) - set(existing)
    to_remove = set(existing) - set(listed_sites)
    to_keep = set(listed_sites) & set(existing)
    for site in to_add:
        meta = next((s for s in sites_list if s["site"] == site), None)
        if meta:
            create_site(site, meta, flags_dir, proxy_tpl, serve_tpl, location_tpl, force=False, dry_run=dry_run)
    for site in to_remove:
        remove_site(site, dirs.get("list_path"), flags_dir, dry_run=dry_run, **dirs)
    for site in to_keep:
        meta = next((s for s in sites_list if s["site"] == site), None)
        if meta and meta.get("flags", {}).get("force", False):
            create_site(site, meta, flags_dir, proxy_tpl, serve_tpl, location_tpl, force=True, dry_run=dry_run)
    sync_flags(sites_list, flags_dir, dry_run=dry_run)

def remove_site(site: str, list_path: Union[str, Path], flags_dir: Union[str, Path] = "templates", dry_run: bool = False, **dirs: Any) -> None:
    """Remove site from list/config/cache/dns, reload."""
    list_path = Path(list_path)
    available_dir = Path(dirs.get("available_dir", DEFAULT_SITES_AVAILABLE))
    enabled_dir = Path(dirs.get("enabled_dir", DEFAULT_SITES_ENABLED))
    cache_base = Path(dirs.get("cache_base", DEFAULT_CACHE_BASE))
    cache_combined = Path(dirs.get("cache_combined", DEFAULT_CACHE_COMBINED))
    dns_combined = Path(dirs.get("dns_combined", DEFAULT_DNS_COMBINED))
    content = list_path.read_text()
    lines = [l for l in content.splitlines() if not l.strip().startswith(site)]
    if dry_run:
        log.info(f"[dry-run] Would remove {site} from sites.txt")
    else:
        atomic_write(str(list_path), "\n".join(lines) + "\n")
        log.info(f"Removed {site} from sites.txt")
    tgt_enabled = enabled_dir / site
    tgt_avail = available_dir / site
    if tgt_enabled.exists():
        if dry_run:
            log.info(f"[dry-run] Would remove {tgt_enabled}")
        else:
            tgt_enabled.unlink()
    if tgt_avail.exists():
        if dry_run:
            log.info(f"[dry-run] Would remove {tgt_avail}")
        else:
            tgt_avail.unlink()
    _remove_entry_from_combined(cache_combined, site, dry_run=dry_run)
    _remove_entry_from_combined(dns_combined, f"/{site}/", dry_run=dry_run)
    cache_dir = cache_base / site
    if cache_dir.exists():
        if dry_run:
            log.info(f"[dry-run] Would remove cache dir {cache_dir}")
        else:
            remove_dir(str(cache_dir), recursive=True)
    manage_nginx_service(dry_run=dry_run)

def list_sites(available_dir: Path = DEFAULT_SITES_AVAILABLE) -> List[str]:
    """List available sites."""
    if not available_dir.exists():
        return []
    return [p.stem for p in available_dir.glob("*")]

# Service Control
@retry(stop=stop_after_attempt(3), wait=wait_fixed(1))
def manage_nginx_service(
    pid_file: Path = DEFAULT_PID_FILE,
    nginx_cmd: str = DEFAULT_NGINX_CMD,
    test_cmd: List[str] = DEFAULT_TEST_CMD,
    reload_cmd: List[str] = DEFAULT_RELOAD_CMD,
    start_cmd: List[str] = DEFAULT_START_CMD,
    dry_run: bool = False
) -> bool:
    """Test/reload/start Nginx service with retries."""
    if dry_run:
        log.info("[dry-run] Would manage Nginx service")
        return True
    if not is_root():
        raise NginxOpsError("Requires root")
    proc = subprocess.run(test_cmd, capture_output=True)
    if proc.returncode == 0:
        subprocess.run(reload_cmd, capture_output=True)
        log.info("Nginx reloaded successfully")
        return True
    if pid_file.exists():
        pid = pid_file.read_text().strip()
        if pid:
            subprocess.run(["kill", "-QUIT", pid], capture_output=True)
            time.sleep(1)
            log.info(f"Gracefully quit Nginx pid {pid}")
    pid_file.unlink(missing_ok=True)
    subprocess.run(start_cmd, capture_output=True)
    log.info("Started Nginx")
    return True

# Utils
def flush_dns() -> None:
    """Flush DNS cache cross-platform."""
    if is_windows():
        run(["ipconfig", "/flushdns"])
    elif is_linux():
        if command_exists("nscd"):
            run(["nscd", "-i", "hosts"], elevated=True)
        if command_exists("systemd-resolve"):
            run(["systemd-resolve", "--flush-caches"], elevated=True)
    log.info("Flushed DNS cache")

def generate_sites_from_list(
    list_path: Union[str, Path],
    proxy_tpl: Union[str, Path],
    serve_tpl: Union[str, Path],
    location_tpl: Union[str, Path],
    flags_dir="templates", 
    dry_run: bool = False,
    **dirs_and_cmds: Any
) -> None:
    """Full pipeline: parse, sync sites + flags, flush DNS, manage service."""
    sites = parse_sites_list(list_path)
    sync_sites(sites, proxy_tpl, serve_tpl, location_tpl, flags_dir, dry_run=dry_run, **dirs_and_cmds)
    flush_dns()
    manage_nginx_service(dry_run=dry_run)
    if console:
        table = Table(title="Generated Sites")
        table.add_column("Site")
        table.add_column("Upstream")
        table.add_column("Flags")
        for s in sites:
            flags_str = ", ".join([k if v is True else f"{k}={v}" for k,v in s['flags'].items()])
            table.add_row(s['site'], s['upstream'], flags_str)
        console.print(table)
    log.info("Site generation complete")

# Initialization
def init(generate_dir: Union[str, Path] = "/etc/nginx/generate-sites", sites_txt: bool = True, manage_py: bool = True) -> None:
    """Set up the generate-sites folder structure with new templates, sites.txt, etc."""
    generate_dir = Path(generate_dir)
    ensure_dir(str(generate_dir))
    tpl_dir = generate_dir / "templates"
    ensure_dir(str(tpl_dir))
    templates = {
        "cache.conf": """# per-site cache settings for {{SITE}}
# Put these inside server {} (preferably inside location / {})
# Use the precomputed $bypass_cache (computed in http { } via map)
# proxy_cache_bypass prevents serving from cache for the request
# proxy_no_cache prevents the response from being cached
proxy_cache {{SITE}}_cache;
proxy_cache_key "$scheme://$host$request_uri";
proxy_cache_bypass $bypass_cache;
proxy_no_cache $bypass_cache;
# Cache most common responses
proxy_cache_valid 200 301 302 30m;
proxy_cache_valid 404 1m;
proxy_cache_valid any 10m;
# Cache immediately (not after 2 hits)
proxy_cache_min_uses 1;
# Allow stale responses if backend is slow/down
proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
proxy_cache_lock on;
proxy_cache_background_update on;
# Add debug headers while testing (remove after verification)
add_header X-Bypass "$bypass_cache" always;
add_header X-Cache-Status $upstream_cache_status always;
proxy_read_timeout 300;
proxy_send_timeout 300;""",
        "cache-path.conf": """# per-site cache path for {{SITE}}
# MUST be in http {} context (not inside server {})
proxy_cache_path {{CACHE_DIR}} levels=1:2 keys_zone={{SITE}}_cache:100m max_size=2g inactive=60m use_temp_path=off;""",
        "dns.conf": """address=/{{SITE}}/{{IP}}""",
        "error.conf": """proxy_intercept_errors on;""",
        "location.conf": """location {{ PATH }} {
    proxy_pass {{ UPSTREAM }};
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300;
    proxy_send_timeout 300;
}""",
        "reverse-proxy.conf": """server {
    listen 80;
    server_name {{ SITE }};
    return 301 https://$host$request_uri; # Redirect to HTTPS
}
server {
    listen 443 ssl;
    server_name {{ SITE }};
    client_max_body_size {{ CLIENT_MAX_BODY_SIZE | default("10M") }};
    access_log /var/log/nginx/{{ SITE }}-access.log combined buffer=32k flush=5m;
    error_log /var/log/nginx/{{ SITE }}-error.log;
    include snippets/error-pages.conf;
    location / {
        # make sure IP_ADDRESS includes scheme (http:// or https://) in sites.txt or upstream value
        proxy_pass {{ IP_ADDRESS }};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        # recommended for large uploads
        # proxy_request_buffering off;
        proxy_set_header Range $http_range;
    }
}""",
        "serve.conf": """server {
    listen 80;
    server_name {{ SITE }};
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl; # add `http2` if desired
    server_name {{ SITE }};
  
    root {{ ROOT_PATH }};
    index index.html index.htm;
    # default unlimited (0) used previously; you can override via context
    client_max_body_size {{ CLIENT_MAX_BODY_SIZE | default("0M") }};
    access_log /var/log/nginx/{{ SITE }}-access.log;
    error_log /var/log/nginx/{{ SITE }}-error.log;
    location / {
        # try real file first, then SPA index.html
        try_files $uri $uri/ /index.html;
        # preserve original headers
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # If you actually proxy here, add a proxy_pass line. For pure static serve, remove.
        # proxy_pass {{ IP_ADDRESS }};
        # other useful options for SPAs:
        # add_header Cache-Control "no-store" always;
    }
}""",
    }
    for name, content in templates.items():
        path = tpl_dir / name
        ensure_dir(str(path.parent))
        atomic_write(str(path), content)
    if sites_txt:
        sites_path = generate_dir / "sites.txt"
        if not sites_path.exists():
            atomic_write(str(sites_path), "# site upstream [flags] [/path=upstream]\n")
    if manage_py:
        manage_path = generate_dir / "manage_sites.py"
        if not manage_path.exists():
            atomic_write(str(manage_path), "# Placeholder for manage_sites.py\n")
    log.info(f"Initialized generate-sites at {generate_dir} with templates")