<#
.SYNOPSIS
    Cleans up database and command queue files from AutoSklad project

.DESCRIPTION
    Deletes all database files and command queue JSON files from both
    client and server directories, regardless of absolute project path.

.PARAMETER ProjectRoot
    Absolute path to AutoSklad project root (optional, auto-detects if not provided)

.PARAMETER Force
    Force deletion without confirmation

.EXAMPLE
    # Run from AutoSklad directory - auto-detects path
    .\cleanup_databases.ps1

    # Run from anywhere with explicit path
    .\cleanup_databases.ps1 -ProjectRoot "C:\Projects\AutoSklad"

    # Skip confirmation prompts
    .\cleanup_databases.ps1 -Force
#>

param(
    [Parameter(Mandatory = $false)]
    [string]$ProjectRoot,

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

# 1. Find project root
if (-not $ProjectRoot) {
    try {
        # Try to find project root using git
        $ProjectRoot = & git rev-parse --show-toplevel 2>$null
        if ($LASTEXITCODE -eq 0 -and $ProjectRoot) {
            Write-InfoMessage "Found project root via git: $ProjectRoot"
        }
        else {
            throw "Git command failed"
        }
    }
    catch {
        # Fallback: Search for .git directory walking up
        Write-WarningMessage "Git not available or not in repository, searching manually..."
        $currentPath = Get-Location

        while ($currentPath -and $currentPath.Path -ne $currentPath.Root) {
            if (Test-Path (Join-Path $currentPath ".git")) {
                $ProjectRoot = $currentPath.Path
                Write-InfoMessage "Found project root via .git search: $ProjectRoot"
                break
            }
            $currentPath = Split-Path $currentPath -Parent
        }

        if (-not $ProjectRoot) {
            Write-ErrorMessage "Could not find AutoSklad project root. Please provide -ProjectRoot parameter."
            exit 1
        }
    }
}

# Verify project root exists and looks like AutoSklad
if (-not (Test-Path $ProjectRoot)) {
    Write-ErrorMessage "Project root path does not exist: $ProjectRoot"
    exit 1
}

if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
    Write-WarningMessage "Project root doesn't appear to be a git repository: $ProjectRoot"
    Write-WarningMessage "Proceeding anyway, but please verify this is the correct AutoSklad directory."
}

# Define files to delete (relative to project root)
$filesToDelete = @(
    "server/dbSync/Model/sync.db",
    "client/dbSync/Model/sync.db",
    "server/command_queue.json",
    "client/command_queue.json",
    "server/DB/Data/web_vending.db",
    "client/DB/Data/vending.db"
)

# Cache directories to clear (schema/fields)
$cacheDirectories = @(
    "server/dbSync/Logic_v2/cache/schema",
    "client/dbSync/Logic_v2/cache/schema"
)

# 2. Show what we're about to do
Write-InfoMessage ""
Write-InfoMessage "AutoSklad Database Cleanup Script"
Write-InfoMessage "=================================="
Write-InfoMessage "Project root: $ProjectRoot"
Write-InfoMessage ""
Write-InfoMessage "Files to delete:"
foreach ($relativePath in $filesToDelete) {
    $fullPath = Join-Path $ProjectRoot $relativePath
    $exists = Test-Path $fullPath
    if ($exists) {
        Write-Host "  FOUND: $relativePath" -ForegroundColor Green
    }
    else {
        Write-Host "  NOT FOUND: $relativePath" -ForegroundColor Yellow
    }
}

Write-InfoMessage ""
Write-InfoMessage "Cache directories to clear:"
foreach ($relativePath in $cacheDirectories) {
    $fullPath = Join-Path $ProjectRoot $relativePath
    if (Test-Path $fullPath) {
        Write-Host "  FOUND: $relativePath" -ForegroundColor Green
    }
    else {
        Write-Host "  NOT FOUND: $relativePath" -ForegroundColor Yellow
    }
}
Write-InfoMessage ""

# 3. Ask for confirmation unless forced
if (-not $Force) {
    $confirmation = Read-Host "Do you want to delete these files? (y/N)"
    if ($confirmation -ne "y" -and $confirmation -ne "Y") {
        Write-InfoMessage "Operation cancelled."
        exit 0
    }
}

Write-InfoMessage ""
Write-InfoMessage "Starting deletion..."
Write-InfoMessage ""

$deletedCount = 0
$notFoundCount = 0
$cacheClearedCount = 0
$cacheMissingCount = 0

# 4. Delete each file
foreach ($relativePath in $filesToDelete) {
    $fullPath = Join-Path $ProjectRoot $relativePath

    if (Test-Path $fullPath) {
        try {
            Remove-Item -Path $fullPath -Force -ErrorAction Stop
            Write-SuccessMessage "Deleted: $relativePath"
            $deletedCount++
        }
        catch {
            Write-ErrorMessage "Failed to delete: $relativePath - $($_.Exception.Message)"
        }
    }
    else {
        Write-WarningMessage "Not found: $relativePath"
        $notFoundCount++
    }
}

# 5. Summary
Write-InfoMessage ""
Write-InfoMessage "Clearing cache directories..."
Write-InfoMessage ""
foreach ($relativePath in $cacheDirectories) {
    $fullPath = Join-Path $ProjectRoot $relativePath
    if (Test-Path $fullPath) {
        try {
            Get-ChildItem -Path $fullPath -File | Remove-Item -Force -ErrorAction Stop
            Write-SuccessMessage "Cleared cache: $relativePath"
            $cacheClearedCount++
        }
        catch {
            Write-ErrorMessage "Failed to clear cache: $relativePath - $($_.Exception.Message)"
        }
    }
    else {
        Write-WarningMessage "Cache directory not found: $relativePath"
        $cacheMissingCount++
    }
}

Write-InfoMessage ""
Write-InfoMessage "Cleanup Summary:"
Write-InfoMessage "- Files successfully deleted: $deletedCount"
Write-InfoMessage "- Files not found: $notFoundCount"
Write-InfoMessage "- Cache directories cleared: $cacheClearedCount"
Write-InfoMessage "- Cache directories missing: $cacheMissingCount"

if ($deletedCount -eq $filesToDelete.Count) {
    Write-SuccessMessage "All database files have been cleaned up!"
}
elseif ($deletedCount -gt 0) {
    Write-SuccessMessage "Cleanup partially complete. Some files were deleted."
}
else {
    Write-WarningMessage "No files were deleted. They were either not found or deletion failed."
}

Write-InfoMessage ""
Write-InfoMessage "You may need to restart the client/server for changes to take effect."
