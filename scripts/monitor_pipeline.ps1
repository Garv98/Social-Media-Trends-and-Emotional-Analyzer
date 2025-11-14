# ============================================
# Pipeline Monitoring Dashboard
# ============================================
# Real-time monitoring of collector health and metrics
# Usage: .\scripts\monitor_pipeline.ps1

param(
    [int]$RefreshSeconds = 10
)

$ErrorActionPreference = "SilentlyContinue"

function Get-CollectorStats {
    $Stats = @{
        IsRunning = $false
        EventsToday = 0
        FileSize = "0 KB"
        LastUpdate = "Never"
        DataRate = "0 events/min"
        UniqueSubreddits = 0
        ErrorCount = 0
    }
    
    # Check if collector is running
    $CollectorProcess = Get-Process | Where-Object { $_.CommandLine -like "*reddit_poll*" }
    $Stats.IsRunning = $null -ne $CollectorProcess
    
    # Get today's events file
    $TodayPath = "data\raw\$(Get-Date -Format 'yyyy\\MM\\dd')"
    $EventFile = "$TodayPath\events-$(Get-Date -Format 'yyyy-MM-dd').jsonl"
    
    if (Test-Path $EventFile) {
        # Count events
        $Stats.EventsToday = (Get-Content $EventFile | Measure-Object -Line).Lines
        
        # File size
        $FileSizeBytes = (Get-Item $EventFile).Length
        if ($FileSizeBytes -gt 1MB) {
            $Stats.FileSize = "{0:N2} MB" -f ($FileSizeBytes / 1MB)
        } else {
            $Stats.FileSize = "{0:N2} KB" -f ($FileSizeBytes / 1KB)
        }
        
        # Last update
        $LastWrite = (Get-Item $EventFile).LastWriteTime
        $Stats.LastUpdate = $LastWrite.ToString("HH:mm:ss")
        
        # Calculate data rate (events in last 5 minutes)
        $RecentEvents = Get-Content $EventFile -Tail 100 | ForEach-Object {
            try {
                $Event = $_ | ConvertFrom-Json
                $EventTime = [DateTime]::Parse($Event.collected_at)
                if (((Get-Date) - $EventTime).TotalMinutes -le 5) {
                    1
                }
            } catch { }
        } | Measure-Object -Sum
        
        if ($RecentEvents.Sum) {
            $Stats.DataRate = "{0:N1} events/min" -f ($RecentEvents.Sum / 5)
        }
        
        # Unique subreddits today
        $Subreddits = Get-Content $EventFile | ForEach-Object {
            try {
                ($_ | ConvertFrom-Json).metadata.subreddit
            } catch { }
        } | Sort-Object -Unique
        $Stats.UniqueSubreddits = ($Subreddits | Measure-Object).Count
    }
    
    # Check for errors in logs
    $LogFile = "logs\collector-$(Get-Date -Format 'yyyy-MM-dd').log"
    if (Test-Path $LogFile) {
        $Stats.ErrorCount = (Select-String -Path $LogFile -Pattern "\[ERROR\]" | Measure-Object).Count
    }
    
    return $Stats
}

function Get-KafkaStats {
    $Stats = @{
        IsRunning = $false
        MessagesSent = 0
    }
    
    # Check if Kafka producer is running
    $KafkaProcess = Get-Process | Where-Object { $_.CommandLine -like "*kafka_producer.py*" }
    $Stats.IsRunning = $null -ne $KafkaProcess
    
    # Count messages from log
    $LogFile = "logs\kafka-producer-$(Get-Date -Format 'yyyy-MM-dd').log"
    if (Test-Path $LogFile) {
        $Stats.MessagesSent = (Select-String -Path $LogFile -Pattern "Delivered to" | Measure-Object).Count
    }
    
    return $Stats
}

function Get-HTTPServerStats {
    $Stats = @{
        IsRunning = $false
        Port = 8000
        Requests = 0
    }
    
    # Check if HTTP server is running
    $HTTPProcess = Get-Process | Where-Object { $_.CommandLine -like "*http.server*" }
    $Stats.IsRunning = $null -ne $HTTPProcess
    
    # Count requests from log
    $LogFile = "logs\http-server-$(Get-Date -Format 'yyyy-MM-dd').log"
    if (Test-Path $LogFile) {
        $Stats.Requests = (Select-String -Path $LogFile -Pattern "GET" | Measure-Object).Count
    }
    
    return $Stats
}

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "     AUTOMATED PIPELINE MONITORING DASHBOARD                   " -ForegroundColor Cyan
Write-Host "================================================================`n" -ForegroundColor Cyan

Write-Host "Press Ctrl+C to stop monitoring`n" -ForegroundColor Yellow

while ($true) {
    $Collector = Get-CollectorStats
    $Kafka = Get-KafkaStats
    $HTTP = Get-HTTPServerStats
    
    Clear-Host
    
    Write-Host "`n================================================================" -ForegroundColor Cyan
    Write-Host "     AUTOMATED PIPELINE MONITORING DASHBOARD                   " -ForegroundColor Cyan
    Write-Host "================================================================`n" -ForegroundColor Cyan
    
    # Collector Status
    Write-Host "-- REDDIT DATA COLLECTOR " -NoNewline -ForegroundColor Yellow
    if ($Collector.IsRunning) {
        Write-Host "[RUNNING]" -ForegroundColor Green
    } else {
        Write-Host "[STOPPED]" -ForegroundColor Red
    }
    Write-Host "   Events Today:      $($Collector.EventsToday)" -ForegroundColor White
    Write-Host "   File Size:         $($Collector.FileSize)" -ForegroundColor White
    Write-Host "   Last Update:       $($Collector.LastUpdate)" -ForegroundColor White
    Write-Host "   Collection Rate:   $($Collector.DataRate)" -ForegroundColor White
    Write-Host "   Subreddits:        $($Collector.UniqueSubreddits)" -ForegroundColor White
    Write-Host "   Errors Today:      $($Collector.ErrorCount)" -ForegroundColor $(if ($Collector.ErrorCount -eq 0) { "Green" } else { "Red" })
    Write-Host ""
    
    # Kafka Status
    Write-Host "-- KAFKA REAL-TIME STREAMING " -NoNewline -ForegroundColor Yellow
    if ($Kafka.IsRunning) {
        Write-Host "[RUNNING]" -ForegroundColor Green
    } else {
        Write-Host "[STOPPED]" -ForegroundColor Red
    }
    Write-Host "   Messages Sent:     $($Kafka.MessagesSent)" -ForegroundColor White
    Write-Host "   Topic:             social-media-events" -ForegroundColor White
    Write-Host "   Bootstrap:         localhost:9092" -ForegroundColor White
    Write-Host ""
    
    # HTTP Server Status
    Write-Host "-- HTTP DATA SERVER " -NoNewline -ForegroundColor Yellow
    if ($HTTP.IsRunning) {
        Write-Host "[RUNNING]" -ForegroundColor Green
    } else {
        Write-Host "[STOPPED]" -ForegroundColor Red
    }
    Write-Host "   Requests Today:    $($HTTP.Requests)" -ForegroundColor White
    Write-Host "   Port:              $($HTTP.Port)" -ForegroundColor White
    Write-Host "   URL:               http://localhost:$($HTTP.Port)/" -ForegroundColor White
    Write-Host ""
    
    # Overall Status
    $AllRunning = $Collector.IsRunning -and $Kafka.IsRunning -and $HTTP.IsRunning
    Write-Host "Pipeline Status: " -NoNewline -ForegroundColor Cyan
    if ($AllRunning) {
        Write-Host "ALL SYSTEMS OPERATIONAL" -ForegroundColor Green
    } else {
        Write-Host "PARTIAL OPERATION" -ForegroundColor Yellow
    }
    
    Write-Host "`nRefreshing in $RefreshSeconds seconds... (Ctrl+C to stop)" -ForegroundColor Gray
    $timestamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    Write-Host "Last Update: $timestamp`n" -ForegroundColor Gray
    
    Start-Sleep -Seconds $RefreshSeconds
}
