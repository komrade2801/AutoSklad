<#
.SYNOPSIS
    Sets up virtual environments for AutoSklad client and/or server

.DESCRIPTION
    Deletes and recreates virtual environments, then installs requirements.
    Can target client, server, or both.

.PARAMETER Components
    Components to setup: 'client', 'server', or 'both' (default: both)

.PARAMETER Force
    Skip confirmation prompts

.EXAMPLE
    # Setup both client and server
    .\venv_setup.ps1

    # Setup only client
    .\venv_setup.ps1 -Components client

    # Force setup without confirmation
    .\venv_setup.ps1 -Force
#>

param(
    [Parameter(Mandatory = $false)]
    [ValidateSet('client', 'server', 'both')]
    [string]$Components = 'both',

    [Parameter(Mandatory = $false)]
    [switch]$Force
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
    $componentsList = @('client', 'server')
} else {
    $componentsList = @($Components)
}

Write-InfoMessage ""
Write-InfoMessage "AutoSklad Virtual Environment Setup Script"
Write-InfoMessage "=========================================="
Write-InfoMessage "Components to setup: $($componentsList -join ', ')"
Write-InfoMessage ""

# Check if directories exist
$missingDirs = @()
foreach ($comp in $componentsList) {
    if (-not (Test-Path $comp)) {
        $missingDirs += $comp
    }
}

if ($missingDirs.Count -gt 0) {
    Write-ErrorMessage "Missing directories: $($missingDirs -join ', ')"
    Write-ErrorMessage "Please run this script from the AutoSklad project root directory."
    exit 1
}

# Show what will be done
Write-InfoMessage "Actions to perform:"
foreach ($comp in $componentsList) {
    Write-Host "  - Delete and recreate venv in $comp/" -ForegroundColor Yellow
    Write-Host "  - Install requirements from $comp/requirements.txt" -ForegroundColor Yellow
}
Write-InfoMessage ""

# Ask for confirmation unless forced
if (-not $Force) {
    $confirmation = Read-Host "Do you want to proceed? This will delete existing virtual environments. (y/N)"
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-InfoMessage "Operation cancelled."
        exit 0
    }
}

Write-InfoMessage "Starting virtual environment setup..."
Write-InfoMessage ""

$successCount = 0
$failCount = 0

foreach ($comp in $componentsList) {
    Write-InfoMessage "Processing $comp..."
    $compPath = Join-Path $PWD $comp

    try {
        # Change to component directory
        Push-Location $compPath

        # Remove existing venv if it exists
        if (Test-Path "venv") {
            Write-InfoMessage "Removing existing venv..."
            Remove-Item -Recurse -Force "venv" -ErrorAction Stop
        }

        # Create new venv
        Write-InfoMessage "Creating virtual environment..."
        & python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create virtual environment"
        }

        # Activate venv and upgrade pip
        Write-InfoMessage "Activating venv and upgrading pip..."
        & .\venv\Scripts\Activate.ps1
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to activate virtual environment"
        }

        & python -m pip install --upgrade pip wheel
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to upgrade pip"
        }

        # Install requirements
        if (Test-Path "requirements.txt") {
            Write-InfoMessage "Installing requirements..."
            & pip install -r requirements.txt
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to install requirements"
            }
        } else {
            Write-WarningMessage "requirements.txt not found in $comp/, skipping installation"
        }

        Write-SuccessMessage "$comp setup completed successfully"
        $successCount++

    } catch {
        Write-ErrorMessage "Failed to setup $comp - $($_.Exception.Message)"
        $failCount++
    } finally {
        # Return to original directory
        Pop-Location
    }

    Write-InfoMessage ""
}

# Summary
Write-InfoMessage "Setup Summary:"
Write-InfoMessage "- Successfully setup: $successCount"
Write-InfoMessage "- Failed: $failCount"

if ($failCount -eq 0) {
    Write-SuccessMessage "All components setup successfully!"
} else {
    Write-WarningMessage "Some components failed to setup. Check the output above for details."
}
