"""
Nginx Operations Module (extras)
Provides high-level utilities for managing Nginx sites, configs, caching, and service control.
Built on core modules for file ops, commands, templating, etc. Supports Linux/Windows.
Key features:
- Parse sites lists with upstreams, locations (as dict), flags (as dict for values).
- Render templates (proxy/serve) with Jinja, apply flags post-render using templates and meta.
- Validate upstreams (ping or HTTP check via requests).
- Manage site configs: create/enable/disable/remove, skip existing unless forced.
- Handle per-site cache: apply/remove based on flags, manage combined cache paths.
- Sync sites from file with atomic reload/rollback, handle dns updates.
- Cross-platform: Detect OS, adjust paths/commands.
- Optional: Rich tables for site listings, tenacity retries, slack notifications.
- All functions check for required templates before proceeding.
- Flag handling for dns, cache, force, error, upload, additional locations (/).
- Flags applied using mother function, reading from templates with META for logic.
- No hardcoded Nginx configs; all from templates.
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
    read_marked_block, ensure_dir, remove_dir, set_mode, set_owner, file_exists, search_in_file, replace_regex_in_file
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
DEFAULT_DNSMASQ_CONF = "/etc/dnsmasq.conf"
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
    "reload_cache",
    # Sync & Remove
    "sync_sites",
    "remove_site",
    # Service Control
    "manage_nginx_service",
    # Utils
    "flush_dns",
    "generate_sites_from_list",
    # Initialization
    "init",
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
parse_sites_list(list_path: str) -> List[Dict[str, Any]]: Parse sites.txt to dicts with locations and flags (dict with values).
# Rendering & Building
render_nginx_template(template_path: str, context: Dict[str, Any]) -> str: Jinja render, checks template exists.
build_locations_block(locations: Dict[str, str], location_tpl: str) -> str: Build location blocks from template.
# Validation
validate_upstream(upstream: str, fallback: str = DUMMY_UPSTREAM, timeout: int = 1, use_http: bool = True) -> str: Ping/HTTP check, fallback.
# Logs & Dirs
setup_site_logs(site: str, log_dir: str = DEFAULT_LOG_DIR, nginx_user: Optional[str] = None) -> Tuple[str, str]: Create logs, set perms.
ensure_cache_dir(site: str, cache_base: str = DEFAULT_CACHE_BASE) -> str: Create/return cache dir.
# Config Management
write_site_config(site: str, rendered: str, available_dir: str = DEFAULT_SITES_AVAILABLE, enabled_dir: str = DEFAULT_SITES_ENABLED) -> None: Write and enable.
# Cache Management
reload_cache(sites: Union[str, List[str]], flags_dir: str, markers: Dict[str, str], cache_base: str = DEFAULT_CACHE_BASE, cache_combined: str = DEFAULT_CACHE_COMBINED) -> None: Clear and re-apply cache.
# Sync & Remove
sync_sites(sites_list: List[Dict[str, Any]], proxy_tpl: str, serve_tpl: str, location_tpl: str, flags_dir: str, **dirs) -> None: Sync sites, apply flags, cache, dns.
remove_site(site: str, list_path: str, flags_dir: str, **dirs) -> None: Remove from list/config/cache/dns, reload.
# Service Control
manage_nginx_service(pid_file: str = DEFAULT_PID_FILE, nginx_cmd: str = DEFAULT_NGINX_CMD, test_cmd: List[str] = DEFAULT_TEST_CMD, reload_cmd: List[str] = DEFAULT_RELOAD_CMD, start_cmd: List[str] = DEFAULT_START_CMD) -> bool: Test/reload/start.
# Utils
flush_dns() -> None: Flush DNS cache.
generate_sites_from_list(list_path: str, proxy_tpl: str, serve_tpl: str, location_tpl: str, flags_dir: str, **dirs_and_cmds) -> None: Full generation with validation/logs/sync/reload/dns.
# Initialization
init(generate_dir: str = "/etc/nginx/generate-sites", sites_txt: bool = True, manage_py: bool = True) -> None: Set up generate-sites structure with templates, sites.txt, etc.
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
    """Parse sites file to list of dicts {site, upstream, locations: dict, flags: dict}."""
    if not file_exists(list_path):
        raise NginxOpsError(f"sites.txt not found: {list_path}")
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
        flags = {}
        for p in parts[2:]:
            if p.startswith('/'):
                if '=' in p:
                    path, up = p.split('=', 1)
                    locations[path.strip()] = up.strip()
            else:
                if '=' in p:
                    k, v = p.split('=', 1)
                    flags[k.lower()] = v.strip()
                else:
                    flags[p.lower()] = True
        sites.append({"site": site, "upstream": upstream, "locations": locations, "flags": flags})
    log.info(f"Parsed {len(sites)} sites from {list_path}")
    return sites
# Rendering & Building
def render_nginx_template(template_path: str, context: Dict[str, Any]) -> str:
    """Render Nginx template with Jinja, check if exists."""
    if not file_exists(template_path):
        raise NginxOpsError(f"Template not found: {template_path}")
    template = read_file(template_path)
    return render_jinja(template, context)
def build_locations_block(locations: Dict[str, str], location_tpl: str) -> str:
    """Build Nginx location blocks from dict {path: upstream} using template."""
    if not file_exists(location_tpl):
        raise NginxOpsError(f"Location template not found: {location_tpl}")
    tpl = read_file(location_tpl)
    blocks = []
    for path, upstream in locations.items():
        context = {"PATH": path, "UPSTREAM": upstream}
        block = render_jinja(tpl, context)
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
    log.info(f"Setup logs for {site}: {access_log}, {error_log}")
    return access_log, error_log
def ensure_cache_dir(site: str, cache_base: str = DEFAULT_CACHE_BASE) -> str:
    """Create/return per-site cache dir, set perms."""
    cache_dir = os.path.join(cache_base, site)
    ensure_dir(cache_dir)
    set_mode(cache_dir, 0o755)
    log.info(f"Ensured cache dir for {site}: {cache_dir}")
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
    log.info(f"Wrote and enabled config for {site}: {tgt_avail} -> {tgt_enabled}")
# Helper Functions
def find_insert_line(site_conf: str, placement: str = 'server_443_out_after_location') -> Optional[int]:
    """Find the line number to insert a block based on placement."""
    if placement != 'server_443_out_after_location':
        raise NginxOpsError(f"Unsupported placement: {placement}")
    content = read_file(site_conf)
    lines = content.splitlines()
    in_server_443 = False
    location_depth = 0
    prev_location_depth = 0
    for i, line in enumerate(lines):
        if 'listen 443' in line:
            in_server_443 = True
        if in_server_443:
            if 'location / {' in line:
                location_depth = 1
            prev_location_depth = location_depth
            location_depth += line.count('{') - line.count('}')
            if location_depth == 0 and prev_location_depth > 0:
                return i + 1
    log.warning("Could not find insert point")
    return None
def apply_flag(
    flag: str,
    value: Any,
    force: bool,
    site: str,
    site_conf: str,
    flags_dir: str,
    additional_blocks: Dict[str, List[str]],
    dns_sites: List[str],
    dns_meta: Dict[str, Any],
) -> None:
    """Mother function to apply a flag using template and meta."""
    tpl_path = os.path.join(flags_dir, f"{flag}.conf")
    if not file_exists(tpl_path):
        log.warning(f"Flag template not found for {flag}: {tpl_path}")
        return
    tpl = read_file(tpl_path)
    meta = {}
    if tpl.startswith("# META:"):
        lines = tpl.splitlines()
        meta_line = lines[0][7:].strip()
        tpl = "\n".join(lines[1:])
        for pair in meta_line.split(','):
            if '=' in pair:
                k, v = pair.strip().split('=', 1)
                meta[k] = v
    action = meta.get('action', 'insert')
    begin = meta.get('begin', f"# ---- {flag.upper()}-BEGIN ----")
    end = meta.get('end', f"# ---- {flag.upper()}-END ----")
    placement = meta.get('placement', 'server_443_out_after_location')
    pattern = meta.get('pattern')
    default = meta.get('default')
    additional_tpl = meta.get('additional_tpl')
    additional_type = meta.get('additional_type')
    additional_target = meta.get('additional_target')
    mode = meta.get('mode')
    target_dir = meta.get('target_dir', DEFAULT_DNSMASQ_DIR)
    target_conf = meta.get('target_conf', DEFAULT_DNSMASQ_CONF)
    if action == 'dns':
        dns_meta.update({'mode': mode or 'auto', 'target_dir': target_dir, 'target_conf': target_conf, 'additional_target': additional_target})
    context = {'SITE': site, 'VALUE': value if value is not True else '', 'CACHE_DIR': ensure_cache_dir(site) if flag == 'cache' else '', 'IP': DEFAULT_NGINX_IP}
    rendered = render_jinja(tpl, context)
    if begin not in rendered:
        rendered = f"{begin}\n{rendered.strip()}\n{end}"
    has_block = search_in_file(site_conf, begin) and search_in_file(site_conf, end)
    if action == 'insert':
        if value:
            if has_block:
                if force:
                    remove_block_between_markers(site_conf, begin, end)
                    log.info(f"Forced removal of old {flag} block for {site}")
                else:
                    log.info(f"{flag} block already present for {site}")
                    return
            insert_line = find_insert_line(site_conf, placement)
            if insert_line is None:
                raise NginxOpsError(f"Insert line not found for placement {placement}")
            content = read_file(site_conf)
            lines = content.splitlines()
            lines.insert(insert_line, rendered.splitlines())
            atomic_write(site_conf, "\n".join(lines) + "\n")
            log.info(f"Inserted {flag} block for {site}")
        else:
            if has_block:
                remove_block_between_markers(site_conf, begin, end)
                log.info(f"Removed {flag} block for {site}")
    elif action == 'replace':
        if pattern and default:
            if value:
                context['VALUE'] = value
            else:
                context['VALUE'] = default
            rendered = render_jinja(tpl, context)
            replace_regex_in_file(site_conf, pattern, rendered)
            log.info(f"Replaced {flag} for {site}")
    elif action == 'dns':
        if value:
            additional_blocks['dns'].append(rendered)
            dns_sites.append(site)
        else:
            conf = os.path.join(target_dir, f"{site}.conf")
            if file_exists(conf):
                remove_file(conf)
                log.info(f"Removed DNS conf for {site}")
    if value and additional_tpl and additional_type:
        add_path = os.path.join(flags_dir, additional_tpl)
        if file_exists(add_path):
            add_rendered = render_jinja(read_file(add_path), context)
            additional_blocks[additional_type].append(add_rendered)
            log.info(f"Added additional {additional_type} for {flag} in {site}")
# Cache Management
def reload_cache(
    sites: Union[str, List[str]],
    flags_dir: str,
    cache_base: str = DEFAULT_CACHE_BASE,
    cache_combined: str = DEFAULT_CACHE_COMBINED,
) -> None:
    """Clear and re-apply cache for site(s)."""
    if isinstance(sites, str):
        sites = [sites]
    for site in sites:
        cache_dir = os.path.join(cache_base, site)
        if os.path.exists(cache_dir):
            remove_dir(cache_dir, recursive=True)
            log.info(f"Cleared cache dir for {site}: {cache_dir}")
        site_conf = os.path.join(DEFAULT_SITES_ENABLED, site)
        if file_exists(site_conf):
            site_conf = resolve_symlink(site_conf)
            # Apply cache flag as if value=True, force=True
            apply_flag('cache', True, True, site, site_conf, flags_dir, {}, [], {})
        else:
            log.warning(f"Site conf not found for reload cache: {site}")
    manage_nginx_service()
# Sync & Remove
def sync_sites(
    sites_list: List[Dict[str, Any]],
    proxy_tpl: str,
    serve_tpl: str,
    location_tpl: str,
    flags_dir: str,
    **dirs: str,
) -> None:
    """Sync sites: create/remove, apply flags (error, cache, dns, upload, force, locations), cache, dns. Skip existing unless forced."""
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
                remove_site(site, dirs.get("list_path"), flags_dir, **dirs)
                log.info(f"Removed site {site} as not in list")
    # Create/update
    additional_blocks = {'cache_path': [], 'dns': []}
    dns_sites = []
    dns_meta = {}
    nginx_user = detect_nginx_user()
    for s in sites_list:
        site = s['site']
        flags = s['flags']
        tgt_avail = os.path.join(available_dir, site)
        force = 'force' in flags
        if file_exists(tgt_avail) and not force:
            log.info(f"Skipping existing config for {site} (no force flag)")
            # Still apply flags if changed, but for simplicity, assume sync only adds new or forced
            continue
        upstream = validate_upstream(s['upstream'])
        is_serve = upstream.startswith('/')
        template = serve_tpl if is_serve else proxy_tpl
        context = {
            "SITE": site,
            "IP_ADDRESS": upstream if not is_serve else "",
            "ROOT_PATH": upstream if is_serve else "",
            "CLIENT_MAX_BODY_SIZE": flags.get('upload', "10") if not is_serve else flags.get('upload', "0")
        }
        rendered = render_nginx_template(template, context)
        # Additional locations
        locations_block = build_locations_block(s['locations'], location_tpl)
        rendered = replace_substring(rendered, "# Additional locations", locations_block)
        # Write temp for apply
        atomic_write(tgt_avail, rendered)
        # Apply flags
        for flag, value in flags.items():
            if flag in ['force', 'upload']:
                continue  # upload in context, force in logic
            apply_flag(flag, value, force, site, tgt_avail, flags_dir, additional_blocks, dns_sites, dns_meta)
        # Enable
        write_site_config(site, read_file(tgt_avail), available_dir, enabled_dir)
        setup_site_logs(site, log_dir, nginx_user)
    # Handle additional
    if additional_blocks['cache_path']:
        content = "\n".join(additional_blocks['cache_path']) + "\n"
        atomic_write(cache_combined, content)
        log.info(f"Updated combined cache paths: {cache_combined}")
    if additional_blocks['dns'] and dns_meta:
        changed = False
        mode = dns_meta.get('mode', 'auto')
        target_dir = dns_meta.get('target_dir', DEFAULT_DNSMASQ_DIR)
        target_conf = dns_meta.get('target_conf', DEFAULT_DNSMASQ_CONF)
        if mode == 'auto':
            if os.path.exists(target_dir):
                mode = 'per_file'
            else:
                mode = 'append'
        if mode == 'per_file':
            ensure_dir(target_dir)
            current_confs = {f for f in os.listdir(target_dir) if f.endswith(".conf")}
            for i, site in enumerate(dns_sites):
                conf_path = os.path.join(target_dir, f"{site}.conf")
                r = additional_blocks['dns'][i]
                if not file_exists(conf_path) or read_file(conf_path) != r:
                    atomic_write(conf_path, r)
                    set_mode(conf_path, "644")
                    set_owner(conf_path, "root:root")
                    changed = True
                    log.info(f"Updated DNS conf for {site}")
            for conf in current_confs:
                site_from_conf = conf[:-5]
                if site_from_conf not in dns_sites:
                    remove_file(os.path.join(target_dir, conf))
                    changed = True
                    log.info(f"Removed DNS conf for {site_from_conf}")
        elif mode == 'append':
            content = read_file(target_conf)
            lines = [l for l in content.splitlines() if not 'address=/' in l]
            lines.extend(additional_blocks['dns'])
            new_content = "\n".join(lines) + "\n"
            if new_content != content:
                atomic_write(target_conf, new_content)
                changed = True
                log.info("Appended DNS entries to main conf")
        if changed:
            run(["systemctl", "restart", "dnsmasq"], elevated=True)
            log.info("Restarted dnsmasq due to changes")
def remove_site(site: str, list_path: str, flags_dir: str, **dirs: str) -> None:
    """Remove site from list/config/cache/dns, reload."""
    available_dir = dirs.get("available_dir", DEFAULT_SITES_AVAILABLE)
    enabled_dir = dirs.get("enabled_dir", DEFAULT_SITES_ENABLED)
    cache_base = dirs.get("cache_base", DEFAULT_CACHE_BASE)
    cache_combined = dirs.get("cache_combined", DEFAULT_CACHE_COMBINED)
    content = read_file(list_path)
    lines = [l for l in content.splitlines() if not l.strip().startswith(site)]
    atomic_write(list_path, "\n".join(lines) + "\n")
    log.info(f"Removed {site} from sites.txt")
    remove_site_files(site, available_dir, enabled_dir)
    # Remove cache
    remove_site_cache_entries(site, cache_combined, cache_base)
    # Remove dns if template exists
    dns_tpl = os.path.join(flags_dir, "dns.conf")
    if file_exists(dns_tpl):
        # Load meta
        tpl = read_file(dns_tpl)
        meta = {}
        if tpl.startswith("# META:"):
            lines = tpl.splitlines()
            meta_line = lines[0][7:].strip()
            for pair in meta_line.split(','):
                if '=' in pair:
                    k, v = pair.strip().split('=', 1)
                    meta[k] = v
        mode = meta.get('mode', 'auto')
        target_dir = meta.get('target_dir', DEFAULT_DNSMASQ_DIR)
        target_conf = meta.get('target_conf', DEFAULT_DNSMASQ_CONF)
        if mode == 'auto':
            if os.path.exists(target_dir):
                mode = 'per_file'
            else:
                mode = 'append'
        if mode == 'per_file':
            conf = os.path.join(target_dir, f"{site}.conf")
            if file_exists(conf):
                remove_file(conf)
                log.info(f"Removed DNS conf for {site}")
                run(["systemctl", "restart", "dnsmasq"], elevated=True)
        elif mode == 'append':
            content = read_file(target_conf)
            lines = [l for l in content.splitlines() if site not in l]
            new_content = "\n".join(lines) + "\n"
            if new_content != content:
                atomic_write(target_conf, new_content)
                log.info(f"Removed DNS entry for {site} from main conf")
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
        log.info("Nginx reloaded successfully")
        return True
    if os.path.exists(pid_file):
        pid = read_file(pid_file).strip()
        if pid and run(["kill", "-0", pid], no_die=True).returncode == 0:
            run(["kill", "-QUIT", pid])  # Graceful quit
            time.sleep(1)
            log.info(f"Gracefully quit Nginx pid {pid}")
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
    log.info("Flushed DNS cache")
def generate_sites_from_list(
    list_path: str,
    proxy_tpl: str,
    serve_tpl: str,
    location_tpl: str,
    flags_dir: str,
    **dirs_and_cmds: Any,
) -> None:
    """Full pipeline: parse, validate, render (proxy/serve), setup logs, sync, reload."""
    sites = parse_sites_list(list_path)
    sync_sites(sites, proxy_tpl, serve_tpl, location_tpl, flags_dir, list_path=list_path, **dirs_and_cmds)
    flush_dns()
    manage_nginx_service(**dirs_and_cmds)
    if console:
        table = create_rich_table("Generated Sites", ["Site", "Upstream", "Flags"])
        for s in sites:
            flags_str = ", ".join([k if v is True else f"{k}={v}" for k,v in s['flags'].items()])
            table.add_row(s['site'], s['upstream'], flags_str)
        console.print(table)
    log.info("Site generation complete")
def remove_site_cache_entries(site: str, cache_combined: str, cache_base: str) -> None:
    """Helper to remove cache entries/dir."""
    if os.path.exists(cache_combined):
        content = read_file(cache_combined)
        content = re.sub(rf"# ---- CACHE-PATH-BEGIN ----\s*# per-site cache path for {re.escape(site)}\s*.*?\s*# ---- CACHE-PATH-END ----\s*", "", content, flags=re.DOTALL)
        atomic_write(cache_combined, content)
        log.info(f"Removed cache entry for {site} from {cache_combined}")
    remove_dir(os.path.join(cache_base, site), recursive=True)
def remove_site_files(site: str, available_dir: str, enabled_dir: str) -> None:
    """Helper to remove config files."""
    avail = os.path.join(available_dir, site)
    enabled = os.path.join(enabled_dir, site)
    remove_file(enabled)
    remove_file(avail)
    log.info(f"Removed config files for {site}")
# Initialization
def init(generate_dir: str = "/etc/nginx/generate-sites", sites_txt: bool = True, manage_py: bool = True) -> None:
    """Set up the generate-sites folder structure, create templates if source provided, sites.txt, and optional manage_sites.py."""
    ensure_dir(generate_dir)
    tpl_dir = os.path.join(generate_dir, "templates")
    ensure_dir(tpl_dir)
    flags_dir = os.path.join(tpl_dir, "flags")
    ensure_dir(flags_dir)
    # Default templates content from user-provided cats, adjusted
    templates = {
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
    # Additional locations
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
    # Additional locations
}""",
        "location.conf": """location {{PATH}} {
    proxy_pass {{UPSTREAM}};
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300;
    proxy_send_timeout 300;
}""",
        "flags/cache.conf": """# META: action=insert,placement=server_443_out_after_location,additional_tpl=cache-path.conf,additional_type=cache_path,additional_target=/etc/nginx/conf.d/cache-paths.conf
# per-site cache settings for {{SITE}}
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
        "flags/cache-path.conf": """# META: begin=# ---- CACHE-PATH-BEGIN ----,end=# ---- CACHE-PATH-END ----
# per-site cache path for {{SITE}}
# MUST be in http {} context (not inside server {})
proxy_cache_path {{CACHE_DIR}} levels=1:2 keys_zone={{SITE}}_cache:100m max_size=2g inactive=60m use_temp_path=off;""",
        "flags/dns.conf": """# META: action=dns,mode=auto,target_dir=/etc/dnsmasq.d,target_conf=/etc/dnsmasq.conf
address=/{{SITE}}/{{IP}}""",
        "flags/error.conf": """# META: action=insert,placement=server_443_out_after_location
proxy_intercept_errors on;""",
        "flags/upload.conf": """# META: action=replace,pattern=client_max_body_size .* ;,default=10
client_max_body_size {{VALUE}}M ;""",
    }
    for name, content in templates.items():
        path = os.path.join(tpl_dir, name)
        ensure_dir(os.path.dirname(path))
        atomic_write(path, content)
    if sites_txt:
        sites_path = os.path.join(generate_dir, "sites.txt")
        if not os.path.exists(sites_path):
            atomic_write(sites_path, "# site upstream [flags] [/path=upstream]\n")
    if manage_py:
        manage_path = os.path.join(generate_dir, "manage_sites.py")
        if not os.path.exists(manage_path):
            atomic_write(manage_path, "# Placeholder for manage_sites.py\n")
    log.info(f"Initialized generate-sites at {generate_dir} with templates")