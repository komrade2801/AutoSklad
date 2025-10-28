<#
.SYNOPSIS
    Starts AutoSklad server and/or client applications in separate PowerShell terminals

.DESCRIPTION
    Launches server, client, or both in new PowerShell windows.
    Each app runs with proper environment setup using PowerShell syntax.

.PARAMETER Components
    Components to start: 'client', 'server', or 'both' (default: both)

.PARAMETER Mocks
    Enable mock mode for client ($env:AUTOSKLAD_USE_MOCKS = '1')

.EXAMPLE
    # Start both server and client
    .\start_apps.ps1

    # Start only server
    .\start_apps.ps1 -Components server

    # Start client with mocks enabled
    .\start_apps.ps1 -Components client -Mocks
#>

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('client', 'server', 'both')]
    [string]$Components = 'both',

    [Parameter(Mandatory = $false)]
    [switch]$Mocks
)

function Write-ErrorMessage {
    param([string]$Message)
    Write-Host "ERROR: $Message" -ForegroundColor Red
}

function Write-SuccessMessage {
    param([string]$Message)
    Write-Host "SUCCESS: $Message" -ForegroundColor Green
}

function Write-InfoMessage {
    param([string]$Message)
    Write-Host "INFO: $Message" -ForegroundColor Cyan
}

function Write-WarningMessage {
    param([string]$Message)
    Write-Host "WARNING: $Message" -ForegroundColor Yellow
}

# Determine components to process
$componentsList = @()
if ($Components -eq 'both') {
    $componentsList = @('server', 'client')  # Start server first
} else {
    $componentsList = @($Components)
}

Write-InfoMessage ""
Write-InfoMessage "AutoSklad Application Startup Script"
Write-InfoMessage "====================================="
Write-InfoMessage "Components to start: $($componentsList -join ', ')"
if ($Mocks) {
    Write-InfoMessage "Client mock mode: Enabled"
}
Write-InfoMessage ""

# Check if directories and venvs exist
$missingItems = @()
foreach ($comp in $componentsList) {
    if (-not (Test-Path $comp)) {
        $missingItems += "$comp directory"
    } elseif (-not (Test-Path "$comp/venv")) {
        $missingItems += "$comp/venv"
    }
}

if ($missingItems.Count -gt 0) {
    Write-ErrorMessage "Missing required items: $($missingItems -join ', ')"
    Write-ErrorMessage "Please run .\scripts\venv_setup.ps1 first to create virtual environments."
    exit 1
}

# Show what will be done
Write-InfoMessage "Actions to perform:"
foreach ($comp in $componentsList) {
    Write-Host "  - Start $comp in new PowerShell window" -ForegroundColor Yellow
}
if ($Mocks -and $componentsList -contains 'client') {
    Write-Host "  - Enable mock mode for client" -ForegroundColor Yellow
}
Write-InfoMessage ""

$confirmation = Read-Host "Do you want to start the applications? (y/N)"
if ($confirmation -ne "y" -and $confirmation -ne "Y") {
    Write-InfoMessage "Operation cancelled."
    exit 0
}

Write-InfoMessage "Starting applications..."
Write-InfoMessage ""

$startedCount = 0

foreach ($comp in $componentsList) {
    Write-InfoMessage "Starting $comp..."

    $compPath = Join-Path $PWD $comp

    # Build PowerShell command as a script block
    $psCommand = @"
cd '$compPath'
& .\venv\Scripts\Activate.ps1
"@

    if ($comp -eq 'client' -and $Mocks) {
        $psCommand += @"

`$env:AUTOSKLAD_USE_MOCKS = '1'
"@
    }

    $psCommand += @"

& python main.py
"@

    try {
        # Start in new PowerShell window
        Start-Process -FilePath "powershell.exe" -ArgumentList "-NoExit", "-Command `"$psCommand`""
        Write-SuccessMessage "$comp started successfully in new PowerShell window"
        $startedCount++
    } catch {
        Write-ErrorMessage "Failed to start $comp - $($_.Exception.Message)"
    }

    # Small delay between starts
    Start-Sleep -Seconds 2
}

Write-InfoMessage ""
Write-InfoMessage "Startup Summary:"
Write-InfoMessage "- Applications started: $startedCount"

if ($startedCount -eq $componentsList.Count) {
    Write-SuccessMessage "All applications started successfully!"
    Write-InfoMessage "Check the new PowerShell windows for application output."
} else {
    Write-WarningMessage "Some applications failed to start. Check the output above for details."
}
