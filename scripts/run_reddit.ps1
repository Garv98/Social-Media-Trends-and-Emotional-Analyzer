param(
    [string]$ConfigPath = "configs/config.yaml"
)

Write-Host "Running Reddit polling collector" -ForegroundColor Cyan
python -m src.collector.connectors.reddit_poll --config $ConfigPath
