# Runbook — Relance manuelle du Bootstrap Runner

## Contexte

Le bootstrap runner est un service Python intégré à KIX qui orchestre le démarrage des services critiques de l'écosystème gerivdb.

**Port** : 8810  
**Service** : `bootstrap`  
**Localisation** : `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\services\bootstrap_runner.py`

## Procédure de relance manuelle

### Étape 1 — Vérifier l'état actuel

```powershell
# Vérifier KIX
Invoke-RestMethod -Uri "http://127.0.0.1:8800/health" -Method Get

# Vérifier bootstrap
Invoke-RestMethod -Uri "http://127.0.0.1:8810/health" -Method Get

# Vérifier le statut détaillé
Invoke-RestMethod -Uri "http://127.0.0.1:8810/bootstrap/status" -Method Get
```

### Étape 2 — Identifier la cause de l'échec

```powershell
# Vérifier les logs KIX
Get-Content "D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\logs\kix.log" -Tail 50

# Vérifier les logs bootstrap
Get-Content "D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\logs\bootstrap.log" -Tail 50

# Vérifier les blockers
$status = Invoke-RestMethod -Uri "http://127.0.0.1:8810/bootstrap/status" -Method Get
$status.blockers
```

### Étape 3 — Relancer le bootstrap

#### Option A — Via KIX (recommandé)

```powershell
# Redémarrer le runner bootstrap via KIX
Invoke-RestMethod -Uri "http://127.0.0.1:8800/runners/bootstrap/restart" -Method Post -Headers @{"Authorization"="Bearer <TOKEN>"}
```

#### Option B — Via PowerShell direct

```powershell
# Arrêter le processus bootstrap existant
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*bootstrap_runner*" } | Stop-Process -Force

# Redémarrer bootstrap
Start-Process python -ArgumentList @("D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\services\bootstrap_runner.py") -WorkingDirectory "D:\DO\WEB\TOOLS\L2-PLATFORM\KIX" -WindowStyle Hidden
```

#### Option C — Via ECOS CLI

```powershell
ecos security restart
# ou
Restart-Process -Name "python" -ArgumentList @("D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\services\bootstrap_runner.py")
```

### Étape 4 — Vérifier la relance

```powershell
# Attendre 5 secondes
Start-Sleep -Seconds 5

# Vérifier que bootstrap est prêt
$ready = Invoke-RestMethod -Uri "http://127.0.0.1:8810/bootstrap/ready" -Method Get
if ($ready.ready -eq $true) {
    Write-Host "[OK] Bootstrap prêt" -ForegroundColor Green
} else {
    Write-Host "[ERREUR] Bootstrap pas prêt: $($ready.blockers -join ', ')" -ForegroundColor Red
}
```

### Étape 5 — Vérifier les services dépendants

```powershell
# Vérifier que tous les services sont up
$status = Invoke-RestMethod -Uri "http://127.0.0.1:8810/bootstrap/status" -Method Get
$status.services | Format-Table -AutoSize
```

## Cas particuliers

### Cas 1 — KIX ne démarre pas

```powershell
# Vérifier les logs KIX
Get-Content "D:\DO\WEB\TOOLS\L2-PLATFORM\KIX\logs\kix.log" -Tail 100

# Redémarrer KIX
Get-Process -Name "python*" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*KIX*" } | Stop-Process -Force
Start-Sleep -Seconds 2
Start-Process python -ArgumentList @("-m","src.app") -WorkingDirectory "D:\DO\WEB\TOOLS\L2-PLATFORM\KIX" -WindowStyle Hidden
```

### Cas 2 — Arbiter ne démarre pas

```powershell
# Démarrer Arbiter manuellement
Start-Process powershell -ArgumentList @("-ExecutionPolicy","Bypass","-File","D:\DO\WEB\TOOLS\L4-TOOLS\TRIX\start-git-arbiter.ps1") -WindowStyle Hidden

# Vérifier
Invoke-RestMethod -Uri "http://127.0.0.1:8742/health" -Method Get
```

### Cas 3 — SecretResolver échoue

```powershell
# Vérifier les variables d'environnement
$env:TRIX_DAEMON_TOKEN

# Vérifier le keyring
python -c "import keyring; print(keyring.get_password('gerivdb', 'trix_daemon_token'))"

# Si le secret est absent, le définir
[System.Environment]::SetEnvironmentVariable("TRIX_DAEMON_TOKEN", "<token>", "User")
```

## Contacts

- **KIX** : `D:\DO\WEB\TOOLS\L2-PLATFORM\KIX`
- **GOVERNANCE-HUB** : `D:\DO\WEB\TOOLS\L0-CANON\GOVERNANCE-HUB`
- **PRD** : `PRD/PRD-MOC-BOOTSTRAP-RUNNER-GOVERNANCE-2026-08-20.md`
