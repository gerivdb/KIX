import os

files = [
    'D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/PRD-MOC/PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md',
    'D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/PRD-MOC/PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md',
]

for path in files:
    with open(path, encoding='utf-8') as f:
        content = f.read()
    
    filename = os.path.basename(path)
    
    # Find proof-of-life section
    if '## 9. PROOF-OF-LIFE' in content:
        start = content.find('## 9. PROOF-OF-LIFE')
        end = content.find('## 10.', start)
        if end == -1:
            end = len(content)
        section = content[start:end]
        print(f'{filename}:')
        print(section[:400])
        print('...')
    elif '## 9. PREUVE-OF-LIFE' in content:
        start = content.find('## 9. PREUVE-OF-LIFE')
        end = content.find('## 10.', start)
        if end == -1:
            end = len(content)
        section = content[start:end]
        print(f'{filename}:')
        print(section[:400])
        print('...')
    else:
        print(f'{filename}: No proof-of-life section found')
    print()
