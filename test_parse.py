from llama_updater import parse_asset_name

names = [
    'llama-b10357-bin-ubuntu-openvino-2026.2.1-x64.tar.gz',
    'llama-b10357-bin-ubuntu-rocm-7.14-x64.tar.gz',
    'llama-b10357-bin-ubuntu-sycl-fp16-x64.tar.gz',
    'llama-b10357-bin-ubuntu-sycl-fp32-x64.tar.gz',
    'llama-b10357-bin-ubuntu-vulkan-x64.tar.gz',
    'llama-b10357-bin-ubuntu-x64.tar.gz'
]

for name in names:
    parsed = parse_asset_name(name)
    print('Name: %s | Platform: %s | Backend: %s' % (name, parsed['platform'], parsed['backend']))
