import yaml

with open('D:/DO/WEB/TOOLS/L0-CANON/GOVERNANCE-HUB/known_repositories.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f)

repos = data.get('repos', [])
print(f'Total repos in SOT: {len(repos)}')

# Find all KIX-related repos
kix_keywords = ['kix', 'trix', 'flex', 'wazaa', 'gateway', 'bootstrap', 'runners', 'orchestrat', 'llux', 'rootx', 'timx', 'plix', 'jevx', 'rlm', 'kg-l', 'kg_l', 'kg-l-', 'kg_l_']
kix_ecosystem = []

for repo in repos:
    repo_name = repo.get('repo', '')
    desc = repo.get('description', '')
    
    # Check if repo is KIX-related
    is_kix = any(keyword in repo_name.lower() for keyword in kix_keywords)
    is_kix = is_kix or any(keyword in desc.lower() for keyword in ['kix', 'orchestrat', 'runner', 'trix', 'flex', 'wazaa'])
    
    if is_kix:
        kix_ecosystem.append({
            'repo': repo_name,
            'local_path': repo.get('local_path', 'N/A'),
            'status': repo.get('status', 'unknown'),
            'layer': repo.get('layer', 'N/A'),
            'owner': repo.get('owner', 'N/A'),
            'description': desc[:80] if desc else ''
        })

print(f'\nKIX ecosystem repos: {len(kix_ecosystem)}')
for repo in kix_ecosystem:
    print(f"  {repo['repo']}: {repo['local_path']} ({repo['status']}) - {repo['description']}")
