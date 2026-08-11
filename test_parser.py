import re
from pathlib import Path
from typing import Dict

known_os = ["linux", "windows", "darwin", "ubuntu", "debian", "centos", "rocky", "alpine", "fedora", "rhel", "amazon", "oracle", "suse", "opensuse", "gentoo", "manjaro", "elementary", "pop", "zorin", "linuxmint", "deepin", "kali", "parrot", "win"]

def parse_asset_name(name: str) -> Dict[str, str]:
    base_name = name
    if name.endswith(".tar.gz") or name.endswith(".tgz"):
        base_name = name.replace(".tar.gz", "").replace(".tgz", "")
    else:
        base_name = Path(name).stem
    
    new_pattern = r"^llama-[a-zA-Z0-9_.-]+-bin-(?P<platform>[a-zA-Z0-9_.-]+?)(?:-(?P<backend>[a-z]+))?-(?P<arch>x64|arm64)(?:-(?P<variant>\w+))?$"
    match = re.match(new_pattern, base_name)
    if match:
        platform_name = match.group('platform')
        arch = match.group('arch')
        variant = match.group('variant')
        backend = match.group('backend')
        
        parts = [p for p in platform_name.split('-') if p != "bin"]
        
        if backend is None:
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
            "variant": None,
            "backend": None
        }
    
    return {"platform": None, "arch": None, "variant": None, "backend": None}

# Test 1: ubuntu-x64
print(f"ubuntu-x64: {parse_asset_name('llama-b8800-bin-ubuntu-x64.tar.gz')}")
# Test 2: ubuntu-vulkan-x64
print(f"ubuntu-vulkan-x64: {parse_asset_name('llama-b8800-bin-ubuntu-vulkan-x64.tar.gz')}")
