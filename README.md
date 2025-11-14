# Social Media Trends & Emotion Analyzer - MLOps Pipeline

An automated data collection and processing pipeline for social media sentiment analysis with real-time streaming capabilities.

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PowerShell 5.1+ (Windows)
- Reddit API credentials (praw.ini)
- Kafka & Zookeeper (for streaming)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd MLops_temp
```

2. **Install Python dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure Reddit API credentials**
   - Create `praw.ini` in the root directory
   - Add your Reddit API credentials (see `praw.ini.example`)

4. **Configure the pipeline**
   - Edit `configs/config.yaml` to adjust subreddits, collection intervals, etc.

### Running the Pipeline

**Start everything with one command:**
```powershell
.\scripts\start_pipeline.ps1
```

This automatically starts:
- 📊 **Data Collector**: Polls Reddit every 60 seconds for new posts
- 🌊 **Kafka Producer**: Streams data in real-time
- 🌐 **HTTP Server**: Serves collected data files globally

**Monitor the pipeline:**
```powershell
.\scripts\monitor_pipeline.ps1
```

**Stop the pipeline:**
```powershell
Get-Job | Stop-Job
Get-Job | Remove-Job
```

## 📁 Project Structure

```
MLops_temp/
├── configs/              # Configuration files
│   └── config.yaml      # Main pipeline configuration
├── data/
│   ├── raw/             # Raw collected data (JSONL format)
│   └── processed/       # Preprocessed data
├── docs/                # Documentation
│   ├── AUTOMATED_PIPELINE.md      # Complete pipeline guide
│   ├── TEAM_ACCESS_GUIDE.md       # Remote access instructions
│   └── PIPELINE_ISSUE_RESOLVED.md # Troubleshooting history
├── logs/                # Application logs
├── scripts/             # Automation scripts
│   ├── start_pipeline.ps1         # Master orchestrator
│   ├── start_collector.ps1        # Auto-restart collector
│   ├── start_kafka_producer.ps1   # Kafka streaming
│   ├── start_http_server.ps1      # File server
│   └── monitor_pipeline.ps1       # Live dashboard
├── src/
│   ├── collector/       # Data collection modules
│   │   ├── connectors/  # Platform connectors (Reddit)
│   │   ├── preprocessing/ # Data cleaning & transformation
│   │   └── sinks/       # Data output (file, Kafka)
│   └── utils/           # Utility functions
├── .gitignore
├── README.md
└── requirements.txt
```

## 📊 Data Collection

**Current Configuration:**
- **15 diverse subreddits** across 7 categories:
  - Technology: r/technology, r/programming, r/artificial
  - Gaming: r/gaming, r/Games
  - News: r/worldnews, r/politics
  - Science: r/science, r/space
  - Entertainment: r/movies, r/television
  - Sports: r/sports, r/nba
  - General: r/AskReddit, r/todayilearned

- **Collection Rate**: 150 posts every 60 seconds (~9,000/hour)
- **Data Format**: JSONL (newline-delimited JSON)
- **Deduplication**: Reddit ID + SHA256 content hash
- **Timezone**: UTC

**Sample Event:**
```json
{
  "id": "abc123",
  "platform": "reddit",
  "text": "Post content here...",
  "collected_at": "2025-11-14T12:34:56Z",
  "metadata": {
    "subreddit": "technology",
    "author": "username",
    "score": 42,
    "num_comments": 15,
    "created_utc": 1699968896.0
  }
}
```

## 🌐 Team Access

Team members can access collected data remotely for EDA and dashboard development.

**HTTP Access (for batch analysis):**
```python
import requests, json, pandas as pd

# Replace with your data server IP
response = requests.get("http://<SERVER_IP>:8000/2025/11/14/events-2025-11-14.jsonl")
events = [json.loads(line) for line in response.text.split('\n') if line]
df = pd.DataFrame(events)
```

**Kafka Access (for real-time streaming):**
```python
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'social-media-events',
    bootstrap_servers='<SERVER_IP>:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    event = message.value
    # Process real-time event
```

See **[TEAM_QUICK_START.md](TEAM_QUICK_START.md)** for complete access instructions.

## 📖 Documentation

- **[AUTOMATED_PIPELINE.md](docs/AUTOMATED_PIPELINE.md)** - Complete pipeline usage guide
- **[TEAM_ACCESS_GUIDE.md](docs/TEAM_ACCESS_GUIDE.md)** - Remote access setup & examples
- **[TEAM_QUICK_START.md](TEAM_QUICK_START.md)** - Quick reference for team members
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command cheat sheet

## 🛠️ Features

- ✅ **Automated Data Collection**: Self-restarting collector with 999 retry attempts
- ✅ **Real-time Streaming**: Kafka producer for live dashboards
- ✅ **Global HTTP Access**: Share data files with team via HTTP server
- ✅ **Deduplication**: Intelligent duplicate detection (Reddit ID + content hash)
- ✅ **Preprocessing**: Automatic text cleaning and normalization
- ✅ **Health Monitoring**: Live dashboard showing collection metrics
- ✅ **Auto-Recovery**: Automatic restart on errors with exponential backoff
- ✅ **UTC Timezone**: Consistent timestamp handling across all components

## 📈 Performance

- **Collection Rate**: ~9,000 events/hour, ~150,000/day
- **Deduplication**: ~30% duplicate rate (varies by subreddit)
- **Uptime**: 24/7 automated operation with auto-restart
- **Storage**: ~1-2 MB per day (JSONL format)

## 🐛 Troubleshooting

**Pipeline not collecting data?**
```powershell
# Check job status
Get-Job | Format-Table

# View collector logs
Get-Content logs\collector-$(Get-Date -Format yyyy-MM-dd).log -Wait

# Restart pipeline
Get-Job | Stop-Job; Get-Job | Remove-Job
.\scripts\start_pipeline.ps1
```

**Can't access HTTP server remotely?**
- Check Windows Firewall allows port 8000 inbound
- Verify correct IP address (use `Get-NetIPAddress -AddressFamily IPv4`)
- Ensure both machines on same network

See **[docs/PIPELINE_ISSUE_RESOLVED.md](docs/PIPELINE_ISSUE_RESOLVED.md)** for detailed troubleshooting history.

## 🤝 Team Roles

- **Data Collection Lead**: Pipeline setup, data collection automation
- **Model Team**: Emotion labeling, model training on collected data
- **Dashboard Team**: Real-time visualization, trend analysis
- **DevOps Team**: Infrastructure monitoring, deployment automation

## 📝 Configuration

Edit `configs/config.yaml` to customize:
- Subreddits to monitor
- Collection interval (default: 60 seconds)
- Posts per subreddit (default: 10)
- Output format and sink type
- Kafka topic and settings

## ⚠️ Important Notes

1. **Never commit credentials**: `praw.ini` is excluded in `.gitignore`
2. **Data files excluded**: Large `.jsonl` files not pushed to git
3. **UTC timezone**: All timestamps and file dates use UTC (not local time)
4. **Reddit API limits**: 60 requests/minute - current config uses 15/minute

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- Reddit API via PRAW
- Apache Kafka for streaming
- PowerShell for automation

---

**Status**: ✅ Production-ready | 🚀 Actively collecting data
