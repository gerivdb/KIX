import yaml

with open('D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/runners.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f)

runners = data.get('runners', [])

# Find runners with missing working_dir or entrypoint
missing = []
for r in runners:
    name = r.get('name')
    rtype = r.get('runner_type')
    working_dir = r.get('working_dir')
    entrypoint = r.get('entrypoint')
    binary = r.get('binary')
    
    issues = []
    if not working_dir:
        issues.append('no working_dir')
    if not entrypoint and not binary and rtype not in ['custom']:
        issues.append('no entrypoint/binary')
    
    if issues:
        missing.append((name, rtype, issues))

print(f'Runners with configuration issues: {len(missing)}')
for name, rtype, issues in missing:
    issue_str = ' | '.join(issues)
    print(f'  {name} ({rtype}): {issue_str}')
