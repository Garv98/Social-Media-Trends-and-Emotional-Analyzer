# Twitter Sentiment Data Collection Pipeline

A real-time data streaming pipeline that collects Twitter data, processes it through Kafka, and stores it in PostgreSQL for sentiment analysis.

## 🏗️ Architecture Overview

```
Twitter API → Data Collector → Kafka → PostgreSQL + Redis
                    ↓
              EDA Dashboard ← Data Quality Monitor
```

**Data Flow:**
1. **Data Collector** fetches tweets from Twitter API based on trending hashtags
2. **Kafka Streaming** processes tweets in real-time through message queues
3. **PostgreSQL Storage** stores processed tweets with sentiment analysis
4. **Redis Caching** provides fast access to frequently queried data
5. **Monitoring & Analytics** generates quality reports and EDA dashboards

## 🛠️ Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

### 2. Set Up the Environment
- Create a virtual environment:
  ```bash
  python -m venv .venv
  ```
- Activate the virtual environment:
  - **Windows**: `\.venv\Scripts\activate`
  - **Linux/Mac**: `source .venv/bin/activate`
- Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

### 3. Configure Environment Variables
- Copy `.env.example` to `.env`:
  ```bash
  cp .env.example .env
  ```
- Update `.env` with your Twitter API credentials and database settings.

#### Example `.env` Configuration
```env
# Twitter API Configuration
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=twitter_sentiment
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Application Settings
HASHTAG_MODE=universal
TARGET_HASHTAGS=
TWEETS_PER_COLLECTION=500
COLLECTION_INTERVAL_MINUTES=15
MAX_TWEETS_PER_HASHTAG=50

# Logging
LOG_LEVEL=INFO
```

### 4. Start Docker Services
- Ensure Docker is installed and running.
- Start PostgreSQL, Redis, and Kafka services:
  ```bash
  docker-compose up -d
  ```

#### Verifying Services
- PostgreSQL: Access via `psql` or a database client at `localhost:5433`.
- Redis: Test connection using `redis-cli`.
- Kafka: Verify using `kafka-topics.sh`.

**Note**: When you start the services for the first time, Docker will:
- Create a fresh PostgreSQL database named `twitter_sentiment`
- Automatically initialize the database schema using `database/init.sql`
- Start with an empty database (no existing tweet data)
- Each team member gets their own independent database instance

**Data Streaming**: Once you run the data collector, it will:
- Connect to Twitter API and fetch real-time tweets
- Stream data through Kafka for real-time processing
- Store processed tweets in your PostgreSQL database
- Your database will gradually fill with collected tweet data

---

## 🚀 How to Run the Project

### 1. Initialize the Database
**Note**: This step is optional if you're using Docker, as the database schema is automatically created when the PostgreSQL container starts. Run this only if you're using a local PostgreSQL installation.

```bash
python scripts/init_db.py
```

### 2. Run the Data Collector
This starts the real-time tweet collection and streaming pipeline:
```bash
python scripts/run_collector.py
```

**What happens:**
- Connects to Twitter API using your bearer token
- Fetches tweets based on trending hashtags (universal mode)
- Streams tweets through Kafka for real-time processing
- Stores processed tweets with sentiment analysis in PostgreSQL
- Runs continuously, collecting new data every 15 minutes (configurable)

### 3. Monitor Data Quality
```bash
python scripts/data_quality_monitor.py
```

### 4. Generate EDA Dashboard
After collecting data for some time, generate analytics dashboard:
```bash
python scripts/eda_dashboard_generator.py
```

**Note**: This requires actual tweet data in the database. Let the collector run for at least 30-60 minutes before generating meaningful dashboards.

---

## 📂 Folder Structure
```
MLOps/
├── data_collector/         # Core data collection modules
│   ├── twitter_client.py   # Twitter API integration
│   ├── data_processor.py   # Data preprocessing logic
│   ├── database.py         # PostgreSQL and Redis management
│   ├── kafka_producer.py   # Kafka producer for streaming
├── scripts/                # Utility scripts
│   ├── init_db.py          # Database initialization
│   ├── run_collector.py    # Main data collection script
│   ├── data_quality_monitor.py # Data quality checks
│   ├── eda_dashboard_generator.py # EDA dashboard generation
├── tests/                  # Unit tests
├── .env                    # Environment variables
├── docker-compose.yml      # Docker services configuration
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

---

## 🔧 Environment Variables
The `.env` file contains the following variables:
```env
# Twitter API Configuration
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=twitter_sentiment
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Application Settings
HASHTAG_MODE=universal
TARGET_HASHTAGS=
TWEETS_PER_COLLECTION=500
COLLECTION_INTERVAL_MINUTES=15
MAX_TWEETS_PER_HASHTAG=50

# Logging
LOG_LEVEL=INFO
```

---

## 🧪 Testing
Run unit tests to ensure everything is working:
```bash
pytest tests/
```

---

## 🔧 Troubleshooting

### Package Installation Issues (Windows)
If you encounter build errors when installing requirements (especially for `pandas` or `psycopg2-binary`):

1. **Install Microsoft Visual C++ Build Tools**:
   - Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Or install Visual Studio with C++ development tools

2. **Alternative: Use pre-compiled wheels**:
   ```bash
   pip install --only-binary=all -r requirements.txt
   ```

3. **Use conda instead of pip** (if you have Anaconda/Miniconda):
   ```bash
   conda env create -f environment.yml
   ```

### Database Connection Issues
- Ensure Docker is running and containers are started
- Check if port 5433 is available (not used by other applications)
- Verify `.env` file has correct database credentials

### Service Access
- PostgreSQL Admin UI: http://localhost:8080 (Adminer)
- Kafka UI: http://localhost:8090
- Database: localhost:5433
- Redis: localhost:6379