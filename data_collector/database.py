import psycopg2
from psycopg2.extras import RealDictCursor, Json
import redis
import os
from dotenv import load_dotenv
import json
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

load_dotenv()

class PostgreSQLManager:
    """PostgreSQL database manager for tweet storage and analytics"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self._setup_connections()
    
    def _setup_logger(self):
        logger = logging.getLogger('PostgreSQLManager')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger
    
    def _setup_connections(self):
        """Setup database connections"""
        try:
            self.pg_connection = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=os.getenv('POSTGRES_PORT', '5432'),
                database=os.getenv('POSTGRES_DB', 'twitter_sentiment'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', 'password')
            )
            self.pg_connection.autocommit = True
            self.logger.info("PostgreSQL connection established")
        except Exception as e:
            self.logger.error(f"PostgreSQL connection failed: {str(e)}")
            raise
        
        # Redis for caching
        try:
            self.redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                decode_responses=True
            )
            # Test Redis connection
            self.redis_client.ping()
            self.logger.info("Redis connection established")
        except Exception as e:
            self.logger.warning(f"Redis connection failed: {str(e)}. Continuing without caching.")
            self.redis_client = None
    
    def create_tables(self):
        """Create database tables if they don't exist"""
        try:
            cursor = self.pg_connection.cursor()
            
            # Create tweets table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tweets (
                    id BIGINT PRIMARY KEY,
                    original_text TEXT NOT NULL,
                    cleaned_text TEXT,
                    ml_text TEXT,
                    created_at TIMESTAMP NOT NULL,
                    author_id BIGINT,
                    author_username VARCHAR(255),
                    retweet_count INTEGER DEFAULT 0,
                    like_count INTEGER DEFAULT 0,
                    reply_count INTEGER DEFAULT 0,
                    quote_count INTEGER DEFAULT 0,
                    char_count INTEGER,
                    word_count INTEGER,
                    hashtag_count INTEGER DEFAULT 0,
                    mention_count INTEGER DEFAULT 0,
                    url_count INTEGER DEFAULT 0,
                    token_count INTEGER,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    processed BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create hashtags table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hashtags (
                    id SERIAL PRIMARY KEY,
                    hashtag VARCHAR(255) UNIQUE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create tweet_hashtags junction table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tweet_hashtags (
                    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
                    hashtag_id INTEGER REFERENCES hashtags(id) ON DELETE CASCADE,
                    PRIMARY KEY (tweet_id, hashtag_id)
                )
            """)
            
            # Create mentions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mentions (
                    id SERIAL PRIMARY KEY,
                    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
                    username VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create urls table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS urls (
                    id SERIAL PRIMARY KEY,
                    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
                    url TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create sentiment_predictions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_predictions (
                    id SERIAL PRIMARY KEY,
                    tweet_id BIGINT REFERENCES tweets(id) ON DELETE CASCADE,
                    sentiment VARCHAR(50) NOT NULL,
                    confidence FLOAT NOT NULL,
                    model_version VARCHAR(100),
                    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tweet_id)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_created_at ON tweets(created_at)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweets_processed ON tweets(processed)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tweet_hashtags_hashtag_id ON tweet_hashtags(hashtag_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_predictions_tweet_id ON sentiment_predictions(tweet_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_hashtags_hashtag ON hashtags(hashtag)")
            
            cursor.close()
            self.logger.info("Database tables created successfully")
            
        except Exception as e:
            self.logger.error(f"Error creating tables: {str(e)}")
            raise
    
    def store_tweet(self, tweet_data: Dict[str, Any]) -> bool:
        """
        Store tweet in PostgreSQL with proper normalization
        
        Args:
            tweet_data: Tweet data dictionary
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            cursor = self.pg_connection.cursor()
            
            # Check if tweet already exists
            cursor.execute("SELECT id FROM tweets WHERE id = %s", (tweet_data['id'],))
            if cursor.fetchone():
                self.logger.debug(f"Tweet {tweet_data['id']} already exists")
                cursor.close()
                return False
            
            # Parse datetime if it's a string
            created_at = tweet_data.get('created_at')
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = datetime.now()
            
            processed_at = tweet_data.get('processed_at')
            if isinstance(processed_at, str):
                try:
                    processed_at = datetime.fromisoformat(processed_at.replace('Z', '+00:00'))
                except:
                    processed_at = None
            
            # Extract public metrics safely
            public_metrics = tweet_data.get('public_metrics', {})
            
            # Insert main tweet data
            insert_tweet_query = """
                INSERT INTO tweets (
                    id, original_text, cleaned_text, ml_text, created_at, author_id, author_username,
                    retweet_count, like_count, reply_count, quote_count,
                    char_count, word_count, hashtag_count, mention_count, url_count, token_count,
                    processed_at, processed
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_tweet_query, (
                tweet_data['id'],
                tweet_data.get('original_text', tweet_data.get('text', '')),
                tweet_data.get('cleaned_text', ''),
                tweet_data.get('ml_text', ''),
                created_at,
                tweet_data.get('author_id'),
                tweet_data.get('author_username'),
                public_metrics.get('retweet_count', 0),
                public_metrics.get('like_count', 0),
                public_metrics.get('reply_count', 0),
                public_metrics.get('quote_count', 0),
                tweet_data.get('char_count', 0),
                tweet_data.get('word_count', 0),
                tweet_data.get('hashtag_count', 0),
                tweet_data.get('mention_count', 0),
                tweet_data.get('url_count', 0),
                tweet_data.get('token_count', 0),
                processed_at,
                tweet_data.get('processed', True)
            ))
            
            # Store hashtags
            hashtags = tweet_data.get('hashtags', [])
            if hashtags:
                self._store_hashtags(cursor, tweet_data['id'], hashtags)
            
            # Store mentions
            mentions = tweet_data.get('mentions', [])
            if mentions:
                self._store_mentions(cursor, tweet_data['id'], mentions)
            
            # Store URLs
            urls = tweet_data.get('urls', [])
            if urls:
                self._store_urls(cursor, tweet_data['id'], urls)
            
            cursor.close()
            self.logger.debug(f"Stored tweet {tweet_data['id']} in PostgreSQL")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing tweet: {str(e)}")
            return False
    
    def _store_hashtags(self, cursor, tweet_id: int, hashtags: List[str]):
        """Store hashtags with proper normalization"""
        for hashtag in hashtags:
            # Clean hashtag
            hashtag = hashtag.lower().replace('#', '')
            
            # Insert or get hashtag ID
            cursor.execute(
                "INSERT INTO hashtags (hashtag) VALUES (%s) ON CONFLICT (hashtag) DO NOTHING",
                (hashtag,)
            )
            
            cursor.execute("SELECT id FROM hashtags WHERE hashtag = %s", (hashtag,))
            result = cursor.fetchone()
            if result:
                hashtag_id = result[0]
                
                # Link tweet to hashtag
                cursor.execute(
                    "INSERT INTO tweet_hashtags (tweet_id, hashtag_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                    (tweet_id, hashtag_id)
                )
    
    def _store_mentions(self, cursor, tweet_id: int, mentions: List[str]):
        """Store user mentions"""
        for mention in mentions:
            mention = mention.replace('@', '').lower()
            cursor.execute(
                "INSERT INTO mentions (tweet_id, username) VALUES (%s, %s)",
                (tweet_id, mention)
            )
    
    def _store_urls(self, cursor, tweet_id: int, urls: List[str]):
        """Store URLs"""
        for url in urls:
            cursor.execute(
                "INSERT INTO urls (tweet_id, url) VALUES (%s, %s)",
                (tweet_id, url)
            )
    
    def get_tweets_by_hashtag(self, hashtag: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tweets by hashtag"""
        try:
            cursor = self.pg_connection.cursor(cursor_factory=RealDictCursor)
            
            query = """
                SELECT t.*, h.hashtag, sp.sentiment, sp.confidence
                FROM tweets t
                JOIN tweet_hashtags th ON t.id = th.tweet_id
                JOIN hashtags h ON th.hashtag_id = h.id
                LEFT JOIN sentiment_predictions sp ON t.id = sp.tweet_id
                WHERE h.hashtag = %s
                ORDER BY t.created_at DESC
                LIMIT %s
            """
            
            cursor.execute(query, (hashtag.lower().replace('#', ''), limit))
            tweets = [dict(row) for row in cursor.fetchall()]
            cursor.close()
            
            return tweets
            
        except Exception as e:
            self.logger.error(f"Error fetching tweets by hashtag: {str(e)}")
            return []
    
    def get_hashtag_statistics(self, hashtag: str) -> Dict[str, Any]:
        """Get comprehensive hashtag statistics"""
        try:
            cursor = self.pg_connection.cursor(cursor_factory=RealDictCursor)
            
            # Basic stats
            stats_query = """
                SELECT 
                    COUNT(DISTINCT t.id) as total_tweets,
                    AVG(t.retweet_count) as avg_retweets,
                    AVG(t.like_count) as avg_likes,
                    AVG(t.char_count) as avg_char_count,
                    MAX(t.created_at) as latest_tweet,
                    MIN(t.created_at) as earliest_tweet
                FROM tweets t
                JOIN tweet_hashtags th ON t.id = th.tweet_id
                JOIN hashtags h ON th.hashtag_id = h.id
                WHERE h.hashtag = %s
            """
            
            cursor.execute(stats_query, (hashtag.lower().replace('#', ''),))
            basic_stats = dict(cursor.fetchone() or {})
            
            # Sentiment distribution
            sentiment_query = """
                SELECT 
                    sp.sentiment,
                    COUNT(*) as count,
                    AVG(sp.confidence) as avg_confidence
                FROM sentiment_predictions sp
                JOIN tweets t ON sp.tweet_id = t.id
                JOIN tweet_hashtags th ON t.id = th.tweet_id
                JOIN hashtags h ON th.hashtag_id = h.id
                WHERE h.hashtag = %s
                GROUP BY sp.sentiment
            """
            
            cursor.execute(sentiment_query, (hashtag.lower().replace('#', ''),))
            sentiment_dist = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            
            stats = {
                'hashtag': hashtag,
                'basic_stats': basic_stats,
                'sentiment_distribution': sentiment_dist,
                'timestamp': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting hashtag statistics: {str(e)}")
            return {}
    
    def cache_tweet_stats(self, hashtag: str, stats: Dict[str, Any]):
        """Cache tweet statistics in Redis"""
        if not self.redis_client:
            return
            
        try:
            key = f"hashtag_stats:{hashtag.lower()}"
            self.redis_client.setex(key, 300, json.dumps(stats, default=str))  # 5 minute expiry
            self.logger.debug(f"Cached stats for hashtag {hashtag}")
        except Exception as e:
            self.logger.error(f"Error caching stats: {str(e)}")
    
    def get_cached_stats(self, hashtag: str) -> Dict[str, Any]:
        """Get cached statistics from Redis"""
        if not self.redis_client:
            return {}
            
        try:
            key = f"hashtag_stats:{hashtag.lower()}"
            cached_data = self.redis_client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return {}
        except Exception as e:
            self.logger.error(f"Error getting cached stats: {str(e)}")
            return {}
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """Get overall collection summary"""
        try:
            cursor = self.pg_connection.cursor(cursor_factory=RealDictCursor)
            
            # Overall stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_tweets,
                    COUNT(DISTINCT author_id) as unique_authors,
                    AVG(char_count) as avg_char_count,
                    AVG(hashtag_count) as avg_hashtags_per_tweet,
                    MAX(created_at) as latest_tweet,
                    MIN(created_at) as earliest_tweet
                FROM tweets
            """)
            overall_stats = dict(cursor.fetchone() or {})
            
            # Top hashtags
            cursor.execute("""
                SELECT h.hashtag, COUNT(*) as tweet_count
                FROM hashtags h
                JOIN tweet_hashtags th ON h.id = th.hashtag_id
                GROUP BY h.hashtag
                ORDER BY tweet_count DESC
                LIMIT 10
            """)
            top_hashtags = [dict(row) for row in cursor.fetchall()]
            
            cursor.close()
            
            return {
                'overall_stats': overall_stats,
                'top_hashtags': top_hashtags,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting collection summary: {str(e)}")
            return {}
    
    def close_connections(self):
        """Close database connections"""
        try:
            if hasattr(self, 'pg_connection'):
                self.pg_connection.close()
                self.logger.info("PostgreSQL connection closed")
        except:
            pass
        
        try:
            if hasattr(self, 'redis_client') and self.redis_client:
                self.redis_client.close()
                self.logger.info("Redis connection closed")
        except:
            pass


# Example usage and testing
if __name__ == "__main__":
    # Test database manager
    db = PostgreSQLManager()
    
    # Create tables
    db.create_tables()
    
    # Test tweet storage
    sample_tweet = {
        'id': 123456789,
        'text': 'Test tweet about #AI and #MachineLearning',
        'original_text': 'Test tweet about #AI and #MachineLearning',
        'cleaned_text': 'test tweet about ai and machine learning',
        'created_at': datetime.now().isoformat(),
        'author_id': 987654321,
        'author_username': 'testuser',
        'public_metrics': {
            'retweet_count': 5,
            'like_count': 10,
            'reply_count': 2,
            'quote_count': 1
        },
        'hashtags': ['#ai', '#machinelearning'],
        'mentions': [],
        'urls': [],
        'char_count': 45,
        'word_count': 8,
        'hashtag_count': 2,
        'mention_count': 0,
        'url_count': 0
    }
    
    success = db.store_tweet(sample_tweet)
    print(f"Tweet storage: {'Success' if success else 'Failed'}")
    
    # Get summary
    summary = db.get_collection_summary()
    print(f"Collection summary: {summary}")
    
    # Close connections
    db.close_connections()
