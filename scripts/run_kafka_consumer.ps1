param(
    [string]$Bootstrap = "localhost:9092",
    [string]$Topic = "social_events",
    [string]$Group = "demo-consumer",
    [string]$Out = $null
)

Write-Host "Starting Kafka consumer on $Bootstrap topic $Topic" -ForegroundColor Cyan
py -3 -m src.consumer.kafka_tail --bootstrap $Bootstrap --topic $Topic --group $Group --out $Out
