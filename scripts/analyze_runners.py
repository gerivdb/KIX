import yaml

with open('D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/runners.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f)

runners = data.get('runners', [])
print(f'Total runners in runners.yaml: {len(runners)}')

# Group by type
types = {}
for r in runners:
    t = r.get('runner_type', 'unknown')
    types[t] = types.get(t, 0) + 1

print('\nBy type:')
for t, count in sorted(types.items()):
    print(f'  {t}: {count}')

# List all runner names
print('\nAll runners:')
for r in runners:
    name = r.get('name')
    rtype = r.get('runner_type')
    print(f'  {name} ({rtype})')
