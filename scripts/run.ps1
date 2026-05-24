param(
    [switch]$SkipInstall,
    [switch]$SkipIngest
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Add-DockerBinToPathIfNeeded {
    $dockerBin = "C:\Program Files\Docker\Docker\resources\bin"

    if (-not (Test-Path $dockerBin)) {
        return
    }

    $pathParts = $env:PATH -split ";"
    if ($pathParts -notcontains $dockerBin) {
        $env:PATH = "$dockerBin;$env:PATH"
    }
}

function Wait-DockerEngine {
    param([int]$TimeoutSeconds = 120)

    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    while ($sw.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
        try {
            docker info *> $null
            return $true
        }
        catch {
            Start-Sleep -Seconds 2
        }
    }

    return $false
}

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

Write-Step "Preparando ambiente"
Add-DockerBinToPathIfNeeded

if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "Arquivo .env criado a partir de .env.example" -ForegroundColor Yellow
        Write-Host "Preencha as chaves no .env antes de executar novamente, se necessario." -ForegroundColor Yellow
    }
    else {
        throw "Arquivo .env nao encontrado e .env.example tambem nao existe."
    }
}

Write-Step "Validando Docker"
try {
    docker info *> $null
}
catch {
    $dockerDesktop = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerDesktop) {
        Write-Host "Docker Engine indisponivel. Tentando abrir Docker Desktop..." -ForegroundColor Yellow
        Start-Process $dockerDesktop

        if (-not (Wait-DockerEngine -TimeoutSeconds 120)) {
            throw "Docker nao ficou pronto em ate 120s. Abra o Docker Desktop e tente novamente."
        }
    }
    else {
        throw "Docker nao encontrado. Instale o Docker Desktop para continuar."
    }
}

Write-Step "Subindo Postgres + pgvector"
docker compose up -d

$pythonCandidates = @(
    (Join-Path $projectRoot ".venv\Scripts\python.exe"),
    (Join-Path (Split-Path -Parent $projectRoot) ".venv\Scripts\python.exe")
)

$pythonExe = $pythonCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $pythonExe) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonExe = $pythonCmd.Source
    }
    else {
        throw "Python nao encontrado. Ative/crie a venv antes de executar o script."
    }
}

if (-not $SkipInstall) {
    Write-Step "Instalando dependencias Python"
    & $pythonExe -m pip install -r requirements.txt
}

if (-not $SkipIngest) {
    Write-Step "Executando ingestao"
    & $pythonExe src/ingest.py
}

Write-Step "Iniciando chat"
& $pythonExe src/chat.py
