from llama_updater import install_release
import json

with open("mock_release.json", "r") as f:
    release = json.load(f)

install_release(release, "b10154")
