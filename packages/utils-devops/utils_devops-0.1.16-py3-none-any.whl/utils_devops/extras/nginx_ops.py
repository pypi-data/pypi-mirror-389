"""
Nginx Operations Module (extras)
Provides high-level utilities for managing Nginx sites, configs, caching, and service control.
Built on core modules for file ops, commands, templating, etc. Supports Linux/Windows.
Key features:
- Parse sites lists with upstreams, locations (as dict), flags.
- Render templates (proxy/serve) with Jinja, apply flags post-render.
- Validate upstreams (ping or HTTP check via requests).
- Manage site configs: create/enable/disable/remove.
- Handle per-site cache: apply/remove based on flags.
- Sync sites from file with atomic reload/rollback, handle dns updates.
- Cross-platform: Detect OS, adjust paths/commands.
- Optional: Rich tables for site listings, tenacity retries, slack notifications.
Dependencies: requests (for upstream validation), rich (tables), tenacity (retries).
Raises NginxOpsError on failures.
"""
from __future__ import annotations
import os
import platform
import re
import shutil
import socket
import time
from pathlib import Path
from utils_devops.core import *
from typing import Dict, List, Optional, Tuple, Union, Any, Sequence
import requests  # For HTTP upstream validation
from tenacity import retry, stop_after_attempt, wait_fixed  # For retries
from utils_devops.core.logs import get_logger
from utils_devops.core.files import (
    atomic_write, backup_file, create_symlink, remove_file, resolve_symlink,
    comment_block_between_markers, uncomment_block_between_markers, insert_block, remove_block_between_markers,
    read_marked_block, ensure_dir, remove_dir, set_mode, set_owner
)
from utils_devops.core.systems import run, reload_service, is_root, is_windows, is_linux, readlink_f, command_exists
from utils_devops.core.strings import render_jinja, replace_substring
from utils_devops.core.script_helpers import backup_many, rollback_backups, with_temp_dir, create_rich_table, send_slack_notify, retry_func

from utils_devops.core.files import read_file
try:
    from rich.console import Console  # For tables
except ImportError:
    Console = None
log = get_logger()
console = Console() if Console else None  # Fallback if rich not installed
# Defaults
DEFAULT_NGINX_CMD = "nginx.exe" if platform.system() == "Windows" else "nginx"
DEFAULT_TEST_CMD = [DEFAULT_NGINX_CMD, "-t"]
DEFAULT_RELOAD_CMD = [DEFAULT_NGINX_CMD, "-s", "reload"]
DEFAULT_START_CMD = [DEFAULT_NGINX_CMD, "-g", "daemon off;"]
DEFAULT_PID_FILE = r"C:\nginx\logs\nginx.pid" if platform.system() == "Windows" else "/run/nginx.pid"
DEFAULT_LOG_DIR = r"C:\nginx\logs" if platform.system() == "Windows" else "/var/log/nginx"
DEFAULT_SITES_AVAILABLE = r"C:\nginx\conf\sites-available" if platform.system() == "Windows" else "/etc/nginx/sites-available"
DEFAULT_SITES_ENABLED = r"C:\nginx\conf\site-enabled" if platform.system() == "Windows" else "/etc/nginx/sites-enabled"
DEFAULT_CACHE_BASE = r"C:\nginx\cache" if platform.system() == "Windows" else "/var/cache/nginx/sites"
DEFAULT_CACHE_PATH_DIR = r"C:\nginx\conf.d" if platform.system() == "Windows" else "/etc/nginx/conf.d"
DEFAULT_CACHE_COMBINED = os.path.join(DEFAULT_CACHE_PATH_DIR, "cache-paths.conf")
DEFAULT_NGINX_CONF = r"C:\nginx\conf\nginx.conf" if platform.system() == "Windows" else "/etc/nginx/nginx.conf"
DEFAULT_NGINX_USER_LINUX = "www-data"
DEFAULT_NGINX_USER_WINDOWS = "SYSTEM"  # Permissive on Win
DEFAULT_DNSMASQ_DIR = "/etc/dnsmasq.d"
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
    # Cache Management
    "apply_site_cache",
    "reload_cache",
    # DNS Management
    "update_dnsmasq",
    # Sync & Remove
    "sync_sites",
    "remove_site",
    # Service Control
    "manage_nginx_service",
    # Utils
    "flush_dns",
    "generate_sites_from_list",
]
def help() -> None:
    """Print a concise index of functions in this module for interactive use.
    IDEs will also pick up `__all__` and individual function docstrings.
    """
    print(
        """
Nginx Ops (extras) — Function Index
# Paths & Detection
get_nginx_paths(os_type: str = "auto") -> Dict[str, str]: Default Nginx paths.
detect_nginx_user(conf_path: str = DEFAULT_NGINX_CONF) -> str: Parse user from conf.
# Parsing
parse_sites_list(list_path: str) -> List[Dict[str, Any]]: Parse sites.txt to dicts with locations and flags.
# Rendering & Building
render_nginx_template(template_path: str, context: Dict[str, Any]) -> str: Jinja render.
build_locations_block(locations: Dict[str, str]) -> str: Build location blocks from dict.
# Validation
validate_upstream(upstream: str, fallback: str = DUMMY_UPSTREAM, timeout: int = 1, use_http: bool = True) -> str: Ping/HTTP check, fallback.
# Logs & Dirs
setup_site_logs(site: str, log_dir: str = DEFAULT_LOG_DIR, nginx_user: Optional[str] = None) -> Tuple[str, str]: Create logs, set perms.
ensure_cache_dir(site: str, cache_base: str = DEFAULT_CACHE_BASE) -> str: Create/return cache dir.
# Config Management
write_site_config(site: str, rendered: str, available_dir: str = DEFAULT_SITES_AVAILABLE, enabled_dir: str = DEFAULT_SITES_ENABLED) -> None: Write and enable.
# Cache Management
apply_site_cache(site: str, flag: str, cache_template: str, markers: Dict[str, str], site_conf: str, cache_base: str = DEFAULT_CACHE_BASE, cache_combined: str = DEFAULT_CACHE_COMBINED) -> Optional[str]: Apply/remove cache, return path_block if applied.
reload_cache(sites: Union[str, List[str]], cache_template: str, markers: Dict[str, str], cache_base: str = DEFAULT_CACHE_BASE, cache_combined: str = DEFAULT_CACHE_COMBINED) -> None: Clear and re-apply cache.
# DNS Management
update_dnsmasq(sites: List[str], nginx_ip: str = DEFAULT_NGINX_IP, dns_dir: str = DEFAULT_DNSMASQ_DIR) -> bool: Update dnsmasq confs, return True if changed (for reload).
# Sync & Remove
sync_sites(sites_list: List[Dict[str, Any]], template: str, cache_template: Optional[str] = None, markers: Optional[Dict[str, str]] = None, **dirs) -> None: Sync sites, cache, dns.
remove_site(site: str, list_path: str, **dirs) -> None: Remove from list/config/cache/dns, reload.
# Service Control
manage_nginx_service(pid_file: str = DEFAULT_PID_FILE, nginx_cmd: str = DEFAULT_NGINX_CMD, test_cmd: List[str] = DEFAULT_TEST_CMD, reload_cmd: List[str] = DEFAULT_RELOAD_CMD, start_cmd: List[str] = DEFAULT_START_CMD) -> bool: Test/reload/start.
# Utils
flush_dns() -> None: Flush DNS cache.
generate_sites_from_list(list_path: str, proxy_tpl: str, serve_tpl: str, **dirs_and_cmds) -> None: Full generation with validation/logs/sync/reload/dns.
Use `help(nginx_ops.some_function)` to view per-function docs.
"""
    )
# Paths & Detection
def get_nginx_paths(os_type: str = "auto") -> Dict[str, str]:
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
            "log_dir": DEFAULT_LOG_DIR,
            "conf": DEFAULT_NGINX_CONF,
            "pid_file": DEFAULT_PID_FILE,
            "cmd": DEFAULT_NGINX_CMD,
        }
    elif os_type == "linux":
        return {
            "sites_available": "/etc/nginx/sites-available",
            "sites_enabled": "/etc/nginx/sites-enabled",
            "cache_base": "/var/cache/nginx/sites",
            "cache_path_dir": "/etc/nginx/conf.d",
            "cache_combined": "/etc/nginx/conf.d/cache-paths.conf",
            "log_dir": "/var/log/nginx",
            "conf": "/etc/nginx/nginx.conf",
            "pid_file": "/run/nginx.pid",
            "cmd": "nginx",
        }
    else:
        raise NginxOpsError(f"Unsupported os_type: {os_type}")
def detect_nginx_user(conf_path: str = DEFAULT_NGINX_CONF) -> str:
    """Parse 'user' directive from nginx.conf, fallback to defaults."""
    try:
        content = read_file(conf_path)
        match = re.search(r'^\s*user\s+([^;]+);', content, re.MULTILINE)
        if match:
            user = match.group(1).strip()
            log.debug(f"Detected nginx user: {user}")
            return user
    except Exception as e:
        log.warning(f"Failed to detect nginx user: {e}")
    return "SYSTEM" if is_windows() else "www-data"
# Parsing
def parse_sites_list(list_path: str) -> List[Dict[str, Any]]:
    """Parse sites file to list of dicts {site, upstream, locations: dict, flags: list}."""
    content = read_file(list_path)
    sites = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r'\s+', line)
        site = parts[0]
        upstream = parts[1] if len(parts) > 1 else ""
        locations = {}
        flags = []
        for p in parts[2:]:
            if '=' in p:
                path, up = p.split('=', 1)
                locations[path.strip()] = up.strip()
            else:
                flags.append(p.lower())
        sites.append({"site": site, "upstream": upstream, "locations": locations, "flags": flags})
    log.info(f"Parsed {len(sites)} sites from {list_path}")
    return sites
# Rendering & Building
def render_nginx_template(template_path: str, context: Dict[str, Any]) -> str:
    """Render Nginx template with Jinja."""
    template = read_file(template_path)
    return render_jinja(template, context)
def build_locations_block(locations: Dict[str, str]) -> str:
    """Build Nginx location blocks from dict {path: upstream}."""
    blocks = []
    for path, upstream in locations.items():
        block = f"""
location {path} {{
    proxy_pass {upstream};
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300;
    proxy_send_timeout 300;
}}
"""
        blocks.append(block)
    return "\n".join(blocks)
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
                return upstream
        except Exception:
            pass
    else:
        try:
            socket.getaddrinfo(host, None)
            return upstream
        except Exception:
            pass
    log.warning(f"Upstream {upstream} unreachable, using {fallback}")
    return fallback
# Logs & Dirs
def setup_site_logs(site: str, log_dir: str = DEFAULT_LOG_DIR, nginx_user: Optional[str] = None) -> Tuple[str, str]:
    """Create access/error logs, set permissions."""
    ensure_dir(log_dir)
    access_log = os.path.join(log_dir, f"{site}-access.log")
    error_log = os.path.join(log_dir, f"{site}-error.log")
    open(access_log, 'a').close()
    open(error_log, 'a').close()
    set_mode(access_log, 0o644)
    set_mode(error_log, 0o644)
    if nginx_user:
        set_owner(access_log, nginx_user)
        set_owner(error_log, nginx_user)
    log.info(f"Setup logs for {site}")
    return access_log, error_log
def ensure_cache_dir(site: str, cache_base: str = DEFAULT_CACHE_BASE) -> str:
    """Create/return per-site cache dir, set perms."""
    cache_dir = os.path.join(cache_base, site)
    ensure_dir(cache_dir)
    set_mode(cache_dir, 0o755)
    return cache_dir
# Config Management
def write_site_config(
    site: str, rendered: str,
    available_dir: str = DEFAULT_SITES_AVAILABLE,
    enabled_dir: str = DEFAULT_SITES_ENABLED,
) -> None:
    """Write config to available, enable with symlink (or copy on Win)."""
    tgt_avail = os.path.join(available_dir, site)
    tgt_enabled = os.path.join(enabled_dir, site)
    ensure_dir(available_dir)
    ensure_dir(enabled_dir)
    atomic_write(tgt_avail, rendered)
    if is_windows():
        # Windows symlinks need admin; fallback to copy
        shutil.copy(tgt_avail, tgt_enabled)
    else:
        create_symlink(tgt_avail, tgt_enabled, force=True)
    log.info(f"Wrote and enabled config for {site}")
# Cache Management
def apply_site_cache(
    site: str, flag: str,
    cache_template: str,
    markers: Dict[str, str],
    site_conf: str,
    cache_base: str = DEFAULT_CACHE_BASE,
    cache_combined: str = DEFAULT_CACHE_COMBINED,
) -> Optional[str]:
    """Apply/remove cache per flag ('cache'/'no-cache'), return path_block if applied."""
    remove_block_between_markers(site_conf, markers['begin'], markers['end'])
    if flag == 'no-cache':
        return None
    cache_dir = ensure_cache_dir(site, cache_base)
    path_block = read_marked_block(cache_template, markers['path_begin'], markers['path_end'])
    server_block = read_marked_block(cache_template, markers['begin'], markers['end'])
    rendered_server = render_jinja(server_block, {"SITE": site, "CACHE_DIR": cache_dir})
    insert_block(site_conf, rendered_server, before_marker="}")
    rendered_path = render_jinja(path_block, {"SITE": site, "CACHE_DIR": cache_dir})
    return rendered_path
def reload_cache(
    sites: Union[str, List[str]],
    cache_template: str,
    markers: Dict[str, str],
    cache_base: str = DEFAULT_CACHE_BASE,
    cache_combined: str = DEFAULT_CACHE_COMBINED,
) -> None:
    """Clear and re-apply cache for site(s)."""
    if isinstance(sites, str):
        sites = [sites]
    for site in sites:
        remove_dir(os.path.join(cache_base, site), recursive=True)
        log.info(f"Cleared cache for {site}")
        # Assume flag="cache" for re-cache; adjust if needed
        apply_site_cache(site, "cache", cache_template, markers, resolve_symlink(os.path.join(DEFAULT_SITES_ENABLED, site)), cache_base, cache_combined)
    manage_nginx_service()
# DNS Management
def update_dnsmasq(
    sites: List[str],
    nginx_ip: str = DEFAULT_NGINX_IP,
    dns_dir: str = DEFAULT_DNSMASQ_DIR,
) -> bool:
    """Update dnsmasq confs for sites, return True if changed (for reload)."""
    ensure_dir(dns_dir)
    changed = False
    current_confs = {f for f in os.listdir(dns_dir) if f.endswith(".conf")}
    for site in sites:
        conf = f"{site}.conf"
        content = f"address=/{site}/{nginx_ip}\n"
        conf_path = os.path.join(dns_dir, conf)
        if not os.path.exists(conf_path) or read_file(conf_path) != content:
            atomic_write(conf_path, content)
            set_mode(conf_path, "644")
            set_owner(conf_path, "root", "root")
            changed = True
    for conf in current_confs:
        site_from_conf = conf[:-5]
        if site_from_conf not in sites:
            remove_file(os.path.join(dns_dir, conf))
            changed = True
    if changed:
        run(["systemctl", "restart", "dnsmasq"], elevated=True)
    return changed
# Sync & Remove
def sync_sites(
    sites_list: List[Dict[str, Any]],
    proxy_tpl: str,
    serve_tpl: Optional[str] = None,
    cache_template: Optional[str] = None,
    markers: Optional[Dict[str, str]] = None,
    **dirs: str,
) -> None:
    """Sync sites: create/remove, handle cache, dns."""
    available_dir = dirs.get("available_dir", DEFAULT_SITES_AVAILABLE)
    enabled_dir = dirs.get("enabled_dir", DEFAULT_SITES_ENABLED)
    cache_base = dirs.get("cache_base", DEFAULT_CACHE_BASE)
    cache_combined = dirs.get("cache_combined", DEFAULT_CACHE_COMBINED)
    log_dir = dirs.get("log_dir", DEFAULT_LOG_DIR)
    listed_sites = [s['site'] for s in sites_list]
    # Remove extras
    for f in Path(enabled_dir).iterdir():
        if f.is_file() or f.is_symlink():
            site = f.stem
            if site not in listed_sites:
                remove_site_files(site, available_dir, enabled_dir)
                if cache_template:
                    remove_site_cache_entries(site, cache_combined, cache_base)
    # Create/update
    path_blocks = []
    dns_sites = []
    nginx_user = detect_nginx_user()
    for s in sites_list:
        upstream = validate_upstream(s['upstream'])
        is_serve = upstream.startswith('/')
        template = serve_tpl if is_serve and serve_tpl else proxy_tpl
        context = {
            "SITE_NAME": s['site'],
            "IP_ADDRESS": upstream if not is_serve else "",
            "ROOT_PATH": upstream if is_serve else "",
            "LOCATIONS": build_locations_block(s['locations']),
        }
        rendered = render_nginx_template(template, context)
        # Apply flags post-render
        flags = s['flags']
        if 'error' in flags:
            rendered = replace_substring(rendered, "#proxy_intercept_errors on;", "proxy_intercept_errors on;")
        if 'upload-no-limit' in flags:
            rendered = replace_substring(rendered, "client_max_body_size 10M ;", "client_max_body_size 0M ;")
        if s['site'] == "default_server":
            rendered = replace_substring(rendered, "server_name SITE_NAME;", "server_name _;")
            rendered = replace_substring(rendered, "listen 80;", "listen 80 default_server;")
            rendered = replace_substring(rendered, "listen 443 ssl ;", "listen 443 ssl default_server;")
        if 'dns' in flags:
            dns_sites.append(s['site'])
        # Write
        tgt_avail = os.path.join(available_dir, s['site'])
        atomic_write(tgt_avail, rendered)
        access, error = setup_site_logs(s['site'], log_dir, nginx_user)
        # Enable
        tgt_enabled = os.path.join(enabled_dir, s['site'])
        create_symlink(tgt_avail, tgt_enabled, force=True)
        # Cache
        cache_flag = 'cache' if 'cache' in flags else 'no-cache' if 'no-cache' in flags else ''
        if cache_template and markers and cache_flag:
            path_block = apply_site_cache(s['site'], cache_flag, cache_template, markers, tgt_avail, cache_base, cache_combined)
            if path_block:
                path_blocks.append(path_block)
    if path_blocks:
        content = "\n".join(path_blocks) + "\n"
        atomic_write(cache_combined, content)
    # DNS
    if dns_sites:
        changed = update_dnsmasq(dns_sites)
        if changed:
            log.info("DNS updated, reloaded dnsmasq")
def remove_site(site: str, list_path: str, **dirs: str) -> None:
    """Remove site from list/config/cache/dns, reload."""
    available_dir = dirs.get("available_dir", DEFAULT_SITES_AVAILABLE)
    enabled_dir = dirs.get("enabled_dir", DEFAULT_SITES_ENABLED)
    cache_base = dirs.get("cache_base", DEFAULT_CACHE_BASE)
    cache_combined = dirs.get("cache_combined", DEFAULT_CACHE_COMBINED)
    content = read_file(list_path)
    lines = [l for l in content.splitlines() if not l.strip().startswith(site)]
    atomic_write(list_path, "\n".join(lines) + "\n")
    remove_site_files(site, available_dir, enabled_dir)
    remove_site_cache_entries(site, cache_combined, cache_base)
    # Remove dns conf if exists
    dns_conf = os.path.join(DEFAULT_DNSMASQ_DIR, f"{site}.conf")
    if os.path.exists(dns_conf):
        remove_file(dns_conf)
        run(["systemctl", "restart", "dnsmasq"], elevated=True)
    manage_nginx_service()
# Service Control
def manage_nginx_service(
    pid_file: str = DEFAULT_PID_FILE,
    nginx_cmd: str = DEFAULT_NGINX_CMD,
    test_cmd: List[str] = DEFAULT_TEST_CMD,
    reload_cmd: List[str] = DEFAULT_RELOAD_CMD,
    start_cmd: List[str] = DEFAULT_START_CMD,
) -> bool:
    """Test/reload/start Nginx service."""
    if not is_root():
        raise NginxOpsError("Requires root")
    res = reload_service(reload_cmd, test_cmd)
    if res:
        return True
    if os.path.exists(pid_file):
        pid = read_file(pid_file).strip()
        if pid and run(["kill", "-0", pid], no_die=True).returncode == 0:
            run(["kill", "-QUIT", pid])  # Graceful quit
            time.sleep(1)
    remove_file(pid_file)
    run(start_cmd)
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
    log.info("Flushed DNS")
def generate_sites_from_list(
    list_path: str,
    proxy_tpl: str,
    serve_tpl: str,
    **dirs_and_cmds: Any,
) -> None:
    """Full pipeline: parse, validate, render (proxy/serve), setup logs, sync, reload."""
    sites = parse_sites_list(list_path)
    nginx_user = detect_nginx_user()
    for s in sites:
        template = serve_tpl if s['upstream'].startswith('/') else proxy_tpl
        access, error = setup_site_logs(s['site'], nginx_user=nginx_user)
        upstream = validate_upstream(s['upstream'])
        context = {
            "SITE_NAME": s['site'],
            "UPSTREAM_URL": upstream,
            "ACCESS_LOG": access,
            "ERROR_LOG": error,
            "LOCATIONS": build_locations_block(s.get('locations', {})),
        }
        rendered = render_nginx_template(template, context)
        write_site_config(s['site'], rendered, **dirs_and_cmds)
    sync_sites(sites, proxy_tpl, **dirs_and_cmds)
    flush_dns()
    manage_nginx_service(**dirs_and_cmds)
    if console:
        table = create_rich_table("Generated Sites", ["Site", "Upstream", "Flags"])
        for s in sites:
            table.add_row(s['site'], s['upstream'], ", ".join(s['flags']))
        console.print(table)
def remove_site_cache_entries(site: str, cache_combined: str, cache_base: str) -> None:
    """Helper to remove cache entries/dir."""
    if os.path.exists(cache_combined):
        content = read_file(cache_combined)
        content = re.sub(rf".*{site}.*\n?", "", content, flags=re.MULTILINE)
        atomic_write(cache_combined, content)
    remove_dir(os.path.join(cache_base, site), recursive=True)
def remove_cache_from_site(site_conf: str, server_start: str, server_end: str) -> None:
    """Helper to remove cache block."""
    remove_block_between_markers(site_conf, server_start, server_end)
def remove_site_files(site: str, available_dir: str, enabled_dir: str) -> None:
    """Helper to remove config files."""
    avail = os.path.join(available_dir, site)
    enabled = os.path.join(enabled_dir, site)
    remove_file(enabled)
    remove_file(avail)
