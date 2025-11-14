# Kafka Real-Time Consumers

## Usage

**ML Consumer**:
```powershell
py -3 examples\kafka_consumer_ml.py
```

**Live Dashboard**:
```powershell
py -3 examples\kafka_dashboard.py --refresh 2
```

## Setup

1. Enable Kafka sink in `configs/config.yaml`:
```yaml
stream:
  sink: kafka
```

2. Start Reddit collector:
```powershell
py -3 -m src.collector.connectors.reddit_poll
```

3. Run consumers in separate terminals

## Kafka UI

View messages in browser: `http://localhost:8090`
