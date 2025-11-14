# Automated Data Collection Pipeline
## Complete End-to-End Solution for Global Data Streaming

---

## 🚀 Quick Start

### Start Complete Pipeline (Recommended)
```powershell
.\scripts\start_pipeline.ps1
```

This single command starts:
- ✅ **Reddit Data Collector** - Polls 15 subreddits every 60 seconds
- ✅ **Kafka Streaming** - Real-time global data distribution
- ✅ **HTTP Server** - Team access to historical data files
- ✅ **Live Monitoring** - Real-time dashboard with health metrics

### Start Individual Components

```powershell
# Start only the collector (minimal setup)
.\scripts\start_collector.ps1

# Start only HTTP server for file access
.\scripts\start_http_server.ps1 -Port 8000

# Start only Kafka streaming
.\scripts\start_kafka_producer.ps1

# Monitor running pipeline
.\scripts\monitor_pipeline.ps1
```

### Pipeline Control Options

```powershell
# Start without Kafka (file-only mode)
.\scripts\start_pipeline.ps1 -NoKafka

# Start without HTTP server
.\scripts\start_pipeline.ps1 -NoHTTP

# Start in background (no monitoring dashboard)
.\scripts\start_pipeline.ps1 -NoMonitor

# Custom HTTP port
.\scripts\start_pipeline.ps1 -HTTPPort 9000
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   AUTOMATED PIPELINE                        │
└─────────────────────────────────────────────────────────────┘

   Reddit API (15 subreddits)
          ↓
   ┌──────────────────┐
   │ Data Collector   │ ← Auto-restart on failure
   │ (reddit_poll.py) │    Health monitoring
   └────────┬─────────┘    Error logging
            │
            ├─────────────────────────┐
            ↓                         ↓
   ┌─────────────────┐      ┌─────────────────┐
   │   File Sink     │      │  Kafka Sink     │
   │  (JSONL files)  │      │  (Real-time)    │
   └────────┬────────┘      └────────┬────────┘
            │                        │
            ↓                        ↓
   ┌─────────────────┐      ┌─────────────────┐
   │  HTTP Server    │      │ Kafka Consumers │
   │  Port: 8000     │      │ Topic: social-  │
   │  Team Access    │      │ media-events    │
   └─────────────────┘      └─────────────────┘
            │                        │
            ↓                        ↓
      Model Team              Dashboard Team
    (Batch Training)        (Real-time Viz)
```

---

## 🌍 Global Data Access

### 1. Real-Time Streaming (Kafka)

**For Dashboard Team & Real-Time Applications**

```python
# Connect to Kafka stream
from confluent_kafka import Consumer

consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'your-team-name',
    'auto.offset.reset': 'latest'
})

consumer.subscribe(['social-media-events'])

while True:
    msg = consumer.poll(1.0)
    if msg:
        event = json.loads(msg.value().decode('utf-8'))
        # Process event in real-time
        print(f"New event: {event['text'][:50]}...")
```

**Access URLs:**
- Local: `localhost:9092`
- Network: `<your-ip>:9092`
- Topic: `social-media-events`

### 2. Batch File Access (HTTP)

**For Model Team & Historical Analysis**

```python
# Download data files via HTTP
import requests

response = requests.get('http://localhost:8000/2025/11/10/events-2025-11-10.jsonl')
events = [json.loads(line) for line in response.text.split('\n') if line]
```

**Access URLs:**
- Local: `http://localhost:8000/`
- Network: `http://<your-ip>:8000/`
- Browser: Navigate to view file directory

**File Structure:**
```
http://localhost:8000/
  └── 2025/
      └── 11/
          └── 10/
              └── events-2025-11-10.jsonl  (JSONL format)
```

---

## 📈 Monitoring & Health Checks

### Live Dashboard

```powershell
.\scripts\monitor_pipeline.ps1
```

**Dashboard Shows:**
- ✅ Collector Status (Running/Stopped)
- 📊 Events Collected Today
- 💾 File Size & Last Update
- ⚡ Collection Rate (events/min)
- 🎯 Unique Subreddits Covered
- ❌ Error Count
- 🔴 Kafka Messages Sent
- 🌐 HTTP Server Requests

**Example Output:**
```
╔══════════════════════════════════════════════════════════════╗
║     AUTOMATED PIPELINE MONITORING DASHBOARD                 ║
╚══════════════════════════════════════════════════════════════╝

┌─ REDDIT DATA COLLECTOR ✓ RUNNING
│  Events Today:      1,547
│  File Size:         234.56 KB
│  Last Update:       14:32:15
│  Collection Rate:   154.2 events/min
│  Subreddits:        15
│  Errors Today:      0
└─────────────────────────────────────────────────────────────

┌─ KAFKA REAL-TIME STREAMING ✓ RUNNING
│  Messages Sent:     1,547
│  Topic:             social-media-events
│  Bootstrap:         localhost:9092
└─────────────────────────────────────────────────────────────

┌─ HTTP DATA SERVER ✓ RUNNING
│  Requests Today:    23
│  Port:              8000
│  URL:               http://localhost:8000/
└─────────────────────────────────────────────────────────────

Pipeline Status: ALL SYSTEMS OPERATIONAL ✓
```

### Manual Health Checks

```powershell
# Check if collector is running
Get-Process | Where-Object { $_.CommandLine -like "*reddit_poll*" }

# View collector logs
Get-Content logs\collector-$(Get-Date -Format 'yyyy-MM-dd').log -Tail 50 -Wait

# Check today's data
Get-Content "data\raw\$(Get-Date -Format 'yyyy\\MM\\dd')\events-$(Get-Date -Format 'yyyy-MM-dd').jsonl" | Measure-Object -Line

# View background jobs
Get-Job

# Stop all components
Get-Job | Stop-Job
Get-Job | Remove-Job
```

---

## 🔧 Configuration

### Data Collection Settings (`configs/config.yaml`)

```yaml
sources:
  reddit:
    enabled: true
    mode: poll
    subreddits: [
      "news", "worldnews", "politics",       # News & Current Events
      "technology", "science", "Futurology",  # Tech & Science
      "movies", "gaming", "Music",            # Entertainment
      "fitness", "todayilearned", "LifeProTips",  # Lifestyle
      "stocks", "sports", "AskReddit"         # Finance, Sports, Social
    ]
    query: ""  # Empty = ALL posts (no keyword filtering)
    poll_interval_sec: 60  # Poll every 60 seconds
    limit_per_call: 10     # 10 posts/subreddit = 150 posts/poll
```

**Expected Volume:**
- **Per Poll:** 150 posts (15 subreddits × 10 posts)
- **Per Hour:** ~9,000 posts (60 polls × 150 posts)
- **Per Day:** ~216,000 posts (24 hours × 9,000)
- **File Size:** ~50 MB/day (after deduplication ~30%)

### Dual Sink Configuration

```yaml
stream:
  sink: file,kafka  # Both sinks enabled

sinks:
  file:
    root_dir: data/raw
    partition_by: date
    filename_pattern: "events-%Y-%m-%d.jsonl"

  kafka:
    bootstrap_servers: "localhost:9092"
    topic: "social-media-events"
    acks: 1
    compression_type: "snappy"
```

---

## 🛠️ Troubleshooting

### Collector Not Starting

```powershell
# Check Python environment
py -3 --version

# Test Reddit API credentials
py -3 -c "import praw; r = praw.Reddit('bot1'); print('OK')"

# Check config file
Get-Content configs\config.yaml

# View error logs
Get-Content logs\collector-$(Get-Date -Format 'yyyy-MM-dd').log | Select-String "ERROR"
```

### Kafka Connection Issues

```powershell
# Check if Kafka is running
Get-Process | Where-Object { $_.Name -like "*kafka*" }

# Test Kafka connectivity
py -3 -c "from confluent_kafka import Producer; p = Producer({'bootstrap.servers': 'localhost:9092'}); print('OK')"

# View Kafka UI
Start-Process "http://localhost:8090"  # Kafka UI
```

### HTTP Server Not Accessible

```powershell
# Check if port is in use
netstat -ano | findstr :8000

# Test local access
Invoke-WebRequest -Uri "http://localhost:8000/" -Method HEAD

# Check firewall rules (for network access)
Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*Python*" }
```

### No Data Being Collected

**Possible Causes:**
1. **Reddit API rate limit** - Check logs for "429" errors
2. **Network issues** - Verify internet connection
3. **Config errors** - Validate YAML syntax
4. **Credentials expired** - Refresh Reddit API tokens

**Debug Steps:**
```powershell
# Test direct collection
py -3 -m src.collector.connectors.reddit_poll --config configs/config.yaml

# Check deduplication ratio
Get-Content logs\collector-$(Get-Date -Format 'yyyy-MM-dd').log | Select-String "DEDUP"

# Verify subreddit accessibility
py -3 -c "import praw; r = praw.Reddit('bot1'); print(list(r.subreddit('technology').new(limit=5)))"
```

---

## 📋 Maintenance

### Daily Tasks

```powershell
# Check pipeline health (automated)
.\scripts\monitor_pipeline.ps1

# View collection summary
$file = "data\raw\$(Get-Date -Format 'yyyy\\MM\\dd')\events-$(Get-Date -Format 'yyyy-MM-dd').jsonl"
Get-Content $file | Measure-Object -Line
```

### Weekly Tasks

```powershell
# Archive old logs
Compress-Archive -Path "logs\*.log" -DestinationPath "logs\archive-$(Get-Date -Format 'yyyy-MM-dd').zip"
Remove-Item "logs\*.log" -Exclude "*$(Get-Date -Format 'yyyy-MM-dd')*"

# Check disk space
Get-PSDrive C | Select-Object Used,Free
```

### Monthly Tasks

```powershell
# Review error patterns
Get-Content logs\*.log | Select-String "ERROR" | Group-Object | Sort-Object Count -Descending

# Update Reddit API credentials (if rotating)
# Edit credentials in Reddit developer portal

# Review subreddit coverage
# Adjust configs/config.yaml if topics need expansion
```

---

## 🎯 Performance Optimization

### Increase Collection Rate

```yaml
# In configs/config.yaml
sources:
  reddit:
    poll_interval_sec: 30  # Poll every 30 seconds (2x faster)
    limit_per_call: 20     # 20 posts/subreddit (2x more)
```

⚠️ **Warning:** Higher rates may hit Reddit API limits (60 requests/minute)

### Reduce Memory Usage

```yaml
stream:
  batch_size: 10        # Flush more frequently
  flush_interval_ms: 100  # Shorter interval
```

### Network Optimization

```yaml
sinks:
  kafka:
    compression_type: "snappy"  # Compress data
    max_in_flight_requests: 5   # Pipeline requests
    linger_ms: 100              # Batch messages
```

---

## 🔐 Security Considerations

### HTTP Server Access Control

```powershell
# Restrict to localhost only (more secure)
.\scripts\start_http_server.ps1 -Host "127.0.0.1"

# Allow network access (less secure, for team)
.\scripts\start_http_server.ps1 -Host "0.0.0.0"
```

### Kafka Authentication

Currently using local Kafka without authentication. For production:

```yaml
sinks:
  kafka:
    bootstrap_servers: "your-kafka-cluster:9093"
    security_protocol: "SASL_SSL"
    sasl_mechanism: "PLAIN"
    sasl_username: "your-username"
    sasl_password: "your-password"
```

### Credentials Management

Reddit API credentials stored in `praw.ini`. **Do not commit this file to Git!**

```powershell
# Verify praw.ini is in .gitignore
Get-Content .gitignore | Select-String "praw.ini"
```

---

## 📞 Team Integration Guide

### Model Team (Batch Processing)

**Access Method:** HTTP Server

```python
# Download all data for training
import requests
import json
from datetime import datetime, timedelta

def download_events(date):
    url = f"http://localhost:8000/{date.year}/{date.month:02d}/{date.day:02d}/events-{date.strftime('%Y-%m-%d')}.jsonl"
    response = requests.get(url)
    return [json.loads(line) for line in response.text.split('\n') if line]

# Download last 7 days
events = []
for i in range(7):
    date = datetime.now() - timedelta(days=i)
    events.extend(download_events(date))

print(f"Downloaded {len(events)} events for training")
```

### Dashboard Team (Real-Time)

**Access Method:** Kafka Streaming

```python
# See examples/kafka_dashboard.py
# Run with: py -3 examples/kafka_dashboard.py
```

### DevOps Team (Monitoring)

**Access Method:** Monitoring Dashboard + Logs

```powershell
# Automated monitoring
.\scripts\monitor_pipeline.ps1

# Alerts (example: check for errors)
$errors = Get-Content logs\collector-$(Get-Date -Format 'yyyy-MM-dd').log | Select-String "ERROR"
if ($errors.Count -gt 10) {
    Write-Host "ALERT: High error count!" -ForegroundColor Red
}
```

---

## 🚦 Production Deployment

### Step 1: Verify Infrastructure

```powershell
# Check Kafka is running
Get-Process | Where-Object { $_.Name -like "*kafka*" }

# Check disk space (need ~2GB/month)
Get-PSDrive C

# Check network ports available
netstat -ano | findstr "8000 9092"
```

### Step 2: Start Pipeline

```powershell
# Start complete pipeline
.\scripts\start_pipeline.ps1
```

### Step 3: Validate Data Flow

Wait 2-3 minutes, then check:

```powershell
# Check events collected
$file = "data\raw\$(Get-Date -Format 'yyyy\\MM\\dd')\events-$(Get-Date -Format 'yyyy-MM-dd').jsonl"
Get-Content $file | Measure-Object -Line

# Should see 150+ events after first poll
```

### Step 4: Share Access URLs

**Send to team:**
- Kafka: `<your-ip>:9092` → Topic: `social-media-events`
- HTTP: `http://<your-ip>:8000/`
- Monitoring: SSH/RDP access to run `.\scripts\monitor_pipeline.ps1`

### Step 5: Monitor First 24 Hours

```powershell
# Watch logs continuously
Get-Content logs\collector-$(Get-Date -Format 'yyyy-MM-dd').log -Wait

# Check for any ERROR messages
Get-Content logs\collector-$(Get-Date -Format 'yyyy-MM-dd').log | Select-String "ERROR"
```

---

## 📊 Expected Results

### After 1 Hour
- ✅ ~9,000 events collected
- ✅ ~1.5 MB JSONL file
- ✅ 0-5% deduplication ratio
- ✅ All 15 subreddits covered

### After 24 Hours
- ✅ ~150,000 unique events (after dedup)
- ✅ ~30-50 MB JSONL file
- ✅ Diverse emotion-rich content across 7 categories
- ✅ Ready for Model Team labeling

### After 1 Week
- ✅ ~1,000,000 unique events
- ✅ ~200-350 MB total data
- ✅ Sufficient dataset for emotion model training
- ✅ Trend patterns visible for dashboard

---

## 🎓 Next Steps

1. **Start Pipeline:** `.\scripts\start_pipeline.ps1`
2. **Monitor First Hour:** Watch dashboard, verify data collection
3. **Share URLs:** Provide team access to Kafka & HTTP
4. **Model Team:** Begin emotion labeling after 24 hours
5. **Dashboard Team:** Build real-time visualizations using Kafka
6. **DevOps:** Set up automated alerts for errors/downtime

---

## 📚 Related Documentation

- `docs/KAFKA_REALTIME_GUIDE.md` - Kafka streaming setup
- `docs/TEAM_GUIDE.md` - Team access guide
- `examples/kafka_consumer_ml.py` - ML team consumer example
- `examples/kafka_dashboard.py` - Dashboard consumer example
- `PIPELINE_TEST_REPORT.md` - Pipeline validation results

---

**Questions or Issues?** Check logs in `logs/` directory or run `.\scripts\monitor_pipeline.ps1` for live status.
