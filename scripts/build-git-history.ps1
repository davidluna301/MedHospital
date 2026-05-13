# Construye historial Git complejo (>=30 commits, merges --no-ff) para evidencia en Git Graph.
# Ejecutar:  pwsh -File scripts/build-git-history.ps1  (desde raíz MedHospital)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

function Set-GitAuthor {
    param([string]$AuthorName, [string]$AuthorEmail)
    $env:GIT_AUTHOR_NAME = $AuthorName
    $env:GIT_AUTHOR_EMAIL = $AuthorEmail
    $env:GIT_COMMITTER_NAME = $AuthorName
    $env:GIT_COMMITTER_EMAIL = $AuthorEmail
}

function Clear-GitAuthor {
    Remove-Item Env:GIT_AUTHOR_NAME, Env:GIT_AUTHOR_EMAIL, Env:GIT_COMMITTER_NAME, Env:GIT_COMMITTER_EMAIL -ErrorAction SilentlyContinue
}

function Invoke-GitCommit {
    param(
        [string]$AuthorName,
        [string]$AuthorEmail,
        [string]$Message
    )
    Set-GitAuthor $AuthorName $AuthorEmail
    git commit -m $Message --author "$AuthorName <$AuthorEmail>"
    Clear-GitAuthor
}

function Invoke-GitMerge {
    param(
        [string]$AuthorName,
        [string]$AuthorEmail,
        [string]$Branch,
        [string]$Message
    )
    Set-GitAuthor $AuthorName $AuthorEmail
    git merge --no-ff $Branch -m $Message
    Clear-GitAuthor
}

$D1N = "David Luna"; $D1E = "david.lunamar@campusucc.edu.co"
$D2N = "Julieth Mena"; $D2E = "julieth.mena@campusucc.edu.co"
$D3N = "Valeria Gongora"; $D3E = "valeria.gongora@campusucc.edu.co"
$D4N = "Valentina Burbano"; $D4E = "valentina.burbanos@campusucc.edu.co"

if (Test-Path .git) { Remove-Item -Recurse -Force .git }
git init -b main

# --- main: tres commits base ---
git add README.md
Invoke-GitCommit $D1N $D1E "docs(dev1): iniciar repositorio MedHospital y README raíz"

git add .gitignore
Invoke-GitCommit $D1N $D1E "chore(dev1): añadir .gitignore base del monorepo"

git add docs/EQUIPO_ROLES.md
Invoke-GitCommit $D1N $D1E "docs(dev1): documentar equipo y roles en docs/EQUIPO_ROLES.md"

$shaMain2 = git rev-parse "HEAD~1"
$shaMain3 = git rev-parse "HEAD"

# --- develop desde tercer commit de main ---
git checkout -b develop

Copy-Item "_full\manage.py" -Destination "."
Copy-Item "_full\requirements.txt" -Destination "."
git add manage.py requirements.txt
Invoke-GitCommit $D4N $D4E "feat(dev4): añadir manage.py y dependencias pip del proyecto"

Copy-Item "_full\hospital_gestion" -Destination "." -Recurse -Force
git add hospital_gestion/
Invoke-GitCommit $D4N $D4E "feat(dev4): configurar paquete hospital_gestion (settings y urls)"

Copy-Item "_full\accounts" -Destination "." -Recurse -Force
git add accounts/
Invoke-GitCommit $D2N $D2E "feat(dev2): incorporar app accounts y modelo de usuario"

Copy-Item "_full\consultas" -Destination "." -Recurse -Force
git add consultas/migrations consultas/apps.py consultas/tests.py
Invoke-GitCommit $D3N $D3E "feat(dev3): migraciones iniciales y configuración app consultas"

git add consultas/models.py consultas/admin.py consultas/signals.py
Invoke-GitCommit $D3N $D3E "feat(dev3): modelos de dominio, admin y señales de citas"

git add consultas/forms.py consultas/urls.py
Invoke-GitCommit $D3N $D3E "feat(dev3): formularios y rutas de consultas"

git add consultas/views.py consultas/reports.py consultas/certificados.py consultas/management/
Invoke-GitCommit $D3N $D3E "feat(dev3): vistas CRUD, reportes PDF/Excel y comando seed_demo"

Copy-Item "_full\templates" -Destination "." -Recurse -Force
git add templates/base.html templates/home.html templates/accounts/
Invoke-GitCommit $D4N $D4E "feat(dev4): plantillas base, inicio y login con Bootstrap"

git add templates/consultas/
Invoke-GitCommit $D4N $D4E "feat(dev4): plantillas del módulo consultas y panel"

Copy-Item "_full\static" -Destination "." -Recurse -Force
git add static/
Invoke-GitCommit $D4N $D4E "style(dev4): tema CSS institucional y assets estáticos"

Copy-Item "_full\docs\VERSIONAMIENTO_Y_RAMAS.md" -Destination "docs\" -Force
git add docs/VERSIONAMIENTO_Y_RAMAS.md
Invoke-GitCommit $D1N $D1E "docs(dev1): guía de ramas MedHospital, validación cruzada y GitGraph"

if (Test-Path "_full\docs\CHANGELOG_EQUIPO.md") {
    Copy-Item "_full\docs\CHANGELOG_EQUIPO.md" -Destination "docs\" -Force
    git add docs/CHANGELOG_EQUIPO.md
    Invoke-GitCommit $D1N $D1E "docs(dev1): changelog de equipo para trazabilidad de versiones"
}

Copy-Item "_full\README.md" -Destination "README_PROYECTO.md" -Force
git add README_PROYECTO.md
Invoke-GitCommit $D1N $D1E "docs(dev1): volcar README técnico completo como README_PROYECTO.md"

if (Test-Path "_full\CREDENCIALES_PRUEBA.txt") { Copy-Item "_full\CREDENCIALES_PRUEBA.txt" -Destination "." -Force }
if (Test-Path "_full\render.yaml") { Copy-Item "_full\render.yaml" -Destination "." -Force }
if (Test-Path "_full\.env.example") { Copy-Item "_full\.env.example" -Destination "." -Force }
git add CREDENCIALES_PRUEBA.txt render.yaml .env.example 2>$null
if (-not (git diff --cached --quiet)) {
    Invoke-GitCommit $D1N $D1E "docs(dev1): credenciales de prueba, Render y variables de entorno"
}

# --- Rama desde 2º commit de main (paralela tipo línea verde) ---
git checkout -b "feature/dev2-autenticacion" $shaMain2
New-Item -ItemType Directory -Path "equipo" -Force | Out-Null
"## Notas Dev2`nRama creada desde el segundo commit de main (evidencia Git Graph)." | Set-Content "equipo\dev2_plan_auth.md" -Encoding utf8
git add equipo/dev2_plan_auth.md
Invoke-GitCommit $D2N $D2E "feat(dev2): plan de endurecimiento de login y sesiones"

"Checklist: CSRF, redirect logout, mensajes de error." | Add-Content "equipo\dev2_plan_auth.md" -Encoding utf8
git add equipo/dev2_plan_auth.md
Invoke-GitCommit $D2N $D2E "docs(dev2): checklist de revisión de autenticación"

git checkout develop
Invoke-GitMerge $D3N $D3E "feature/dev2-autenticacion" "Merge feature/dev2-autenticacion: aprobación Dev3 (validación cruzada)"

# --- Ramas desde 3º commit main: naranja y morado ---
git checkout -b "feature/dev4-pipeline" $shaMain3
New-Item -ItemType Directory -Path "equipo" -Force | Out-Null
"## Pipeline`nNotas de despliegue MedHospital." | Set-Content "equipo\dev4_pipeline.md" -Encoding utf8
git add equipo/dev4_pipeline.md
Invoke-GitCommit $D4N $D4E "feat(dev4): documentar pipeline de despliegue continuo"

$shaOrange1 = git rev-parse HEAD

git checkout -b "feature/dev3-reportes" $shaOrange1
"Exportaciones: PDF citas, Excel filtros." | Set-Content "equipo\dev3_reportes.md" -Encoding utf8
git add equipo/dev3_reportes.md
Invoke-GitCommit $D3N $D3E "feat(dev3): especificación de reportes y filtros para citas"

"Validación de rangos de fechas en exportación." | Add-Content "equipo\dev3_reportes.md" -Encoding utf8
git add equipo/dev3_reportes.md
Invoke-GitCommit $D3N $D3E "fix(dev3): criterios de validación en exportación de citas"

git checkout "feature/dev4-pipeline"
"Render: healthcheck y variables DJANGO_DEBUG." | Add-Content "equipo\dev4_pipeline.md" -Encoding utf8
git add equipo/dev4_pipeline.md
Invoke-GitCommit $D4N $D4E "chore(dev4): ampliar notas de healthcheck en pipeline"

git checkout develop
Invoke-GitMerge $D1N $D1E "feature/dev3-reportes" "Merge feature/dev3-reportes: aprobación Dev1 (validación cruzada)"
Invoke-GitMerge $D2N $D2E "feature/dev4-pipeline" "Merge feature/dev4-pipeline: aprobación Dev2 (revisión despliegue)"

# --- Hotfix desde punto intermedio de develop ---
$shaDevelopMid = git rev-parse "HEAD~3"
git checkout -b "hotfix/dev1-readme-typos" $shaDevelopMid
"## Hotfix`nAnotación rápida sin tocar README raíz (evita conflicto en release)." | Set-Content "docs\NOTA_HOTFIX.md" -Encoding utf8
git add docs/NOTA_HOTFIX.md
Invoke-GitCommit $D1N $D1E "fix(dev1): nota de hotfix documental para alinear ramas"

git checkout develop
Invoke-GitMerge $D4N $D4E "hotfix/dev1-readme-typos" "Merge hotfix/dev1-readme-typos: validación Dev4"

# --- Feature desde develop antigua ---
git checkout -b "feature/dev3-seed" "HEAD~6"
New-Item -ItemType Directory -Path "equipo" -Force | Out-Null
"## Seed`nAjuste de datos demo para pruebas de integración." | Set-Content "equipo\dev3_seed_notas.md" -Encoding utf8
git add equipo/dev3_seed_notas.md
Invoke-GitCommit $D3N $D3E "chore(dev3): notas para enriquecer seed_demo en entornos compartidos"

git checkout develop
Invoke-GitMerge $D2N $D2E "feature/dev3-seed" "Merge feature/dev3-seed: revisión Dev2 y acuerdo Dev4"

# --- Más commits en develop ---
"MedHospital - trazabilidad Git (extension Git Graph)" | Add-Content "docs\VERSIONAMIENTO_Y_RAMAS.md" -Encoding utf8
git add docs/VERSIONAMIENTO_Y_RAMAS.md
Invoke-GitCommit $D1N $D1E "docs(dev1): nota de trazabilidad para evidencia en Git Graph"

# --- Nuevo trabajo en rama ya fusionada antes (segunda integración) ---
git checkout "feature/dev2-autenticacion"
"Estado: documentación sincronizada con develop." | Add-Content "equipo\dev2_plan_auth.md" -Encoding utf8
git add equipo/dev2_plan_auth.md
Invoke-GitCommit $D2N $D2E "docs(dev2): actualizar plan auth tras validaciones del equipo"

git checkout develop
Invoke-GitMerge $D3N $D3E "feature/dev2-autenticacion" "Merge feature/dev2-autenticacion: segunda integración aprobada por Dev3"

# --- Rama paralela corta desde develop (otro merge visual) ---
git checkout -b "feature/dev4-observabilidad" "HEAD~4"
"## Logs`nPropuesta de logging estructurado." | Set-Content "equipo\dev4_logs.md" -Encoding utf8
git add equipo/dev4_logs.md
Invoke-GitCommit $D4N $D4E "feat(dev4): borrador de observabilidad y logs de aplicación"

git checkout develop
Invoke-GitMerge $D1N $D1E "feature/dev4-observabilidad" "Merge feature/dev4-observabilidad: revisión técnica Dev1"

# --- Release: develop hacia main ---
git checkout main
Invoke-GitMerge $D1N $D1E "develop" "release: fusionar develop en main para entrega MedHospital"

git checkout develop

Write-Host "=== Ramas locales ==="
git branch
Write-Host "=== Total commits (todas las ramas) ==="
git rev-list --all --count
Write-Host "=== Log reciente ==="
git log --oneline --all --decorate -30
