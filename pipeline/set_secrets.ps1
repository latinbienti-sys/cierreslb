# -*- powershell -*-
# Crea/actualiza en GitHub los secretos que usa el workflow horario,
# tomandolos del config.json local de Odoo. NO imprime los valores.
#
# Uso (una sola vez, despues de autenticar gh):
#   gh auth login --hostname github.com
#   powershell -ExecutionPolicy Bypass -File pipeline\set_secrets.ps1
$ErrorActionPreference = "Stop"
$repo = "latinbienti-sys/cierreslb"

gh auth status 1>$null 2>$null
if ($LASTEXITCODE -ne 0) { throw "gh no esta autenticado. Ejecuta primero: gh auth login" }

$cfgPath = Join-Path $env:USERPROFILE "Desktop\crmlatinbien\config.json"
if (-not (Test-Path $cfgPath)) { throw "No se encontro $cfgPath" }
$odoo = (Get-Content -Raw $cfgPath -Encoding utf8 | ConvertFrom-Json).odoo
if (-not $odoo.url -or -not $odoo.db -or -not $odoo.user -or -not $odoo.api_key) {
    throw "config.json incompleto (url/db/user/api_key)."
}

$secrets = [ordered]@{
    ODOO_URL     = [string]$odoo.url
    ODOO_DB      = [string]$odoo.db
    ODOO_USER    = [string]$odoo.user
    ODOO_API_KEY = [string]$odoo.api_key
}
foreach ($k in $secrets.Keys) {
    gh secret set $k --repo $repo --body $secrets[$k] 1>$null
    if ($LASTEXITCODE -ne 0) { throw "fallo al crear el secreto $k" }
    Write-Host "secreto $k listo"
}
Write-Host "Secretos de Actions configurados para $repo (solo lectura de Odoo)."
