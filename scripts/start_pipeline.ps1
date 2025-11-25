# ============================================
# MASTER PIPELINE ORCHESTRATOR
# ============================================
# Starts complete automated data collection pipeline
# Components: Reddit Collector + HTTP Server + Monitoring
# Usage: .\scripts\start_pipeline.ps1

param(
    [switch]$NoHTTP,        # Skip HTTP server
    [switch]$NoMonitor,     # Skip monitoring dashboard
    [int]$HTTPPort = 8000
)

$ErrorActionPreference = "Continue"

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "         AUTOMATED DATA PIPELINE - STARTING                     " -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

# ============================================
# CLEANUP: Stop any existing pipeline jobs
# ============================================
Write-Host "-- Cleaning up existing jobs..." -ForegroundColor Yellow
$ExistingCollectors = Get-Job -Name "*DataCollector*" -ErrorAction SilentlyContinue
$ExistingHTTP = Get-Job -Name "*HTTPServer*" -ErrorAction SilentlyContinue
$ExistingKafka = Get-Job -Name "*Kafka*" -ErrorAction SilentlyContinue

$CleanedCount = 0
if ($ExistingCollectors) {
    $ExistingCollectors | Stop-Job -PassThru | Remove-Job -Force
    $CleanedCount += $ExistingCollectors.Count
}
if ($ExistingHTTP) {
    $ExistingHTTP | Stop-Job -PassThru | Remove-Job -Force
    $CleanedCount += $ExistingHTTP.Count
}
if ($ExistingKafka) {
    $ExistingKafka | Stop-Job -PassThru | Remove-Job -Force
    $CleanedCount += $ExistingKafka.Count
}

if ($CleanedCount -gt 0) {
    Write-Host "   Stopped $CleanedCount existing job(s)" -ForegroundColor Green
} else {
    Write-Host "   No existing jobs found" -ForegroundColor Gray
}

Start-Sleep -Seconds 2


# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "Created logs directory" -ForegroundColor Green
}

# Track running jobs
$Jobs = @()

# Get current working directory to pass to jobs
$WorkingDir = Get-Location

# 1. Start Reddit Data Collector
Write-Host "`n-- Starting Reddit Data Collector..." -ForegroundColor Yellow
$CollectorJob = Start-Job -Name "DataCollector" -ScriptBlock {
    param($WorkDir)
    Set-Location $WorkDir
    & "$WorkDir\scripts\start_collector.ps1" -MaxRestarts 999
} -ArgumentList $WorkingDir
$Jobs += $CollectorJob
Write-Host "   Status: STARTED (Job ID: $($CollectorJob.Id))" -ForegroundColor Green
Write-Host "   Logs:   logs\collector-$(Get-Date -Format 'yyyy-MM-dd').log" -ForegroundColor Gray

Start-Sleep -Seconds 3


# Start HTTP Server (if enabled)
if (-not $NoHTTP) {
    Write-Host "`n-- Starting HTTP Data Server..." -ForegroundColor Yellow
    $HTTPJob = Start-Job -Name "HTTPServer" -ScriptBlock {
        param($Port)
        Set-Location $using:PWD
        .\scripts\start_http_server.ps1 -Port $Port
    } -ArgumentList $HTTPPort
    $Jobs += $HTTPJob
    Write-Host "   Status: STARTED (Job ID: $($HTTPJob.Id))" -ForegroundColor Green
    Write-Host "   Port:   $HTTPPort" -ForegroundColor Gray
    Write-Host "   URL:    http://localhost:$HTTPPort/" -ForegroundColor Gray
    
    # Get network IP
    $LocalIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"} | Select-Object -First 1).IPAddress
    if ($LocalIP) {
        Write-Host "   Network: http://$($LocalIP):$HTTPPort/" -ForegroundColor Cyan
    }
    Start-Sleep -Seconds 2
} else {
    Write-Host "`nHTTP Server: SKIPPED" -ForegroundColor Gray
}

# 4. Display Pipeline Status
Write-Host "`n================================================================" -ForegroundColor Green
Write-Host "         PIPELINE STARTED SUCCESSFULLY                          " -ForegroundColor Green
Write-Host "================================================================`n" -ForegroundColor Green

Write-Host "Active Components:" -ForegroundColor Cyan
Write-Host "  - Reddit Data Collector (collecting from 15 subreddits)" -ForegroundColor White
if (-not $NoHTTP) {
    Write-Host "  - HTTP Data Server (port: $HTTPPort)" -ForegroundColor White
}

Write-Host "`nData Access URLs:" -ForegroundColor Cyan
if (-not $NoHTTP) {
    Write-Host "  HTTP (Batch):     http://localhost:$HTTPPort/" -ForegroundColor Yellow
    if ($LocalIP) {
        Write-Host "  HTTP (Network):   http://$($LocalIP):$HTTPPort/" -ForegroundColor Yellow
    }
}

Write-Host "`nManagement Commands:" -ForegroundColor Cyan
Write-Host "  Monitor Pipeline:  .\scripts\monitor_pipeline.ps1" -ForegroundColor White
Write-Host "  View Jobs:         Get-Job" -ForegroundColor White
Write-Host "  Stop All:          Get-Job | Stop-Job; Get-Job | Remove-Job" -ForegroundColor White
Write-Host "  View Logs:         Get-Content logs\collector-$(Get-Date -Format 'yyyy-MM-dd').log -Wait" -ForegroundColor White

# 5. Start Monitoring Dashboard (if enabled)
if (-not $NoMonitor) {
    Write-Host "`nStarting monitoring dashboard in 5 seconds..." -ForegroundColor Yellow
    Write-Host "(Press Ctrl+C now to skip monitoring and keep pipeline running in background)`n" -ForegroundColor Gray
    
    Start-Sleep -Seconds 5
    
    # Run monitoring in foreground
    .\scripts\monitor_pipeline.ps1
} else {
    Write-Host "`nMonitoring Dashboard: SKIPPED" -ForegroundColor Gray
    Write-Host "`nPipeline running in background. Use monitoring script to check status:" -ForegroundColor Yellow
    Write-Host "  .\scripts\monitor_pipeline.ps1`n" -ForegroundColor White
}

