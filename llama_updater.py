"""
llama_updater.py — llama.cpp download and update module.

This module handles fetching releases from the GitHub API, selecting
the appropriate platform/architecture, downloading and extracting
archives, and managing the llama-cpp installation directory.
"""

import hashlib
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

# Import logger from ui_manager for consistent logging
from ui_manager import logger as ui_logger


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
        if "aarch64" in machine or "arm64" in machine:
            return "Linux", "arm64"
        if "x86_64" in machine or "amd64" in machine:
            return "Linux", "x64"  # Normalize to x64 for matching
        return "Linux", "aarch64"  # fallback

    elif system == "Windows":
        if "aarch64" in machine or "arm64" in machine:
            return "Windows", "arm64"
        if "x86_64" in machine or "amd64" in machine:
            return "Windows", "x64"  # Normalize to x64 for matching
        return "Windows", "x64"  # fallback

    elif system == "Darwin":
        if "aarch64" in machine or "arm64" in machine:
            return "macOS", "arm64"
        if "x86_64" in machine or "amd64" in machine:
            return "macOS", "x64"  # Normalize to x64 for matching
        return "macOS", "x64"  # fallback

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
    
    # Old format: platform-arch[-variant] (e.g., llama-server-linux-arm64)
    # New format: llama-{tag}-bin-{platform}-{arch} (e.g., llama-b8763-bin-ubuntu-x64)
    
    # Try new format first: llama-{tag}-bin-{platform}-{arch}[-variant]
    # Tag can contain hyphens, so we need a more flexible pattern
    # Also handle optional variant suffix like -vulkan, -cuda, etc.
    # Platform can contain hyphens (e.g., rocky-linux), arch is always x64 or arm64
    new_pattern = r"^llama-[a-zA-Z0-9_-]+-bin-([a-zA-Z0-9-]+)-(x64|arm64)(?:-(\w+))?$"
    match = re.match(new_pattern, base_name)
    if match:
        platform = match.group(1).lower()
        arch = match.group(2).lower()
        variant = match.group(3)  # Capture variant if present (e.g., vulkan, cuda)
        # Convert platform names to standard names
        platform_map = {
            "ubuntu": "Linux",
            "openEuler": "Linux",
            "debian": "Linux",
            "centos": "Linux",
            "rocky": "Linux",
            "alpine": "Linux",
            "archlinux": "Linux",
            "fedora": "Linux",
            "redhat": "Linux",
            "rhel": "Linux",
            "amazon": "Linux",
            "oracle": "Linux",
            "suse": "Linux",
            "opensuse": "Linux",
            "gentoo": "Linux",
            "manjaro": "Linux",
            "elementary": "Linux",
            "pop": "Linux",
            "zorin": "Linux",
            "linuxmint": "Linux",
            "deepin": "Linux",
            "kali": "Linux",
            "parrot": "Linux",
        }
        # Handle compound names like rocky-linux
        if platform in platform_map:
            platform_name = platform_map[platform]
        elif '-' in platform and platform.split('-')[0] in platform_map:
            platform_name = platform_map[platform.split('-')[0]]
        else:
            platform_name = platform
        # Capitalize first letter for consistency with test expectations
        platform_name = platform_name.capitalize()
        return {
            "platform": platform_name,
            "arch": arch,
            "variant": variant if variant else None
        }
    
    # Try old format: project-platform-arch
    # e.g., llama-server-linux-arm64
    pattern = r"^(\w+)-(\w+)-(\w+)-(\w+)"
    match = re.match(pattern, base_name)
    if match:
        # group 1: project (llama), group 2: subproject (server), group 3: platform (linux), group 4: arch (arm64)
        # Normalize platform to standard names
        platform_map = {
            "linux": "Linux",
            "windows": "Windows",
            "darwin": "Darwin",
        }
        platform = platform_map.get(match.group(3).lower(), match.group(3))
        arch = match.group(4).lower()
        # Capitalize first letter
        platform = platform.capitalize()
        return {
            "platform": platform,
            "arch": arch,
            "variant": None
        }
        platform = platform_map.get(match.group(2).lower(), match.group(2))
        arch = match.group(3) if match.group(3) else None
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
        if 'sha256' in name_lower or 'checksum' in name_lower or name_lower.endswith('.txt'):
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
            if variant and platform_info.get('variant') == variant:
                return platform_info['assets'][0]
            # If variant is provided but doesn't match, or if no variant is provided, 
            # we fallback to the first asset of the platform/arch match
            if not variant or platform_info.get('variant') is None:
                return platform_info['assets'][0]
            return None

    
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


def verify_checksum(archive_path: Path, checksum_path: Path) -> bool:
    """
    Verify archive against checksum file.
    
    Args:
        archive_path: Path to archive file
        checksum_path: Path to checksum file
    
    Returns:
        True if verification passes
    
    Raises:
        LlamaUpdaterError: If verification fails
    """
    import hashlib
    
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
        
        print(f"Checking checksum...")
        print(f"  Expected: {expected_hash}")
        print(f"  Actual:   {actual_hash_str}")
        
        if actual_hash_str == expected_hash:
            print("Checksum verification passed!")
            return True
        else:
            print("Checksum verification FAILED!")
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


def verify_installation() -> None:
    """
    Run post-install sanity check (llama-server --version).
    
    Executes llama-server --version and displays output.
    If check fails, prints warning but exits with code 0.
    """
    llama_server = LLAMA_CPP_DIR / "llama-server"
    
    if not llama_server.exists():
        print("Warning: Could not find llama-server executable for verification")
        return
    
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
                print(f"llama-server version: {version_output}\n")
        else:
            print(f"\nWarning: llama-server --version returned exit code {result.returncode}")
            print(f"Output: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("\nWarning: llama-server --version timed out")
    except Exception as e:
        print(f"\nWarning: Could not verify llama-server version: {e}")


def delete_existing_installation() -> None:
    """
    Delete existing llama-cpp folder if present.
    
    Removes the folder entirely without prompting or creating backups.
    """
    try:
        if LLAMA_CPP_DIR.exists():
            shutil.rmtree(LLAMA_CPP_DIR)
            ui_logger.debug(f"Deleted existing llama-cpp folder: {LLAMA_CPP_DIR}")
    except Exception as e:
        raise LlamaUpdaterError(f"Failed to delete existing llama-cpp folder: {e}")


def install_release(release: dict, release_tag: str, ui_manager: Optional["UIManager"] = None) -> None:
    """
    Install a llama.cpp release.

    Args:
        release: Release data dictionary
        release_tag: Release tag for reference
        ui_manager: UIManager instance for UI operations
    """
    from ui_manager import UIManager
    
    ui = ui_manager if ui_manager is not None else UIManager("Install llama.cpp")
    
    ui.print_message(f"Installing llama.cpp release {release_tag}...")
    
    # Update config.json with installation info
    import json
    with open("config.json", "r") as f:
        config = json.load(f)
    
    parsed_info = parse_asset_name(release["assets"][0]["name"])
    config["install"] = {
        "release": release_tag,
        "platform": parsed_info["platform"],
        "arch": parsed_info["arch"],
        "backend": parsed_info.get("variant", "")
    }
    
    with open("config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    ui.print_message(f"Config updated with release: {release_tag}")

    # Delete existing installation first
    delete_existing_installation()

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
            'description': f"{asset_count} asset{'' if asset_count == 1 else 's'}" + variant_suffix
        }
        platform_options.append(platform_entry)
    
    # Find the matching platform info for auto-highlight
    default_platform_idx = None
    for i, platform_info in enumerate(available_platforms, 1):
        if platform_info['platform'].lower() == detected_platform.lower() and platform_info['arch'].lower() == detected_arch.lower():
            default_platform_idx = i - 1  # Zero-based index
            break
    
    # Render platform selection menu
    selected_platform_idx = ui.render_menu(platform_options, default=default_platform_idx, highlighted=default_platform_idx)
    
    if selected_platform_idx == -1:
        print("Platform selection cancelled.")
        return
    
    selected_platform_info = available_platforms[selected_platform_idx]
    
    # Prepare zip file options for menu
    zip_options = []
    for i, asset in enumerate(selected_platform_info['assets'], 1):
        is_default = (i == 1)
        marker = " (default)" if is_default else ""
        zip_entry = {
            'label': asset['name'],
            'description': f"{asset['size']//1024//1024}MB {marker}"
        }
        zip_options.append(zip_entry)
    
    # Render zip file selection menu
    selected_zip_idx = ui.render_menu(zip_options, default=0)
    
    if selected_zip_idx == -1:
        print("Zip file selection cancelled.")
        return
    
    selected_asset = selected_platform_info['assets'][selected_zip_idx]
    asset_name = selected_asset['name']
    
    # Show selected release info through UIManager
    ui.print_message(f"\nSelected: {release_tag} ({asset_name})")
    
    # Check UI mode before render_confirmation
    if not ui._using_curses or not ui._screen:
        ui_logger.warning("UI manager not using curses, falling back to console for confirmation")
    
    # Confirmation prompt
    release_info = f"{release_tag} ({asset_name})"
    confirmed = ui.render_confirmation(f"Proceed with installation?", release_info)
    
    if not confirmed:
        print("Installation cancelled.")
        return
    
    ui_logger.debug(f"User confirmed installation of {release_tag} - {asset_name}")

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
                    # Verification failed - clean up
                    archive_path.unlink(missing_ok=True)
                    checksum_path.unlink(missing_ok=True)
                    raise LlamaUpdaterError("Checksum verification failed")
            finally:
                checksum_path.unlink(missing_ok=True)
        else:
            print("No checksum file available for this release, skipping verification")

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
        verify_installation()

        ui.print_message("Installation complete!")

    except Exception as e:
        # Clean up on error
        archive_path.unlink(missing_ok=True)
        raise e


class LlamaUpdater:
    """Main class for llama.cpp download and update operations."""

    def __init__(self):
        self.owner = GITHUB_OWNER
        self.repo = GITHUB_REPO

    def install(self, interactive: bool = False, ui_manager: Optional["UIManager"] = None) -> None:
        """
        Install the latest llama.cpp release.

        Args:
            interactive: If True, allow manual platform selection
            ui_manager: Optional UIManager instance to use for all UI operations
        """
        from ui_manager import UIManager
        
        # Create UI manager for error display if not provided
        ui = ui_manager if ui_manager is not None else UIManager("Update llama.cpp")
        
        ui_logger.debug("Fetching latest llama.cpp release...")
        try:
            release = get_latest_release()
            print(f"DEBUG: release: {release}")
            release_tag = release["tag_name"]
            
            ui_logger.debug(f"Latest release: {release_tag} ({release['name']})")
            ui_logger.debug(f"Published: {release['published_at']}")
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
        # Sort by published_at descending and take 5 most recent
        recent_releases = sorted(releases, key=lambda x: x['published_at'], reverse=True)[:5]
        
        # Prepare tag options for menu
        tag_options = [
            {'label': 'Enter a tag manually', 'description': ''}
        ]
        for i, r in enumerate(recent_releases[1:], 2):
            tag_options.append({
                'label': r['tag_name'],
                'description': 'latest' if r['tag_name'] == release_tag else ''
            })
        # Add remaining 2 recent releases to make 5 total
        for r in recent_releases[1:3]:
            tag_options.append({
                'label': r['tag_name'],
                'description': ''
            })
        
        # Use UIManager for tag selection
        ui = ui_manager if ui_manager is not None else UIManager("Select a Tag for llama.cpp")
        selected_tag_idx = ui.render_menu(tag_options, default=1, highlighted=1)
        
        if selected_tag_idx == -1:
            print("Tag selection cancelled.")
            return
        elif selected_tag_idx == 0:
            # Manual entry
            manual_tag = ui.get_input("Enter release tag: ")
            if not manual_tag:
                print("Tag entry cancelled.")
                return
            release = get_release_by_tag(manual_tag)
            if release is None:
                print(f"Release not found for tag: {manual_tag}")
                return
            release_tag = release["tag_name"]
        else:
            release = releases[selected_tag_idx - 1]
            release_tag = release["tag_name"]

        # Call install_release which handles platform detection, zip selection, and installation
        if release is not None and release_tag:
            install_release(release, release_tag, ui)
        else:
            print("Installation cancelled or failed to select a valid release.")

    def update(self) -> None:
        """
        Update to the latest release.

        This is similar to install() but implies updating existing installation.
        """
        print("Updating llama.cpp to latest release...")
        self.install()


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
            updater.install()
    else:
        # Default: show available releases
        releases = list_releases()
        print(f"Found {len(releases)} releases:")
        for i, r in enumerate(releases[:10], 1):  # Show first 10
            print(f"  {i}. {r['tag_name']} - {r['name']}")


if __name__ == "__main__":
    main()
