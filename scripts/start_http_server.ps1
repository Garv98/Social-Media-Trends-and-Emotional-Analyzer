# ============================================
# Automated HTTP Data Server
# ============================================
# Serves collected data globally via HTTP
# Usage: .\scripts\start_http_server.ps1

param(
    [int]$Port = 8000,
    [string]$ListenAddress = "0.0.0.0"  # Listen on all interfaces for global access
)

$ErrorActionPreference = "Continue"
$LogDir = "logs"
$LogFile = "$LogDir\http-server-$(Get-Date -Format 'yyyy-MM-dd').log"

# Create logs directory
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

Write-Log "=== HTTP DATA SERVER STARTING ==="
Write-Log "Host: $ListenAddress"
Write-Log "Port: $Port"
Write-Log "Data Directory: data/raw"
Write-Log "Log File: $LogFile"

# Get local IP address for display
$LocalIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"} | Select-Object -First 1).IPAddress

Write-Log "Access URLs:"
Write-Log "  Local:  http://localhost:$Port/"
Write-Log "  Network: http://$($LocalIP):$Port/"
Write-Log "  Global: http://<your-public-ip>:$Port/"
Write-Host "`nPress Ctrl+C to stop the server`n" -ForegroundColor Yellow

try {
    # Start Python HTTP server
    Set-Location "data\raw"
    py -3 -m http.server $Port --bind $ListenAddress 2>&1 | ForEach-Object {
        Write-Log $_
    }
} catch {
    Write-Log "ERROR: $($_.Exception.Message)"
} finally {
    Set-Location ..\..
    Write-Log "=== HTTP SERVER STOPPED ==="
}
