import os

files = [
    'D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/PRD-MOC/PRD-MOC-KIX-MULTI-LANG-ECOSYSTEM-2026-09-24.md',
    'D:/DO/WEB/TOOLS/L2-PLATFORM/KIX/PRD-MOC/PRD-MOC-KIX-EXE-ORCHESTRATION-2026-09-24.md',
]

for path in files:
    with open(path, encoding='utf-8') as f:
        content = f.read()
    
    filename = os.path.basename(path)
    
    # Find proof-of-life section regardless of section number
    markers = [
        '## 9. PROOF-OF-LIFE',
        '## 9. PREUVE-OF-LIFE',
        '## 8. PROOF-OF-LIFE',
        '## 8. PREUVE-OF-LIFE',
        '## PROOF-OF-LIFE',
        '## PREUVE-OF-LIFE',
    ]
    found = False
    for marker in markers:
        if marker in content:
            start = content.find(marker)
            end = content.find('\n## ', start + 1)
            if end == -1:
                end = len(content)
            section = content[start:end]
            print(f'{filename}:')
            print(section[:400])
            print('...')
            found = True
            break
    if not found:
        print(f'{filename}: No proof-of-life section found')
    print()
