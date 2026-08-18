# PR Existence First

> **IntentHash**: `0xPR_EXISTENCE_FIRST_20260818`  
> **Version**: 1.0.0  
> **Domain**: foundational  
> **Type**: workflow  
> **Status**: active  

---

## Synopsis

Skill de vérification préalable d'existence de PR GitHub avant toute action (create / review / merge / resolve). Évite les recréations inutiles, les merges sur branches mortes et les pertes de temps sur des PR déjà intégrées.

---

## Triggers

- `créer PR`, `ouvrir PR`, `PR pour branche X`
- `review PR`, `merge PR`, `résoudre PR`
- `PR existe?`, `état de la PR`, `check PR`
- `feat/...`, `fix/...`, suivie d'une action Git avancée

---

## Prerequisites

- GitHub API accessible en BDCP (token via keyring ou `gh auth token`)
- `git` configuré avec le remote correct
- Connaissance de la branche source et du repo cible

---

## Workflow

### Step 1: Détecter la branche source

```powershell
git branch --show-current
```

### Step 2: Vérifier l'existence d'une PR via GitHub API

```powershell
$token = cmd /c "C:\gh\bin\gh.exe auth token" 2>&1 | Out-String
$token = $token.Trim()
$headers = @{
    Authorization = "Bearer $token"
    Accept = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
}
$resp = Invoke-RestMethod -Uri "https://api.github.com/repos/gerivdb/<REPO>/pulls?head=gerivdb:<BRANCH>&state=all" -Headers $headers -Method Get
```

### Step 3: Router selon le verdict

| Verdict | Action |
|---------|--------|
| `NO_PR` | Créer la PR via API |
| `OPEN` | Utiliser l'existante pour review/merge |
| `CLOSED_NOT_MERGED` | Bloquer — branche abandonnée |
| `MERGED` | Signaler intégré, vérifier main, supprimer branche locale si clean |

### Step 4: Avant merge, vérifier que main contient le code

```powershell
git diff main..<BRANCH>
# Si vide → la branche est morte, ne pas merger
```

---

## API Reference

### Créer une PR (si `NO_PR`)

```python
import requests, os

token = os.environ["GITHUB_TOKEN"]
headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}

resp = requests.post(
    "https://api.github.com/repos/gerivdb/KIX/pulls",
    headers=headers,
    json={
        "title": "feat(process-release-handles): add /process/release-handles route",
        "head": "feat/process-release-handles",
        "base": "main",
    },
)
print(resp.status_code, resp.json().get("html_url"))
```

### merger une PR (si `OPEN`)

```python
resp = requests.put(
    f"https://api.github.com/repos/gerivdb/KIX/pulls/{pr_number}/merge",
    headers=headers,
    json={"merge_method": "squash", "delete_branch": True},
)
print(resp.status_code, resp.json())
```

---

## Anti-patterns

- Créer une PR sans vérifier l'existence
- Supposer qu'une PR est ouverte parce que la branche existe localement
- Recréer une PR fermée sans analyser la raison de la fermeture
- Merger sans vérifier `git diff main..branch` au préalable

---

## Error Handling

| Erreur | Recovery |
|--------|----------|
| API 404 sur `/pulls` | Vérifier le repo et le nom de branche |
| PR `CLOSED` non mergée | Signaler, ne pas recréer, demander HITL |
| PR `MERGED` mais diff non vide | Vérifier si commit de merge = squash, comparer les arbres |
| Token absent | Demander authentification manuelle |

---

## Dependencies

- **Depends on**: `bdcp-github-api-fallback`, `git-remote-safety`
- **Provides to**: `kiva-pr-workflow`, `create-pull-request`

---

## Changelog

| Version | Date | Change | IntentHash |
|---------|------|--------|------------|
| 1.0.0 | 2026-08-18 | Création initiale | `0xPR_EXISTENCE_FIRST_20260818` |

---

## Reference ADR

- **ADR** : ADR-2026-08-08-002-AGENT-MANAGER-V99-CAPACITY
- **IntentHash** : `0xAGENT_MANAGER_V99_CAPACITY_20260818`
- **Dépôt** : gerivdb/GOVERNANCE-HUB
- **Statut ADR** : proposed
- **Màj requise si** : statut ADR passe à deprecated ou superseded
