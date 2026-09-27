import re

with open('D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/src/app.py', encoding='utf-8') as f:
    content = f.read()

# Find endpoints with config:write
pattern = r'@requires_capability\("config:write"\)\s*\n\s*@app\.(get|post|put|delete|patch)\([^)]+\)\s*\n\s*def (\w+)'
matches = re.findall(pattern, content)
print('Endpoints with config:write:')
for method, name in matches:
    print(f'  {name} ({method})')

# Find endpoints with config:read
pattern2 = r'@requires_capability\("config:read"\)\s*\n\s*@app\.(get|post|put|delete|patch)\([^)]+\)\s*\n\s*def (\w+)'
matches2 = re.findall(pattern2, content)
print('\nEndpoints with config:read:')
for method, name in matches2:
    print(f'  {name} ({method})')
