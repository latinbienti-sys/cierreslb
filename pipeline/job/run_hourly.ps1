# Lanzador persistente del job horario "CierreLB Dashboard Horario".
# Vive FUERA de Temp (no lo borra el vaciado de Temp). El repo se auto-recupera
# con 'git clone' si su copia local en Temp desaparece.
$ErrorActionPreference = 'Continue'

$repo = 'C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb'
$py   = 'C:\Users\yarleyc\cierre-dashboard\venv\Scripts\python.exe'
$log  = 'C:\Users\yarleyc\cierre-dashboard\hourly.log'

function WLog($m) { "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $m" | Out-File -Append -Encoding utf8 $log }
function RunLog($cmd) { & $cmd 2>&1 | Out-File -Append -Encoding utf8 $log }

WLog "inicio (repo=$repo)"
try {
  if (-not (Test-Path -LiteralPath (Join-Path $repo '.git'))) {
    WLog "repo ausente: clonando..."
    RunLog { git clone https://github.com/latinbienti-sys/cierreslb.git $repo }
  }
  if (Test-Path -LiteralPath (Join-Path $repo '.git')) {
    Set-Location -LiteralPath $repo
    RunLog { git pull --rebase --autostash }
    RunLog { & $py -X utf8 (Join-Path $repo 'pipeline\update_hourly.py') }
    WLog "fin rc=$LASTEXITCODE"
  } else {
    WLog "ERROR: repo no disponible tras clonar"
  }
} catch {
  WLog "EXCEPCION: $($_.Exception.Message)"
}
