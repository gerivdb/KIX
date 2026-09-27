"""Fix configuration gaps in runners.yaml for active KIX runners."""
import yaml

# Known repo mappings from known_repositories.yaml
REPO_PATHS = {
    'kix': 'D:/DO/WEB/TOOLS/L2-PLATFORM/KIX',
    'bootstrap': 'D:/DO/WEB/TOOLS/L2-PLATFORM/KIX',
    'gateway-manager': 'D:/DO/WEB/TOOLS/L1-INFRA/GATEWAY-MANAGER',
    'trixd': 'D:/DO/WEB/TOOLS/L4-TOOLS/TRIX',
    'wazaa': 'D:/DO/WEB/TOOLS/L4-TOOLS/WAZAA',
    'flex-api': 'D:/DO/WEB/TOOLS/L4-TOOLS/FLEX',
    'kg-l': 'D:/DO/WEB/TOOLS/L4-TOOLS/KG-L',
    'jevx': 'D:/DO/WEB/TOOLS/L4-TOOLS/JEVX',
    'flex-rust': 'D:/DO/WEB/TOOLS/L4-TOOLS/FLEX',
    'go-service': 'D:/DO/WEB/TOOLS/L4-TOOLS/GO-SERVICE',
    'node-service': 'D:/DO/WEB/TOOLS/L4-TOOLS/NODE-SERVICE',
    'batmcp': 'D:/DO/WEB/TOOLS/L4-TOOLS/BAT-MCP',
    'llm-gateway': 'D:/DO/WEB/TOOLS/L1-INFRA/ECOS-CLI',
    'agent-manager': 'D:/DO/WEB/TOOLS/L1-INFRA/AGENT-MANAGER',
    'nexus': 'D:/DO/WEB/TOOLS/L1-INFRA/NEXUS',
    'anamorphoser': 'D:/DO/WEB/TOOLS/L0-CANON/VOLTX',
    'tlm-lang': 'D:/DO/WEB/TOOLS/L0-CANON/unified-design/designs/tlm-lang',
    'kix-ecosystem': 'D:/DO/WEB/TOOLS/L2-PLATFORM/KIX',
    'rlm-metrics': 'D:/DO/WEB/TOOLS/L2-PLATFORM/KIX',
    'rlm-config': 'D:/DO/WEB/TOOLS/L2-PLATFORM/RLM-CONFIG',
    'rlm-deploy': 'D:/DO/WEB/TOOLS/L2-PLATFORM/RLM-DEPLOY',
    'rlm-graph': 'D:/DO/WEB/TOOLS/L2-PLATFORM/RLM-GRAPH',
    'rlm-secure': 'D:/DO/WEB/TOOLS/L2-PLATFORM/RLM-SECURE',
    'rlm-incident': 'D:/DO/WEB/TOOLS/L2-PLATFORM/RLM-INCIDENT',
    'rlm-release': 'D:/DO/WEB/TOOLS/L2-PLATFORM/RLM-RELEASE',
    'kg-l-coherence-watchdog': 'D:/DO/WEB/TOOLS/L4-TOOLS/KG-L',
    'nodex': 'D:/DO/WEB/TOOLS/L4-TOOLS/TALEX',
    'rootx': 'D:/DO/WEB/TOOLS/L4-TOOLS/ROOTX',
    'talex': 'D:/DO/WEB/TOOLS/L4-TOOLS/TALEX',
    'friction-analyzer': 'D:/DO/WEB/TOOLS/L2-PLATFORM/RLM-MDU',
    'wazaa-bus': 'D:/DO/WEB/TOOLS/L4-TOOLS/WAZAA',
}

# Known entrypoints
ENTRYPOINTS = {
    'kix': 'src/app.py',
    'bootstrap': 'services/bootstrap_runner.py',
    'gateway-manager': 'gateway-manager.exe',
    'trixd': 'trix.exe',
    'wazaa': '-m wazaa.wazaa_server',
    'flex-api': 'flex_api.py',
    'kg-l': 'src/kg_l_server.py',
    'jevx': 'server.js',
    'flex-rust': 'flex-rust.exe',
    'go-service': 'go-service.exe',
    'node-service': 'node-service.exe',
    'batmcp': 'batmcp.exe',
    'llm-gateway': 'gateway-manager.exe',
    'agent-manager': 'agent-manager.exe',
    'nexus': 'nexus.exe',
    'anamorphoser': 'anamorphoser.py',
    'tlm-lang': 'tlm_lang.py',
    'kix-ecosystem': 'services/ecosystem_integration.py',
    'rlm-metrics': 'services/metrics_service.py',
    'rlm-config': 'services/config_service.py',
    'rlm-deploy': 'services/deploy_service.py',
    'rlm-graph': 'services/graph_service.py',
    'rlm-secure': 'services/secure_service.py',
    'rlm-incident': 'services/incident_service.py',
    'rlm-release': 'services/release_service.py',
    'kg-l-coherence-watchdog': 'services/coherence_watchdog.py',
    'nodex': 'services/nodex_service.py',
    'rootx': 'services/rootx_service.py',
    'talex': 'services/talex_service.py',
    'friction-analyzer': 'services/friction_analyzer.py',
    'wazaa-bus': 'wazaa_bus.py',
}

with open('D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/runners.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f)

runners = data.get('runners', [])
updated = 0

for r in runners:
    name = r.get('name')
    
    # Fix working_dir
    if not r.get('working_dir') and name in REPO_PATHS:
        r['working_dir'] = REPO_PATHS[name]
        updated += 1
    
    # Fix entrypoint/binary
    if not r.get('entrypoint') and not r.get('binary'):
        rtype = r.get('runner_type')
        if rtype == 'gateway-exe' and name in ENTRYPOINTS:
            r['binary'] = ENTRYPOINTS[name]
            updated += 1
        elif name in ENTRYPOINTS:
            r['entrypoint'] = ENTRYPOINTS[name]
            updated += 1

print(f'Updated {updated} runner configurations')

with open('D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/config/runners.yaml', 'w', encoding='utf-8') as f:
    yaml.dump(data, f, default_flow_style=False, sort_keys=False)

print('runners.yaml saved')
