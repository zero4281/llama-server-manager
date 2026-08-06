"""
llama_updater.py — llama.cpp download and update module.

This module handles fetching releases from the GitHub API, selecting
the appropriate platform/architecture, downloading and extracting
archives, and managing the llama-cpp installation directory.
"""

import argparse
import datetime

import json
import os
import re
import shutil
import subprocess
import sys
import requests
import tempfile
import time
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from runner import Runner
from config import load_config, save_config

import logging
logger = logging.getLogger(__name__)

# Constants
GITHUB_OWNER = "ggml-org"
GITHUB_REPO = "llama.cpp"
GITHUB_API_BASE = "https://api.github.com"
LLAMA_CPP_DIR = Path.cwd() / "llama-cpp"

class LlamaUpdaterError(Exception):
    """Base exception for llama_updater errors."""
    pass

class RateLimitError(LlamaUpdaterError):
    """Raised when GitHub API rate limit is exceeded."""
    def __init__(self, reset_time: str):
        self.reset_time = reset_time
        super().__init__(f"GitHub API rate limit exceeded. Retry after {reset_time}")

class GitHubAPIError(LlamaUpdaterError):
    """Raised when GitHub API is unreachable."""
    def __init__(self, message: str, reset_time: str = 'unknown'):
        self.reset_time = reset_time
        super().__init__(f"GitHub API error: {message}")

class DownloadError(LlamaUpdaterError):
    """Raised when download fails."""
    pass

class ExtractionError(LlamaUpdaterError):
    """Raised when extraction fails."""
    pass

class PlatformNotFoundError(LlamaUpdaterError):
    """Raised when no matching platform is found."""
    pass

# Headers for GitHub API requests
_GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

def _get_api_headers() -> Dict[str, str]:
    """Get headers for GitHub API requests."""
    return _GITHUB_HEADERS.copy()

def detect_platform() -> Tuple[str, str]:
    """
    Detect current platform and architecture.

    Returns:
        Tuple of (system, machine) standardized names.
    """
    import platform
    system = platform.system()
    machine = platform.machine().lower()

    if system == "Linux":
        try:
            distro = platform.freedesktop_os_release().get('NAME', 'Linux')
        except (AttributeError, OSError):
            distro = "Linux"

        if "aarch64" in machine or "arm64" in machine:
            return distro, "arm64"
        if "x86_64" in machine or "amd64" in machine:
            return distro, "x64"  # Normalize to x64 for matching
        return distro, "aarch64"  # fallback

    elif system == "Windows":
        if "aarch64" in machine or "arm64" in machine:
            return "Windows", "arm64"
        if "x86_64" in machine or "amd64" in machine:
            return "Windows", "x64"  # Normalize to x64 for matching
        return "Windows", "x64"  # fallback

    elif system == "Darwin":
        if "aarch64" in machine or "arm64" in machine:
            return "Darwin", "arm64"
        if "x86_64" in machine or "amd64" in machine:
            return "Darwin", "x64"  # Normalize to x64 for matching
        return "Darwin", "x64"  # fallback

    else:
        return system, machine

def _get_release_info(url: str) -> dict:
    """
    Fetch release information from GitHub API.

    Args:
        url: Full API URL for the release

    Returns:
        Release data as dictionary

    Raises:
        GitHubAPIError: If API is unreachable
        RateLimitError: If rate limited
    """
    try:
        response = requests.get(url, headers=_get_api_headers(), timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if hasattr(e, 'response') and e.response is not None:
            status_code = e.response.status_code
            # Check for rate limit headers in 403/429 responses
            reset_header = e.response.headers.get('X-RateLimit-Reset')
            reset_ts = int(reset_header) if reset_header else None
            reset_dt = None
            if reset_ts:
                reset_dt = datetime.datetime.utcfromtimestamp(reset_ts)
                reset_time = reset_dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            else:
                reset_time = 'unknown'
            
            if status_code == 429:
                # Rate limited
                raise RateLimitError(reset_time)
            elif status_code == 403:
                # Check if it's a rate limit 403 (not just forbidden)
                rate_limit_remaining = e.response.headers.get('X-RateLimit-Remaining')
                if rate_limit_remaining == '0':
                    raise RateLimitError(reset_time)
                # Otherwise it's a generic 403
                raise GitHubAPIError(
                    f"GitHub API forbidden (403). "
                    f"Check your network connection or try again later.",
                    reset_time=reset_time
                )
            else:
                raise GitHubAPIError(
                    f"GitHub API error: {status_code} {e.response.text[:200]}",
                    reset_time=reset_time
                )
        else:
            raise GitHubAPIError(f"GitHub API unreachable: {e}")

def get_latest_release() -> dict:
    """
    Get the latest release from llama.cpp repository.

    Returns:
        Release data dictionary
    """
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
    return _get_release_info(url)

def list_releases() -> List[dict]:
    """
    List all releases from llama.cpp repository.

    Returns:
        List of release data dictionaries
    """
    releases = []
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
    page = 1
    max_pages = 5  # GitHub limits to 1000 items by default

    while page <= max_pages and not releases:
        try:
            response = requests.get(url, headers=_get_api_headers(), 
                                   timeout=30, params={'page': page, 'per_page': 100})
            response.raise_for_status()
            page_releases = response.json()
            if not page_releases:
                break
            releases.extend(page_releases)
            page += 1
        except requests.exceptions.RequestException as e:
            # Re-raise if it's a rate limit or other significant error
            if isinstance(e, (RateLimitError, GitHubAPIError)):
                raise
            break

    return releases

def get_release_by_tag(tag: str) -> dict:
    """
    Get a specific release by its tag.

    Args:
        tag: Release tag (e.g., "v0.0.0")

    Returns:
        Release data dictionary
    """
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/tags/{tag}"
    return _get_release_info(url)

def parse_asset_name(name: str) -> Dict[str, str]:
    """
    Parse asset name to extract platform and architecture info.

    Args:
        name: Asset name (e.g., "llama-server-linux-arm64.tar.gz" or
                "llama-b8763-bin-ubuntu-x64.tar.gz")

    Returns:
        Dictionary with parsed info
    """
    # Remove extension (handles .tar.gz, .tgz, .zip, etc.)
    # Remove the extension(s) completely
    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        base_name = name.replace(".tar.gz", "").replace(".tgz", "")
    else:
        base_name = Path(name).stem  # Standard extension removal
    
    # Try new format first: llama-{tag}-bin-{platform}-{arch}[-variant]
    # Tag can contain hyphens, so we need a more flexible pattern
    # Also handle optional variant suffix like -vulkan, -cuda, etc.
    # Platform can contain hyphens (e.g., rocky-linux), arch is always x64 or arm64
    # Try new format first: llama-{tag}-bin-{platform}-{backend}-{arch}[-variant]
    # Tag can contain hyphens, so we need a more flexible pattern
    # Backend is optional, and variant is the optional suffix after architecture
    # Platform can contain hyphens (e.g., rocky-linux), arch is always x64 or arm64
    new_pattern = r"^llama-[a-zA-Z0-9_.-]+-bin-(?P<platform>[a-zA-Z0-9_.-]+(?:-[a-zA-Z0-9_.-]+)*)-(?P<arch>x64|arm64)(?:-(?P<variant>\w+))?$"
    match = re.match(new_pattern, base_name)
    if match:
        platform_name = match.group('platform')
        arch = match.group('arch')
        variant = match.group('variant')
        
        parts = [p for p in platform_name.split('-') if p != "bin"]
        
        known_os = ["linux", "windows", "darwin", "ubuntu", "debian", "centos", "rocky", "alpine", "fedora", "rhel", "amazon", "oracle", "suse", "opensuse", "gentoo", "manjaro", "elementary", "pop", "zorin", "linuxmint", "deepin", "kali", "parrot", "win"]
        
        platform_name = ""
        backend = None
        
        if len(parts) == 1:
            platform_name = parts[0].capitalize()
            backend = None
        elif len(parts) == 2:
            if parts[0].lower() in known_os and parts[1].lower() in known_os:
                platform_name = f"{parts[0]}-{parts[1]}".capitalize()
                backend = None
            elif parts[0].lower() in known_os:
                platform_name = parts[0].capitalize()
                backend = parts[1]
            else:
                platform_name = f"{parts[0]}-{parts[1]}".capitalize()
                backend = None
        else:
            if parts[0].lower() == "rocky" and parts[1].lower() == "linux":
                platform_name = "Linux"
                backend = "-".join(parts[2:])
            elif parts[0].lower() in known_os and parts[1].lower() in known_os:
                platform_name = f"{parts[0]}-{parts[1]}".capitalize()
                backend = "-".join(parts[2:])
            elif parts[0].lower() in known_os:
                platform_name = parts[0].capitalize()
                backend = "-".join(parts[1:])
            else:
                platform_name = f"{parts[0]}-{parts[1]}".capitalize()
                backend = "-".join(parts[2:])


        
        platform_map = {
            "linux": "Linux",
            "windows": "Windows",
            "darwin": "Darwin",
        }
        final_platform = platform_name
        if final_platform not in platform_map and final_platform.lower() in platform_map:
            final_platform = platform_map[final_platform.lower()]
        elif final_platform.lower() in platform_map:
            final_platform = platform_map[final_platform.lower()]
            
        return {
            "platform": final_platform,
            "arch": arch,
            "backend": backend,
            "variant": variant if variant else None
        }
            
    # Try old format: project-platform-arch
    # e.g., llama-server-linux-arm64
    pattern = r"^llama-.*-(x64|arm64)$"
    match = re.match(pattern, base_name)
    if match:
        platform_map = {
            "linux": "Linux",
            "windows": "Windows",
            "darwin": "Darwin",
        }
        parts = base_name.split('-')
        arch = parts[-1].lower()
        platform_parts = []
        for i in range(2, len(parts) - 1):
            if parts[i] != "bin":
                platform_parts.append(parts[i])
        
        if len(platform_parts) == 1:
            platform_name = platform_parts[0].capitalize()
            backend = None
        elif len(platform_parts) == 2:
            if platform_parts[0] in known_os and platform_parts[1] in known_os:
                platform_name = f"{platform_parts[0]}-{platform_parts[1]}".capitalize()
                backend = None
            elif platform_parts[0] in known_os:
                platform_name = platform_parts[0].capitalize()
                backend = platform_parts[1]
            else:
                platform_name = f"{platform_parts[0]}-{platform_parts[1]}".capitalize()
                backend = None
        else:
            if platform_parts[0] == "rocky" and platform_parts[1] == "linux":
                platform_name = "Linux"
                backend = "-".join(platform_parts[2:])
            elif platform_parts[0] in known_os and platform_parts[1] in known_os:
                platform_name = f"{platform_parts[0]}-{platform_parts[1]}".capitalize()
                backend = "-".join(platform_parts[2:])
            elif platform_parts[0] in known_os:
                platform_name = platform_parts[0].capitalize()
                backend = "-".join(platform_parts[1:])
            else:
                platform_name = f"{platform_parts[0]}-{platform_parts[1]}".capitalize()
                backend = "-".join(platform_parts[2:])

            
        platform = platform_map.get(platform_name.lower(), platform_name)
        
        return {
            "platform": platform,
            "arch": arch,
            "variant": None
        }
        
    return {"platform": None, "arch": None, "variant": None}

def get_available_platforms(release: dict) -> List[dict]:
    """
    Get list of available platform/architecture options from release assets.

    Args:
        release: Release data dictionary

    Returns:
        List of platform options
    """
    platforms = {}

    for asset in release.get("assets", []):
        parsed = parse_asset_name(asset["name"])
        if parsed["platform"] and parsed["arch"]:
            key = (parsed["platform"], parsed["arch"])
            if key not in platforms:
                platforms[key] = {
                    "platform": parsed["platform"],
                    "arch": parsed["arch"],
                    "variant": parsed["variant"],
                    "assets": [asset]
                }
            else:
                platforms[key]["assets"].append(asset)

    return list(platforms.values())

def get_checksum_assets(release: dict) -> List[dict]:
    """
    Get checksum assets from release.
    
    Args:
        release: Release data dictionary
    
    Returns:
        List of checksum asset dictionaries
    """
    checksum_assets = []
    for asset in release.get('assets', []):
        name_lower = asset['name'].lower()
        # Check for common checksum file patterns
        # - Standard patterns: .sha256sum.txt, .sha256sum
        # - Contains sha256 or checksum (case-insensitive)
        # - Common patterns: sha256sums, checksums, sha256sums.txt, checksums.txt
        if (name_lower.endswith('.sha256sum.txt') or 
            name_lower.endswith('.sha256sum') or
            'sha256' in name_lower or 
            'checksum' in name_lower or
            name_lower.endswith('sha256sums') or
            name_lower.endswith('checksums') or
            name_lower.endswith('sha256sums.txt') or
            name_lower.endswith('checksums.txt') or
            name_lower == 'sha256sums' or
            name_lower == 'checksums'):
            checksum_assets.append(asset)
    return checksum_assets

def download_checksum(archive_path: Path, checksum_asset: dict, ui_manager: Optional["UIManager"] = None) -> Path:
    """
    Download checksum file.
    
    Args:
        archive_path: Path to archive file
        checksum_asset: Checksum asset dictionary
        ui_manager: UIManager instance for rendering progress bar
    
    Returns:
        Path to downloaded checksum file
    """
    checksum_path = archive_path.with_suffix('.sha256sum.txt')
    download_file(checksum_asset['browser_download_url'], checksum_path, ui_manager=ui_manager)
    return checksum_path

def select_release(release: dict, available_platforms: List[dict], 
                    detected_platform: str, detected_arch: str) -> Optional[dict]:
    """
    Select the appropriate release asset based on platform and architecture.

    Args:
        release: Release data dictionary
        available_platforms: List of platform options
        detected_platform: Detected platform name
        detected_arch: Detected architecture

    Returns:
        Selected asset dictionary, or None if no match found
    """
    detected_key = (detected_platform, detected_arch)
    
    # Find matching platform in available_platforms
    for platform_info in available_platforms:
        if platform_info['platform'].lower() == detected_platform.lower() and platform_info['arch'].lower() == detected_arch.lower():
            return platform_info['assets'][0]
    
    # If no exact match, show options and let user choose
    return None

def download_file(url: str, output_path: Path, ui_manager: Optional["UIManager"] = None) -> Path:
    """
    Download file from URL to output path with continuous progress bar.

    Args:
        url: Download URL
        output_path: Destination path
        ui_manager: UIManager instance for rendering progress bar

    Returns:
        Path to downloaded file

    Raises:
        DownloadError: If download fails
    """
    from ui_manager import UIManager
    
    ui = ui_manager if ui_manager is not None else UIManager("Download llama.cpp")
    
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        total = int(response.headers.get('content-length', 0))
        downloaded = 0
        start_time = time.time()
        speed = 0
        last_update = time.time()
        update_interval = 0.1  # Update every 100ms
        
        with open(output_path, 'wb') as f:
            # Use iter_bytes() for more control over chunk processing
            for data in response.iter_content(chunk_size=8192):
                if not data:  # Skip empty chunks
                    continue
                
                f.write(data)
                downloaded += len(data)
                
                # Calculate speed (bytes per second)
                elapsed = time.time() - start_time
                if elapsed > 0:
                    speed = downloaded / elapsed
                
                # Calculate estimated time remaining
                if total > downloaded and speed > 0:
                    remaining = total - downloaded
                    eta_seconds = int(remaining / speed)
                    eta_minutes = eta_seconds // 60
                    eta_seconds = eta_seconds % 60
                    eta_str = f"{eta_minutes}m {eta_seconds}s"
                else:
                    eta_str = ""
                
                # Get filename from path
                filename = output_path.name
                
                # Calculate progress percentage
                if total > 0:
                    progress_pct = (downloaded / total) * 100
                else:
                    progress_pct = 0
                
                # Update progress bar continuously without waiting for input
                ui.render_progress_bar(
                    filename=filename,
                    current=downloaded,
                    total=total,
                    speed=speed,
                    percent=progress_pct,
                    estimated_time=eta_seconds if eta_str else None
                )
                
        return output_path
    
    except requests.exceptions.RequestException as e:
        raise DownloadError(f"Download failed: {e}")

def extract_archive(archive_path: Path, dest_dir: Path) -> None:
    """
    Extract archive to destination directory.

    Args:
        archive_path: Path to archive file
        dest_dir: Destination directory

    Raises:
        ExtractionError: If extraction fails
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Extract to temp dir first
            if archive_path.suffix == '.zip':
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
            elif archive_path.suffix in ('.tar.gz', '.tgz'):
                with tarfile.open(archive_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(tmpdir)
            else:
                # Try to detect file type
                if archive_path.suffix == '.tar':
                    with tarfile.open(archive_path, 'r') as tar_ref:
                        tar_ref.extractall(tmpdir)
                elif archive_path.suffix == '.gz':
                    with tarfile.open(archive_path, 'r:gz') as tar_ref:
                        tar_ref.extractall(tmpdir)
                else:
                    # Try default zip extraction
                    with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                        zip_ref.extractall(tmpdir)
            
            # Move contents to dest_dir
            extracted_root = Path(tmpdir)
            
            # Find the root extracted directory
            for item in extracted_root.iterdir():
                if item.is_dir() and item.name != '__MACOSX':
                    shutil.move(str(item), str(dest_dir))
                    break
            
    except Exception as e:
        raise ExtractionError(f"Extraction failed: {e}")

def verify_checksum(archive_path: Path, checksum_path: Path, ui_manager: Optional["UIManager"] = None) -> bool:
    """
    Verify archive against checksum file.
    
    Args:
        archive_path: Path to archive file
        checksum_path: Path to checksum file
        ui_manager: UIManager instance for rendering progress bar
    
    Returns:
        True if verification passes
    
    Raises:
        LlamaUpdaterError: If verification fails
    """
    import hashlib
    
    ui = ui_manager if ui_manager is not None else UIManager("Verify Checksum")
    
    try:
        # Calculate actual hash of archive
        actual_hash = hashlib.sha256()
        with open(archive_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                actual_hash.update(chunk)
        actual_hash_str = actual_hash.hexdigest()
        
        # Read expected hash from checksum file
        with open(checksum_path, 'r') as f:
            checksum_data = f.read().strip()
        
        # Parse expected hash (format: "hash  filename" or just "hash")
        expected_hash = checksum_data.split()[0]
        
        ui.print_message(f"Checking SHA-256 checksum...")
        ui.print_message(f"  Expected: {expected_hash}")
        ui.print_message(f"  Actual:   {actual_hash_str}")
        
        if actual_hash_str == expected_hash:
            ui.print_message("Checksum verification passed!")
            return True
        else:
            ui.render_error("Checksum verification FAILED!")
            raise LlamaUpdaterError(
                f"Checksum mismatch! Archive may be corrupted or tampered. "
                f"Please try again or contact support."
            )
    
    except Exception as e:
        raise LlamaUpdaterError(f"Checksum verification failed: {e}")

def ensure_executable(path: Path) -> None:
    """
    Make file executable on Unix systems.
    
    Args:
        path: Path to file
    """
    if sys.platform != 'win32':
        try:
            os.chmod(path, 0o755)
        except OSError:
            pass  # Ignore permission errors

def verify_installation(ui_manager: Optional["UIManager"] = None) -> bool:
    """
    Run post-install sanity check (llama-server --version).
    
    Executes llama-server --version and displays output.
    If check fails, displays a warning but exits with code 0.
    
    Returns:
        bool: True if sanity check passed, False otherwise.
    """
    from ui_manager import UIManager
    ui = ui_manager if ui_manager is not None else UIManager("Verify Installation")
    
    llama_server = LLAMA_CPP_DIR / "llama-server"
    
    if not llama_server.exists():
        ui.print_message("Warning: Could not find llama-server executable for verification")
        return False
    
    try:
        result = subprocess.run(
            [str(llama_server), "--version"],
            stdout=subprocess.PIPE,          
            stderr=subprocess.STDOUT,        
            text=True,                       
            timeout=10                       
        )
        
        if result.returncode == 0:
            import re                                                          
            match = re.search(r'version:\s*(.+)$', result.stdout, re.MULTILINE)
            if match:
                version_output = match.group(1).strip()
                ui.print_message(f"llama-server version: {version_output}\n")
            else:
                ui.print_message(f"llama-server version: {result.stdout.strip()}")
            return True
        else:
            ui.render_error(f"Warning: llama-server --version returned exit code {result.returncode}\nOutput: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        ui.render_error("\nWarning: llama-server --version timed out")
        return False
    except Exception as e:
        ui.render_error(f"\nWarning: Could not verify llama-server version: {e}")
        return False

def ensure_executable(path: Path) -> None:
    """
    Make file executable on Unix systems.
    """
    if sys.platform != 'win32':
        try:
            os.chmod(path, 0o755)
        except OSError:
            pass  # Ignore permission errors


def _restart_llama_server(ui_manager, args, config, is_verified=True):
    pid_file = Path.cwd() / "llama-server.pid"
    if not pid_file.exists():
        return
    
    try:
        pid = int(pid_file.read_text().strip())
    except (ValueError, OSError):
        pid_file.unlink(missing_ok=True)
        return
    
    try:
        os.kill(pid, 0)
    except OSError:
        pid_file.unlink(missing_ok=True)
        return
    
    runner = Runner(args, config, ui_manager)
    runner.stop_server()
    
    if is_verified:
        runner = Runner(argparse.Namespace(), load_config(), ui_manager)
        runner.run()
    else:
        ui_manager.print_message("The previously running llama-server instance was stopped because the new binary failed its sanity check.")




def install_release(release: dict, release_tag: str, ui_manager: Optional["UIManager"] = None, args: Optional[argparse.Namespace] = None, config: Optional[dict] = None) -> None:
    """
    Install a llama.cpp release.
    
    Args:
        release: Release data dictionary
        release_tag: Release tag for reference
        ui_manager: UIManager instance for UI operations
    """
    config = config if config is not None else load_config()
    from ui_manager import UIManager
    ui = ui_manager if ui_manager is not None else UIManager("Install llama.cpp")
    config = load_config()
    
    
    ui.print_message(f"Installing llama.cpp release {release_tag}...")
    
    # Detect platform
    detected_platform, detected_arch = detect_platform()
    
    # Get available platforms
    available_platforms = get_available_platforms(release)
    
    # Prepare platform options for menu
    platform_options = []
    for i, platform_info in enumerate(available_platforms, 1):
        asset_count = len(platform_info['assets'])
        variant_suffix = " (variant: " + platform_info['variant'] + ")" if platform_info['variant'] else ""
        platform_entry = {
            'label': f"{platform_info['platform']} {platform_info['arch']}",
            'description': variant_suffix
        }
        platform_options.append(platform_entry)

    if not platform_options:
        ui.render_error("No compatible assets found for this release.")
        return

    # Find the matching platform info for auto-highlight

    default_platform_idx = None
    for i, platform_info in enumerate(available_platforms, 1):
        if platform_info['platform'].lower() == detected_platform.lower() and platform_info['arch'].lower() == detected_arch.lower():
            default_platform_idx = i - 1  # Zero-based index
            break
    
    # Render platform selection menu
    selected_platform_idx = ui.render_menu(platform_options, default=default_platform_idx, highlighted=default_platform_idx, title="Select Operating System & Architecture")
    
    if selected_platform_idx == -1:
        ui.render_error("Platform selection cancelled.")
        return
    
    selected_platform_info = available_platforms[selected_platform_idx]
    
    # Compute Backend selection
    # Extract backends from assets
    backends = set()
    for asset in selected_platform_info['assets']:
        parsed = parse_asset_name(asset['name'])
        if parsed['backend']:
            backends.add(parsed['backend'])
        else:
            backends.add('cpu')
    
    sorted_backends = sorted(list(backends))
    
    if not sorted_backends:
        sorted_backends = ['cpu']
    
    # Render Compute Backend selection menu
    backend_options = []
    for i, backend in enumerate(sorted_backends, 1):
        backend_entry = {
            'label': backend,
            'description': ''
        }
        backend_options.append(backend_entry)
    
    selected_backend_idx = ui.render_menu(backend_options, default=0, title="Select Compute Backend")
    
    if selected_backend_idx == -1:
        ui.render_error("Compute Backend selection cancelled.")
        return
    
    selected_backend = sorted_backends[selected_backend_idx]
    if not selected_backend:
        selected_backend = 'cpu'
    
    # Filter assets by selected backend
    # Assets with no backend segment in filename are considered 'cpu'
    filtered_assets = []
    for asset in selected_platform_info['assets']:
        parsed = parse_asset_name(asset['name'])
        if parsed['backend'] == selected_backend:
            filtered_assets.append(asset)
        elif not parsed['backend'] and selected_backend == 'cpu':
            filtered_assets.append(asset)
    
    # Select the first matching asset
    selected_asset = filtered_assets[0]
    asset_name = selected_asset['name']
    
    # Show selected release info through UIManager
    ui.print_message(f"\nSelected: {release_tag} ({asset_name})")
    
    # Check UI mode before render_confirmation
    if not ui._using_curses or not ui._screen:
        ui.render_error("UI manager not using curses, falling back to console for confirmation")
    
    # Confirmation prompt
    release_info = f"{release_tag} ({asset_name})"
    confirmed = ui.render_confirmation(f"Proceed with installation?", release_info)
    
    if not confirmed:
        ui.render_error("Installation cancelled.")
        return
    
    logger.debug(f"User confirmed installation of {release_tag} - {asset_name}")
    
    # Delete existing installation first
    delete_existing_installation()

    # Download
    ui.print_message(f"\nDownloading {asset_name}...")
    archive_path = Path(tempfile.gettempdir()) / f"{asset_name}"
    
    try:
        download_file(selected_asset['browser_download_url'], archive_path, ui_manager=ui)
        ui.print_message(f"Downloaded to {archive_path}")
        
        # Check for checksum file
        checksum_assets = get_checksum_assets(release)
        if checksum_assets:
            ui.print_message("Checking checksum...")
            checksum_asset = checksum_assets[0]
            checksum_path = download_checksum(archive_path, checksum_asset, ui_manager=ui)
            
            try:
                if not verify_checksum(archive_path, checksum_path):
                    archive_path.unlink(missing_ok=True)
                    checksum_path.unlink(missing_ok=True)
                    raise LlamaUpdaterError("Checksum verification failed")
            finally:
                    checksum_path.unlink(missing_ok=True)
        else:
            ui.print_message("No checksum file available for this release, skipping verification")
        
        # Extract
        ui.print_message(f"\nExtracting to {LLAMA_CPP_DIR}")
        extract_archive(archive_path, LLAMA_CPP_DIR)
        
        # Ensure llama-server is executable
        llama_server = LLAMA_CPP_DIR / "llama-server"
        if llama_server.exists():
            ensure_executable(llama_server)
            ui.print_message(f"Made {llama_server} executable")
        
        # Clean up
        archive_path.unlink(missing_ok=True)
        
        # Post-install sanity check
        is_verified = verify_installation(ui)
        
        pid_file = Path.cwd() / "llama-server.pid"
        if pid_file.exists():
            _restart_llama_server(ui, args if args is not None else argparse.Namespace(), config, is_verified=is_verified)
        else:
            ui.print_message("No running llama-server detected.")
        options = config.get("options", {})
        llama_cpp = options.get("llama-cpp", {})
        llama_cpp["os-architecture"] = f"{selected_platform_info['platform']}-{selected_platform_info['arch']}"
        llama_cpp["backend"] = selected_backend
        options["llama-cpp"] = llama_cpp
        config["options"] = options
        try:
            save_config(config)
        except Exception as e:
            ui.render_error(f"Warning: Could not save configuration: {e}")
        
    except Exception as e:
        archive_path.unlink(missing_ok=True)
        raise e

def delete_existing_installation() -> None:
    """
    Deletes the existing llama-cpp installation directory.
    """
    if LLAMA_CPP_DIR.exists():
        shutil.rmtree(LLAMA_CPP_DIR, ignore_errors=True)

def _install_release_core(release: dict, release_tag: str, platform: str, arch: str, backend: str, ui_manager: Optional["UIManager"] = None, skip_confirmation: bool = False, is_verified: bool = True) -> None:
    """
    Core installation logic for llama.cpp.
    
    Args:
        release: Release data dictionary
        release_tag: Release tag
        platform: Target platform
        arch: Target architecture
        backend: Target compute backend
        ui_manager: UI manager instance
        skip_confirmation: If True, skip the confirmation prompt
        is_verified: Whether the installation was verified by a sanity check
    """
    from ui_manager import UIManager
    ui = ui_manager if ui_manager is not None else UIManager("Install llama.cpp")
    config = load_config()
    
    # Delete existing installation first
    delete_existing_installation()
    
    # Filter assets by platform and architecture
    filtered_assets = []
    for asset in release.get("assets", []):
        parsed = parse_asset_name(asset['name'])
        if parsed.get('platform') and parsed.get('arch') and parsed['platform'].lower() == platform.lower() and parsed['arch'].lower() == arch.lower():
            
            
            if parsed['backend'] == backend:
                filtered_assets.append(asset)
            elif not parsed['backend'] and backend == 'cpu':
                filtered_assets.append(asset)
    
    if not filtered_assets:
        ui.render_error(f"No matching assets found for {platform}-{arch} with backend {backend}")
        raise PlatformNotFoundError(f"No matching assets found for {platform}-{arch} with backend {backend}")
    
    selected_asset = filtered_assets[0]
    asset_name = selected_asset['name']
    
    ui.print_message(f"\nSelected: {release_tag} ({asset_name})")
    
    if not skip_confirmation:
        release_info = f"{release_tag} ({asset_name})"
        confirmed = ui.render_confirmation(f"Proceed with installation?", release_info)
        if not confirmed:
            ui.render_error("Installation cancelled.")
            return
    
    logger.debug(f"User confirmed installation of {release_tag} - {asset_name}")
    
    # Download
    ui.print_message(f"\nDownloading {asset_name}...")
    archive_path = Path(tempfile.gettempdir()) / f"{asset_name}"
    
    try:
        download_file(selected_asset['browser_download_url'], archive_path, ui_manager=ui)
        ui.print_message(f"Downloaded to {archive_path}")
        
        # Check for checksum file
        checksum_assets = get_checksum_assets(release)
        if checksum_assets:
            ui.print_message("Checking checksum...")
            checksum_asset = checksum_assets[0]
            checksum_path = download_checksum(archive_path, checksum_asset, ui_manager=ui)
            
            try:
                if not verify_checksum(archive_path, checksum_path):
                    archive_path.unlink(missing_ok=True)
                    checksum_path.unlink(missing_ok=True)
                    raise LlamaUpdaterError("Checksum verification failed")
            finally:
                    checksum_path.unlink(missing_ok=True)
        else:
            ui.print_message("No checksum file available for this release, skipping verification")
            
        # Extract
        ui.print_message(f"\nExtracting to {LLAMA_CPP_DIR}")
        extract_archive(archive_path, LLAMA_CPP_DIR)
        
        # Ensure llama-server is executable
        llama_server = LLAMA_CPP_DIR / "llama-server"
        if llama_server.exists():
            ensure_executable(llama_server)
            ui.print_message(f"Made {llama_server} executable")
        
        # Clean up
        archive_path.unlink(missing_ok=True)
        
        # Post-install sanity check
        is_verified_check = verify_installation(ui)
        
        ui.print_message("Installation complete!")
        
        # Restart server if needed
        pid_file = Path.cwd() / "llama-server.pid"
        if pid_file.exists():
            _restart_llama_server(ui, argparse.Namespace(), config, is_verified=is_verified_check)
        else:
            ui.print_message("No running llama-server detected.")
        
        # Persist configuration
        options = config.get("options", {})

        llama_cpp = options.get("llama-cpp", {})
        llama_cpp["os-architecture"] = f"{platform}-{arch}"
        llama_cpp["backend"] = backend
        options["llama-cpp"] = llama_cpp
        config["options"] = options
        try:
            save_config(config)
        except Exception as e:
            ui.render_error(f"Warning: Could not save configuration: {e}")
        
    except Exception as e:
        archive_path.unlink(missing_ok=True)
        raise e

    
class LlamaUpdater:
    """Main class for llama.cpp download and update operations."""
    
    def __init__(self, ui_manager: Optional["UIManager"] = None):
        self.ui = ui_manager
        self.owner = GITHUB_OWNER
        self.repo = GITHUB_REPO
        self.ui_manager = ui_manager
    
    def install(self, interactive: bool = False, ui_manager: Optional["UIManager"] = None, args: Optional[argparse.Namespace] = None) -> None:
        """
        Install the latest llama.cpp release.
        
        Args:
            interactive: If True, allow manual platform selection
            ui_manager: Optional UIManager instance to use for all UI operations
        """
        from ui_manager import UIManager
        
        # Create UI manager for error display if not provided
        ui = ui_manager if ui_manager is not None else UIManager("Update llama.cpp")
        
        logger.debug("Fetching latest llama.cpp release...")
        try:
            release = get_latest_release()
            release_tag = release["tag_name"]
            
            logger.debug(f"Latest release: {release_tag} ({release['name']})")
            logger.debug(f"Published: {release['published_at']}")
        except RateLimitError as e:
            ui.render_error(
                f"GitHub API rate limit exceeded.\n"
                f"Please wait until: {e.reset_time}\n\n"
                f"You can try again later or use a different network connection."
            )
            return
        except GitHubAPIError as e:
            reset_msg = f"\nRetries available after: {e.reset_time}" if e.reset_time != 'unknown' else ""
            ui.render_error(
                f"Failed to fetch release information.\n"
                f"{e}\n\n{reset_msg}"
            )
            return
        
        # Get list of recent releases for tag selection menu
        releases = list_releases()
        # Sort by published_at descending
        sorted_releases = sorted(releases, key=lambda x: x['published_at'], reverse=True)
        
        # Filter out the current release_tag to avoid duplicates
        unique_recent_releases = []
        for rel in sorted_releases:
            if rel['tag_name'] != release_tag and rel['tag_name'] not in [r['tag_name'] for r in unique_recent_releases]:
                unique_recent_releases.append(rel)
            if len(unique_recent_releases) == 5:
                break
        
        # Prepare tag options for menu
        tag_options = [
            {'label': 'Enter a tag manually', 'description': ''}
        ]
        for i, r in enumerate(unique_recent_releases, 2):
            tag_options.append({
                'label': r['tag_name'],
                'description': 'latest' if r['tag_name'] == release_tag else ''
            })
        
        # Use UIManager for tag selection
        ui = ui_manager if ui_manager is not None else UIManager("Select a Tag for llama.cpp")
        selected_tag_idx = ui.render_menu(tag_options, default=1, highlighted=1, title="Select a Release")
        
        if selected_tag_idx == -1:
            ui.render_error("Tag selection cancelled.")
            return
        elif selected_tag_idx == 0:
            # Manual entry
            manual_tag = ui.get_input("Enter release tag: ")
            if not manual_tag:
                ui.render_error("Tag entry cancelled.")
                return
            release = get_release_by_tag(manual_tag)
            if release is None:
                ui.render_error(f"Release not found for tag: {manual_tag}")
                return
            release_tag = release["tag_name"]
        else:
            release = releases[selected_tag_idx - 1]
            release_tag = release["tag_name"]
        
        # Call install_release which handles platform detection, zip selection, and installation
        if release is not None and release_tag:
            install_release(release, release_tag, ui, args=args)
        else:
            ui.render_error("Installation cancelled or failed to select a valid release.")
        
    def update(self, ui_manager: Optional["UIManager"] = None) -> None:
        """
        Update to the latest release.
        
        Args:
            ui_manager: UIManager instance for UI operations
        """
        from ui_manager import UIManager
        ui = ui_manager if ui_manager is not None else UIManager("Update llama.cpp")
        ui.print_message("Updating llama.cpp to latest release...")
        
        config = load_config()
        options = config.get("options", {})
        llama_cpp = options.get("llama-cpp", {})
        
        os_arch = llama_cpp.get("os-architecture")
        backend = llama_cpp.get("backend")
        
        if os_arch and backend:
            logger.debug(f"Fast path detected: os-architecture={os_arch}, backend={backend}")
            
            # Resolve platform and arch from os_arch
            # Assuming os_arch is in format 'platform-arch' (e.g. 'linux-x64')
            parts = os_arch.split('-')
            if len(parts) != 2:
                ui.render_error("Invalid os-architecture in configuration. Expected 'platform-arch'.")
                return
            platform, arch = parts[0].capitalize(), parts[1]
            
            try:
                release = get_latest_release()
                release_tag = release["tag_name"]
                
                # Filter assets
                filtered_assets = []
                for asset in release.get("assets", []):
                    parsed = parse_asset_name(asset['name'])
                    if parsed.get('platform') and parsed.get('arch') and parsed['platform'].lower() == platform.lower() and parsed['arch'].lower() == arch.lower():
                        if parsed['backend'] == backend:
                            filtered_assets.append(asset)
                        elif not parsed['backend'] and backend == 'cpu':
                            filtered_assets.append(asset)


                
                if not filtered_assets:
                    ui.render_error(f"No matching assets found for {platform}-{arch} with backend {backend}")
                    raise PlatformNotFoundError(f"No matching assets found for {platform}-{arch} with backend {backend}")
                
                # Perform installation
                # We can reuse the logic in _install_release_core
                is_verified = verify_installation(ui)
                _install_release_core(release, release_tag, platform, arch, backend, ui, skip_confirmation=True, is_verified=is_verified)
            except PlatformNotFoundError as e:

                ui.render_error(str(e))
                sys.exit(1)
            except Exception as e:
                ui.render_error(f"Fast path update failed: {e}")
                return
        else:
            self.install(ui_manager=ui)
    
    
def main():
    """CLI entry point for llama_updater."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Download and install llama.cpp releases")
    parser.add_argument("--install", action="store_true", help="Install latest release")
    parser.add_argument("--update", action="store_true", help="Update to latest release")
    parser.add_argument("--tag", type=str, help="Specific release tag to install")
    
    args = parser.parse_args()
    
    if args.tag:
        # Install specific tag
        release = get_release_by_tag(args.tag)
        install_release(release, args.tag)
    elif args.install or args.update:
        updater = LlamaUpdater()
        if args.update:
            updater.update()
        else:
            updater.install(args=args)
    else:
        # Default: show available releases
        releases = list_releases()
        ui.print_message(f"Found {len(releases)} releases:")
        for i, r in enumerate(releases[:10], 1):  # Show first 10
            ui.print_message(f"  {i}. {r['tag_name']} - {r['name']}")
    
    
if __name__ == "__main__":
    main()
