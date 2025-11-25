# 📊 **Social Media Trends & Emotional Analysis MLOps Pipeline**

A complete MLOps pipeline for collecting Reddit posts, enriching them with emotion predictions, and serving the data via HTTP for downstream analytics and dashboard consumption.

## 🌟 **Features**

- **Real-time Data Collection**: Polls 15 Reddit subreddits for fresh posts every 60 seconds
- **Emotion Enrichment**: Integrates with AWS Lambda for emotion prediction (6 emotions: joy, sadness, anger, fear, love, unknown)
- **Deduplication**: Persistent deduplication using post IDs and content hashing
- **Data Storage**: JSONL format with date-based partitioning
- **HTTP API**: RESTful server for data access (port 8000)
- **Monitoring Dashboard**: Live pipeline health monitoring
- **Production Ready**: Automated job management, error handling, logging

## 🏗️ **Architecture**

```
Reddit API → Collector → Emotion API → Deduplication → File Sink → HTTP Server
     ↓           ↓           ↓           ↓           ↓           ↓
  Raw Posts   Clean Text   Predictions   Unique IDs   JSONL Files   REST API
```

### **Components**
- **reddit_poll.py**: Main data collection logic
- **dedup.py**: Persistent deduplication
- **`src/common/sinks/file_sink.py`**: JSONL file storage
- **start_pipeline.ps1**: Pipeline orchestrator
- **monitor_pipeline.ps1**: Live monitoring dashboard
- **config.yaml**: Configuration management

## 📋 **Prerequisites**

- **Python 3.8+**
- **PowerShell 5.1+** (Windows)
- **Reddit API Credentials** (Client ID, Secret, User Agent)
- **AWS Lambda** (for emotion prediction API)
- **Git** (for version control)

## 🚀 **Installation**

### **1. Clone Repository**
```bash
git clone https://github.com/yourusername/social-media-emotion-mlops.git
cd social-media-emotion-mlops
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Environment Setup**
Create .env file:
```env
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=mlops-reddit-collector/1.0
```

### **4. Configure Pipeline**
Edit config.yaml:
```yaml
sources:
  reddit:
    enabled: true
    subreddits: ["news", "technology", "politics", "science", "AskReddit"]
    poll_interval_sec: 60
    limit_per_call: 10

stream:
  sink: file

sinks:
  file:
    root_dir: data/raw
    filename_pattern: events-{date}.jsonl
```

## ⚙️ **Configuration**

### **Reddit Settings**
- **Subreddits**: List of 15 subreddits to monitor
- **Poll Interval**: 60 seconds between collections
- **Limit per Call**: 10 posts per subreddit per poll

### **Emotion API**
- **Endpoint**: AWS Lambda function URL
- **Input**: `{"text": "post content"}`
- **Output**: Emotion predictions with confidence scores

### **Data Storage**
- **Format**: JSONL (one JSON object per line)
- **Partitioning**: Date-based directories (`data/raw/YYYY/MM/DD/`)
- **Fields**: id, text, raw_text, timestamp, platform, engagement, lang, meta, emotion_prediction

## 📖 **Usage**

### **Start Pipeline**
```powershell
.\scripts\start_pipeline.ps1
```

**Output:**
```
================================================================
         AUTOMATED DATA PIPELINE - STARTING
================================================================

-- Cleaning up existing jobs...
   Stopped 2 existing job(s)

-- Starting Reddit Data Collector...
   Status: STARTED (Job ID: 35)
   Logs:   logs\collector-2025-11-25.log

-- Starting HTTP Data Server...
   Status: STARTED (Job ID: 37)
   Port:   8000
   URL:    http://localhost:8000/
   Network: http://192.168.1.100:8000/

================================================================
         PIPELINE STARTED SUCCESSFULLY
================================================================
```

### **Monitor Pipeline**
```powershell
.\scripts\monitor_pipeline.ps1
```

**Dashboard:**
```
================================================================
     AUTOMATED PIPELINE MONITORING DASHBOARD                   
================================================================

-- REDDIT DATA COLLECTOR [RUNNING]
   Events Today:      150
   File Size:         0.25 MB
   Last Update:       14:30:25
   Collection Rate:   2.5 events/min
   Subreddits:        15
   Errors Today:      0

-- HTTP DATA SERVER [RUNNING]
   Requests Today:    0
   Port:              8000
   URL:               http://localhost:8000/
   Network:           http://192.168.1.100:8000/

Pipeline Status: ALL SYSTEMS OPERATIONAL
```

### **Stop Pipeline**
```powershell
Get-Job | Stop-Job; Get-Job | Remove-Job
```

## 🌐 **API Endpoints**

### **Data Access**
- **Base URL**: `http://localhost:8000/`
- **Daily Data**: `http://localhost:8000/YYYY/MM/DD/events-YYYY-MM-DD.jsonl`
- **Example**: `http://localhost:8000/2025/11/25/events-2025-11-25.jsonl`

### **Sample Response**
```json
{
  "id": "1p6kn40",
  "text": "what is the coolest idea you ever had?",
  "raw_text": "What is the coolest idea you ever had?",
  "timestamp": "2025-11-25T18:42:52+00:00",
  "platform": "reddit",
  "engagement": {"score": 1, "num_comments": 0},
  "lang": "en",
  "meta": {"subreddit": "AskReddit", "submission_id": "1p6kn40"},
  "emotion_prediction": {
    "label": "joy",
    "score": 0.998,
    "raw_scores": {"joy": 0.998, "sadness": 0.001, "anger": 0.0007, "fear": 0.0003, "love": 0.00009, "unknown": 0.00035}
  }
}
```

## 📊 **Data Schema**

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Reddit submission ID |
| `text` | string | Cleaned, processed text |
| `raw_text` | string | Original post title |
| `timestamp` | ISO string | UTC timestamp |
| `platform` | string | "reddit" |
| `engagement` | object | Score and comment count |
| `lang` | string | Language code ("en") |
| `meta` | object | Subreddit, query, submission_id |
| `emotion_prediction` | object | ML model predictions |

## 🔧 **Development**

### **Run Collector Manually**
```bash
python -m src.collector.connectors.reddit_poll --config configs/config.yaml
```

### **Test Deduplication**
```python
from src.common.preprocess.dedup import Deduplicator
dedup = Deduplicator()
print(dedup.is_duplicate({"id": "test123", "text": "sample text"}))
```

### **View Logs**
```powershell
Get-Content logs\collector-2025-11-25.log -Wait
```

## 📈 **Monitoring & Metrics**

### **Key Metrics**
- **Collection Rate**: Posts collected per minute
- **Deduplication Rate**: Percentage of duplicates removed
- **File Size**: Daily data volume
- **Error Count**: Failed API calls or processing errors

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.
