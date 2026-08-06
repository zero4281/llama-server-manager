import re

base_name = "llama-b10295-bin-ubuntu-openvino-2026.2.1-x64"
# Non-greedy tag part
new_pattern = r"^llama-[a-zA-Z0-9_.-]+?(?:-bin)?-(?P<platform>[a-zA-Z0-9_.-]+(?:-[a-zA-Z0-9_.-]+)*)-(?P<arch>x64|arm64|x86_64)(?:-(?P<variant>\w+))?$"
match = re.match(new_pattern, base_name)
if match:
    print(f"Match: {match.groupdict()}")
else:
    print("No match")
