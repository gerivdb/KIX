import os

runner_types = {
    'python': 'PythonRunner',
    'zig-binary': 'ZigRunner', 
    'gateway-exe': 'GatewayRunner',
    'rust': 'RustRunner',
    'go': 'GoRunner',
    'node': 'NodeRunner',
    'custom': 'CustomRunner'
}

# Check which runners have implementations
for rtype, class_name in runner_types.items():
    filename = class_name.lower().replace('runner', '_runner') + '.py'
    path = f'D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/runners/{filename}'
    if os.path.exists(path):
        print(f'{rtype}: ✅ {class_name} implemented')
    else:
        print(f'{rtype}: ❌ {class_name} MISSING')
