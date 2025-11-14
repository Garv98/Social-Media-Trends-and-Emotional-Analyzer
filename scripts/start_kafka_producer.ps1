# ============================================
# Automated Kafka Producer
# ============================================
# Streams collected data to Kafka for global real-time access
# Usage: .\scripts\start_kafka_producer.ps1

param(
    [string]$KafkaBootstrap = "localhost:9092",
    [string]$Topic = "social-media-events",
    [int]$MaxRestarts = 999
)

$ErrorActionPreference = "Continue"
$LogDir = "logs"
$LogFile = "$LogDir\kafka-producer-$(Get-Date -Format 'yyyy-MM-dd').log"

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

Write-Log "=== KAFKA PRODUCER STARTED ===" "INFO"
Write-Log "Kafka Bootstrap: $KafkaBootstrap" "INFO"
Write-Log "Topic: $Topic" "INFO"

$RestartCount = 0

# Create Kafka producer script
$ProducerScript = @'
import sys
import json
import time
from pathlib import Path
from confluent_kafka import Producer

def delivery_report(err, msg):
    if err:
        print(f"ERROR: Delivery failed: {err}", file=sys.stderr)
    else:
        print(f"Delivered to {msg.topic()} [{msg.partition()}] @ {msg.offset()}")

def tail_file(file_path, producer, topic):
    """Stream new lines from file to Kafka"""
    with open(file_path, 'r', encoding='utf-8') as f:
        # Move to end of file
        f.seek(0, 2)
        
        while True:
            line = f.readline()
            if line:
                try:
                    event = json.loads(line.strip())
                    producer.produce(
                        topic,
                        key=event.get('id', '').encode('utf-8'),
                        value=line.strip().encode('utf-8'),
                        callback=delivery_report
                    )
                    producer.poll(0)
                except Exception as e:
                    print(f"ERROR: Failed to send: {e}", file=sys.stderr)
            else:
                time.sleep(1)
                producer.poll(0)

if __name__ == '__main__':
    bootstrap_servers = sys.argv[1]
    topic = sys.argv[2]
    
    config = {
        'bootstrap.servers': bootstrap_servers,
        'client.id': 'reddit-collector-producer'
    }
    
    producer = Producer(config)
    print(f"Kafka producer connected to {bootstrap_servers}")
    print(f"Streaming to topic: {topic}")
    
    # Get today's events file
    from datetime import datetime
    today = datetime.now()
    file_path = Path(f"data/raw/{today.year}/{today.month:02d}/{today.day:02d}/events-{today.year}-{today.month:02d}-{today.day:02d}.jsonl")
    
    if not file_path.exists():
        print(f"Waiting for file: {file_path}")
        while not file_path.exists():
            time.sleep(5)
    
    print(f"Tailing file: {file_path}")
    tail_file(file_path, producer, topic)
'@

$ProducerScriptPath = "$LogDir\kafka_producer.py"
$ProducerScript | Out-File -FilePath $ProducerScriptPath -Encoding UTF8

while ($RestartCount -lt $MaxRestarts) {
    try {
        Write-Log "Starting Kafka producer (Attempt $($RestartCount + 1))" "INFO"
        
        py -3 $ProducerScriptPath $KafkaBootstrap $Topic 2>&1 | ForEach-Object {
            Write-Log $_ "INFO"
        }
        
    } catch {
        Write-Log "Error: $($_.Exception.Message)" "ERROR"
    }
    
    $RestartCount++
    if ($RestartCount -lt $MaxRestarts) {
        Write-Log "Restarting in 10 seconds..." "WARN"
        Start-Sleep -Seconds 10
    }
}

Write-Log "=== KAFKA PRODUCER STOPPED ===" "INFO"
