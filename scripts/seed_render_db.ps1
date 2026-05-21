# Carga usuarios de prueba en PostgreSQL de Render SIN usar Shell.
# Uso: copie "External Database URL" desde Render → consultamed-db → Connect.
#
#   .\scripts\seed_render_db.ps1 "postgres://usuario:pass@host:5432/consultamed"
#
# O en PowerShell:
#   $env:DATABASE_URL = "postgres://..."
#   .\scripts\seed_render_db.ps1

param(
    [Parameter(Position = 0)]
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [switch]$NoForce
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not $DatabaseUrl) {
    Write-Host @"

Falta DATABASE_URL (URL externa de PostgreSQL en Render).

1. Render Dashboard → consultamed-db → Connect / Connection
2. Copie **External Database URL**
3. Ejecute:

   .\scripts\seed_render_db.ps1 "PEGUE_LA_URL_AQUI"

"@ -ForegroundColor Yellow
    exit 1
}

$env:DATABASE_URL = $DatabaseUrl
$env:DJANGO_DEBUG = "True"
if (-not $env:DJANGO_ALLOWED_HOSTS) { $env:DJANGO_ALLOWED_HOSTS = "127.0.0.1,localhost" }
if (-not $env:DJANGO_SECRET_KEY) { $env:DJANGO_SECRET_KEY = "solo-para-comando-local-seed" }

$seedArgs = if ($NoForce) { @() } else { @("--force") }
Write-Host "Conectando a la BD de Render y ejecutando seed_demo $($seedArgs -join ' ')..." -ForegroundColor Cyan
python manage.py seed_demo @seedArgs
Write-Host ""
Write-Host "Listo. Use las cuentas de CREDENCIALES_PRUEBA.txt en:" -ForegroundColor Green
Write-Host "  https://consultamed.onrender.com/cuentas/iniciar-sesion/" -ForegroundColor Green
