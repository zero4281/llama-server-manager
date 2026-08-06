import re

assets = [
    "llama-b10295-bin-ubuntu-openvino-2026.2.1-x64.tar.gz",
    "llama-b10295-bin-ubuntu-rocm-7.2-x64.tar.gz",
    "llama-b10295-bin-ubuntu-x64.tar.gz"
]

new_pattern = r"^llama-[a-zA-Z0-9_.-]+(?:-bin)?-(?P<platform>[a-zA-Z0-9_.-]+(?:-[a-zA-Z0-9_.-]+)*)-(?P<arch>x64|arm64|x86_64)(?:-(?P<variant>\w+))?$"
match_obj = re.compile(new_pattern)

for asset in assets:
    base_name = asset.replace(".tar.gz", "").replace(".tgz", "")
    match = match_obj.match(base_name)
    if match:
        print(f"Asset: {asset}")
        print(f"  Match: {match.groupdict()}")
    else:
        print(f"Asset: {asset}")
        print(f"  No match")
