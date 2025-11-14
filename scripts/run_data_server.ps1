param(
    [int]$Port = 8000
)

Write-Host "Starting data file server on port $Port..." -ForegroundColor Cyan
py -3 -m src.consumer.data_server --port $Port
