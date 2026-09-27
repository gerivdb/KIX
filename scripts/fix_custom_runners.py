import yaml

with open('D:/DO/WEB/TOOLS/L0-CANON/GOVERNANCE-HUB/known_repositories.yaml', encoding='utf-8') as f:
    sot = yaml.safe_load(f)

sot_repos = {}
for repo in sot.get('repos', []):
    name = repo.get('repo', '').replace('gerivdb/', '')
    sot_repos[name.lower()] = repo.get('local_path')

with open('D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/runners.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f)

runners = data.get('runners', [])
updated = 0

for r in runners:
    name = r.get('name')
    rtype = r.get('runner_type')
    
    if rtype == 'custom' and not r.get('working_dir'):
        # Try to find matching repo
        repo_name = name.replace('-', '').lower()
        if repo_name in sot_repos:
            r['working_dir'] = sot_repos[repo_name]
            updated += 1
            print(f'  {name}: {sot_repos[repo_name]}')
        elif name in sot_repos:
            r['working_dir'] = sot_repos[name]
            updated += 1
            print(f'  {name}: {sot_repos[name]}')

print(f'\nUpdated {updated} custom runners with working_dir')

with open('D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/runners.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print('runners.yaml saved')
