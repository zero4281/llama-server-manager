from llama_updater import get_release_by_tag
release = get_release_by_tag('b10146')
for a in release['assets']:
    print(f"{a['name']} - {a['size']}")
