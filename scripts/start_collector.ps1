# ============================================
# Automated Reddit Data Collector
# ============================================
# Starts collector with auto-restart, logging, and health monitoring
# Usage: .\scripts\start_collector.ps1

param(
    [int]$MaxRestarts = 999,
    [int]$RestartDelaySeconds = 30
)

$ErrorActionPreference = "Continue"

# Get working directory - use parameter if provided, otherwise detect from script location
if (-not $PSCommandPath) {
    # Running in a job without script path - use current location
    $WorkDir = (Get-Location).Path
} else {
    # Running directly - calculate from script location
    $ScriptDir = Split-Path -Parent $PSCommandPath
    $WorkDir = Split-Path -Parent $ScriptDir
}

Write-Host "DEBUG: PSCommandPath = '$PSCommandPath'" -ForegroundColor Gray
Write-Host "DEBUG: WorkDir = '$WorkDir'" -ForegroundColor Gray

Set-Location $WorkDir

$LogDir = "logs"
$LogFile = "$LogDir\collector-$(Get-Date -Format 'yyyy-MM-dd').log"

# Create logs directory
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

Write-Log "=== AUTOMATED DATA COLLECTOR STARTED ===" "INFO"
Write-Log "Working Directory: $WorkDir" "INFO"
Write-Log "Max Restarts: $MaxRestarts" "INFO"
Write-Log "Restart Delay: $RestartDelaySeconds seconds" "INFO"

$RestartCount = 0

while ($RestartCount -lt $MaxRestarts) {
    try {
        Write-Log "Starting collector (Attempt $($RestartCount + 1)/$MaxRestarts)" "INFO"
        
        # Run the collector directly in this process (not via Start-Process)
        # This ensures proper environment inheritance
        $output = & py -3 -m src.collector.connectors.reddit_poll --config configs/config.yaml 2>&1
        
        # Log the output
        $output | ForEach-Object {
            Write-Log $_ "INFO"
        }
        
        # If we get here, the process exited
        Write-Log "Collector exited normally" "WARN"
        
    } catch {
        Write-Log "Error running collector: $($_.Exception.Message)" "ERROR"
        Write-Log "Error details: $($_.Exception.StackTrace)" "ERROR"
    }
    
    $RestartCount++
    
    if ($RestartCount -lt $MaxRestarts) {
        Write-Log "Restarting in $RestartDelaySeconds seconds..." "INFO"
        Start-Sleep -Seconds $RestartDelaySeconds
    } else {
        Write-Log "Max restart limit reached. Stopping." "ERROR"
    }
}

Write-Log "=== COLLECTOR STOPPED ===" "INFO"
