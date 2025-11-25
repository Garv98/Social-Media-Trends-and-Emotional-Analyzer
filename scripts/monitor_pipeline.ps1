# ============================================
# PIPELINE MONITORING DASHBOARD
# ============================================
# Live monitoring of automated data pipeline
# Shows status of collector and HTTP server
# Usage: .\scripts\monitor_pipeline.ps1

param()

$ErrorActionPreference = "SilentlyContinue"

function Get-CollectorStats {
    $logFile = "logs\collector-$(Get-Date -Format 'yyyy-MM-dd').log"
    if (Test-Path $logFile) {
        $content = Get-Content $logFile -Tail 20
        $events = ($content | Select-String "Processed:" | Select-Object -Last 1).ToString()
        $dedup = ($content | Select-String "Deduped:" | Select-Object -Last 1).ToString()
        $errors = ($content | Select-String "Errors:" | Select-Object -Last 1).ToString()
        
        $eventCount = if ($events -match "Processed:\s*(\d+)") { $matches[1] } else { 0 }
        $dedupCount = if ($dedup -match "Deduped:\s*(\d+)") { $matches[1] } else { 0 }
        $errorCount = if ($errors -match "Errors:\s*(\d+)") { $matches[1] } else { 0 }
        
        return @{
            Events = [int]$eventCount
            Deduped = [int]$dedupCount
            Errors = [int]$errorCount
        }
    }
    return @{ Events = 0; Deduped = 0; Errors = 0 }
}

function Get-FileStats {
    $dataDir = "data\raw\$(Get-Date -Format 'yyyy\\MM\\dd')"
    if (Test-Path $dataDir) {
        $files = Get-ChildItem $dataDir -Filter "*.jsonl"
        $totalSize = ($files | Measure-Object -Property Length -Sum).Sum
        $lastFile = $files | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        $lastUpdate = if ($lastFile) { $lastFile.LastWriteTime.ToString("HH:mm:ss") } else { "N/A" }
        return @{
            FileCount = $files.Count
            TotalSize = [math]::Round($totalSize / 1MB, 2)
            LastUpdate = $lastUpdate
        }
    }
    return @{ FileCount = 0; TotalSize = 0; LastUpdate = "N/A" }
}

function Get-HTTPStats {
    # Simple check - in production, you'd query actual server stats
    return @{ Requests = 0 }  # Placeholder
}

# Main monitoring loop
do {
    Clear-Host
    
    Write-Host "================================================================`n         AUTOMATED PIPELINE MONITORING DASHBOARD`n================================================================`n"
    
    # Get job statuses
    $Collector = Get-Job -Name "*DataCollector*" -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Running" } | Select-Object -First 1
    $HTTP = Get-Job -Name "*HTTPServer*" -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Running" } | Select-Object -First 1
    
    # Collector stats
    $collectorStats = Get-CollectorStats
    $fileStats = Get-FileStats
    
    # Status variables (compatible with older PowerShell)
    $collectorStatus = if ($Collector) { "RUNNING" } else { "STOPPED" }
    $httpStatus = if ($HTTP) { "RUNNING" } else { "STOPPED" }
    $AllRunning = $Collector -and $HTTP
    $overallStatus = if ($AllRunning) { "ALL SYSTEMS OPERATIONAL" } else { "PARTIAL OPERATION" }
    
    Write-Host "-- REDDIT DATA COLLECTOR [$collectorStatus]"
    Write-Host ("   Events Today:      " + $collectorStats.Events)
    Write-Host ("   File Size:         " + $fileStats.TotalSize + " MB")
    Write-Host ("   Last Update:       " + $fileStats.LastUpdate)
    Write-Host ("   Collection Rate:   " + [math]::Round($collectorStats.Events / 60, 1) + " events/min")
    Write-Host ("   Subreddits:        15")
    Write-Host ("   Errors Today:      " + $collectorStats.Errors + "`n")
    
    # HTTP Server stats
    $httpStats = Get-HTTPStats
    
    Write-Host "-- HTTP DATA SERVER [$httpStatus]"
    Write-Host ("   Requests Today:    " + $httpStats.Requests)
    Write-Host ("   Port:              8000")
    Write-Host ("   URL:               http://localhost:8000/")
    Write-Host ("   Network:           http://" + (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -like "*Wi-Fi*" } | Select-Object -First 1 -ExpandProperty IPAddress) + ":8000/`n")
    
    Write-Host "Pipeline Status: $overallStatus`n"
    
    Write-Host "Refreshing in 10 seconds... (Ctrl+C to stop)`n"
    Write-Host "Last Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    
    Start-Sleep -Seconds 10
} while ($true)