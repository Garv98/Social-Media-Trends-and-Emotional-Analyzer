param(
    [switch]$EnableKafka,
    [switch]$TestConsumer,
    [switch]$Dashboard
)

Write-Host "`nKafka Setup`n" -ForegroundColor Cyan

# Check Kafka
$kafkaPort = netstat -an | Select-String ":9092" -Quiet
if (-not $kafkaPort) {
    Write-Host "ERROR: Kafka not running on port 9092" -ForegroundColor Red
    exit 1
}
Write-Host "Kafka: Running`n" -ForegroundColor Green

if ($EnableKafka) {
    Copy-Item configs\config.yaml configs\config.yaml.backup -Force
    $config = Get-Content configs\config.yaml -Raw
    $config = $config -replace 'sink: file', 'sink: kafka'
    Set-Content configs\config.yaml -Value $config
    
    Write-Host "Config updated to Kafka sink" -ForegroundColor Green
    Write-Host "Next: py -3 -m src.collector.connectors.reddit_poll`n"
}
elseif ($TestConsumer) {
    Write-Host "Starting ML consumer...`n"
    py -3 examples\kafka_consumer_ml.py
}
elseif ($Dashboard) {
    Write-Host "Starting dashboard...`n"
    py -3 examples\kafka_dashboard.py
}
else {
    Write-Host "Options:"
    Write-Host "  -EnableKafka     Switch to Kafka sink"
    Write-Host "  -TestConsumer    Run ML consumer"
    Write-Host "  -Dashboard       Run live dashboard`n"
}
