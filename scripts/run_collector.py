import sys
import os
import time
import schedule
from datetime import datetime
from typing import List, Dict, Any
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collector.twitter_client import TwitterAPIClient
from data_collector.data_processor import TweetPreprocessor
from data_collector.database import PostgreSQLManager
from data_collector.kafka_producer import TweetKafkaProducer

from dotenv import load_dotenv

load_dotenv()


class TweetCollectionPipeline:
    """Main tweet collection and processing pipeline"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        
        self.twitter_client = TwitterAPIClient()
        self.preprocessor = TweetPreprocessor()
        self.db_manager = PostgreSQLManager()
        self.kafka_producer = TweetKafkaProducer()
        
        self._load_config()
        
        # Initialize database
        self.db_manager.create_tables()
        
        self.logger.info("Tweet collection pipeline initialized")
    
    def _setup_logger(self):
        """Setup logging configuration"""
        logger = logging.getLogger('TweetPipeline')
        logger.setLevel(getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File handler
        file_handler = logging.FileHandler('tweet_collection.log')
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        if not logger.handlers:
            logger.addHandler(console_handler)
            logger.addHandler(file_handler)
        
        return logger
    
    def _load_config(self):
        """Load configuration from environment variables"""
        collection_mode = os.getenv('HASHTAG_MODE', 'universal')
        
        if collection_mode == 'universal':
            from universal_hashtags import UniversalHashtagProvider
            provider = UniversalHashtagProvider()
            self.target_hashtags = provider.get_high_volume_hashtags()
            self.logger.info("Using universal high-volume hashtags")
        elif collection_mode == 'balanced':
            from universal_hashtags import UniversalHashtagProvider
            provider = UniversalHashtagProvider()
            balanced_set = provider.get_balanced_collection_set()
            self.target_hashtags = balanced_set['high_volume'] + balanced_set['diverse_domains']
            self.logger.info("Using balanced universal hashtags")
        else:
            hashtags_str = os.getenv('TARGET_HASHTAGS', '#AI,#MachineLearning,#DataScience')
            self.target_hashtags = [tag.strip() for tag in hashtags_str.split(',')]
            self.logger.info("Using custom hashtags from environment")
        
        self.tweets_per_collection = int(os.getenv('TWEETS_PER_COLLECTION', '200'))
        self.collection_interval = int(os.getenv('COLLECTION_INTERVAL_MINUTES', '10'))
        self.max_tweets_per_hashtag = int(os.getenv('MAX_TWEETS_PER_HASHTAG', '50'))
        
        self.logger.info(f"Configuration loaded:")
        self.logger.info(f"  Target hashtags: {self.target_hashtags[:5]}... ({len(self.target_hashtags)} total)")
        self.logger.info(f"  Tweets per collection: {self.tweets_per_collection}")
        self.logger.info(f"  Collection interval: {self.collection_interval} minutes")
    
    def collect_tweets_for_hashtag(self, hashtag: str) -> List[Dict[str, Any]]:
        """
        Collect tweets for a specific hashtag using Twitter API
        
        Args:
            hashtag: Hashtag to collect tweets for
            
        Returns:
            List of collected tweet dictionaries
        """
        self.logger.info(f"Starting Twitter API collection for hashtag: {hashtag}")
        
        try:
            # Use Twitter API client
            raw_tweets = self.twitter_client.search_hashtag_tweets(
                hashtag=hashtag,
                max_tweets=self.max_tweets_per_hashtag
            )
            
            if not raw_tweets:
                self.logger.warning(f"No tweets collected for {hashtag}")
                return []
            
            self.logger.info(f"Collected {len(raw_tweets)} tweets for {hashtag} via {raw_tweets[0].get('source', 'unknown')}")
            return raw_tweets
            
        except Exception as e:
            self.logger.error(f"Error collecting tweets for {hashtag}: {str(e)}")
            return []
    
    def process_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process raw tweets through the preprocessing pipeline
        
        Args:
            tweets: List of raw tweet dictionaries
            
        Returns:
            List of processed tweet dictionaries
        """
        if not tweets:
            return []
        
        self.logger.info(f"Processing {len(tweets)} tweets...")
        
        try:
            # Batch preprocess tweets
            processed_tweets = self.preprocessor.batch_preprocess(tweets)
            
            # Get processing statistics
            stats = self.preprocessor.get_processing_stats(processed_tweets)
            self.logger.info(f"Processing stats: {stats}")
            
            return processed_tweets
            
        except Exception as e:
            self.logger.error(f"Error processing tweets: {str(e)}")
            return tweets  # Return original tweets if processing fails
    
    def store_tweets(self, tweets: List[Dict[str, Any]]) -> int:
        """
        Store processed tweets in database and send to Kafka
        
        Args:
            tweets: List of processed tweet dictionaries
            
        Returns:
            Number of successfully stored tweets
        """
        if not tweets:
            return 0
        
        self.logger.info(f"Storing {len(tweets)} tweets...")
        
        stored_count = 0
        kafka_sent_count = 0
        
        for tweet in tweets:
            try:
                # Store in PostgreSQL
                if self.db_manager.store_tweet(tweet):
                    stored_count += 1
                
                # Send to Kafka
                if self.kafka_producer.send_processed_tweet(tweet):
                    kafka_sent_count += 1
                    
            except Exception as e:
                self.logger.error(f"Error storing tweet {tweet.get('id', 'unknown')}: {str(e)}")
        
        self.logger.info(f"Storage results: {stored_count}/{len(tweets)} stored in DB, {kafka_sent_count}/{len(tweets)} sent to Kafka")
        return stored_count
    
    def run_collection_cycle(self):
        """
        Run a complete collection cycle for all target hashtags
        """
        cycle_start = datetime.now()
        self.logger.info(f"=== Starting collection cycle at {cycle_start} ===")
        
        total_collected = 0
        total_processed = 0
        total_stored = 0
        
        for hashtag in self.target_hashtags:
            try:
                hashtag_start = time.time()
                
                # Collect tweets
                raw_tweets = self.collect_tweets_for_hashtag(hashtag)
                total_collected += len(raw_tweets)
                
                if raw_tweets:
                    # Process tweets
                    processed_tweets = self.process_tweets(raw_tweets)
                    total_processed += len(processed_tweets)
                    
                    # Store tweets
                    stored_count = self.store_tweets(processed_tweets)
                    total_stored += stored_count
                    
                    # Update hashtag statistics
                    self._update_hashtag_stats(hashtag)
                
                hashtag_duration = time.time() - hashtag_start
                self.logger.info(f"Completed {hashtag} in {hashtag_duration:.2f} seconds")
                
                # Small delay between hashtags
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"Error in collection cycle for {hashtag}: {str(e)}")
        
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        
        self.logger.info(f"=== Collection cycle completed in {cycle_duration:.2f} seconds ===")
        self.logger.info(f"Summary: {total_collected} collected, {total_processed} processed, {total_stored} stored")
        
        return {
            'collected': total_collected,
            'processed': total_processed,
            'stored': total_stored,
            'duration': cycle_duration
        }
    
    def _update_hashtag_stats(self, hashtag: str):
        """Update and cache hashtag statistics"""
        try:
            stats = self.db_manager.get_hashtag_statistics(hashtag)
            if stats:
                self.db_manager.cache_tweet_stats(hashtag, stats)
                self.logger.debug(f"Updated stats for {hashtag}")
        except Exception as e:
            self.logger.error(f"Error updating stats for {hashtag}: {str(e)}")
    
    def run_scheduled_collection(self):
        """
        Run scheduled collection every N minutes
        """
        self.logger.info(f"Starting scheduled collection every {self.collection_interval} minutes")
        
        # Schedule the collection
        schedule.every(self.collection_interval).minutes.do(self.run_collection_cycle)
        
        # Run initial collection
        self.run_collection_cycle()
        
        # Keep running scheduled collections
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Error in scheduled collection: {str(e)}")
                time.sleep(60)
        
        self._cleanup()
    
    def run_one_time_collection(self):
        """
        Run a one-time collection cycle
        """
        self.logger.info("Running one-time collection...")
        result = self.run_collection_cycle()
        self._cleanup()
        return result
    
    def _cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up resources...")
        
        try:
            self.kafka_producer.close()
        except:
            pass
        
        try:
            self.db_manager.close_connections()
        except:
            pass
        
        self.logger.info("Cleanup completed")
    
    def get_collection_summary(self) -> Dict[str, Any]:
        """Get overall collection summary"""
        try:
            summary = self.db_manager.get_collection_summary()
            return summary
        except Exception as e:
            self.logger.error(f"Error getting collection summary: {str(e)}")
            return {}


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Twitter Sentiment Data Collection Pipeline')
    parser.add_argument('--mode', choices=['scheduled', 'once'], default='scheduled',
                        help='Run mode: scheduled (continuous) or once (single run)')
    parser.add_argument('--hashtags', nargs='+', 
                        help='Override target hashtags')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = TweetCollectionPipeline()
    
    # Override hashtags if provided
    if args.hashtags:
        pipeline.target_hashtags = args.hashtags
        pipeline.logger.info(f"Using custom hashtags: {args.hashtags}")
    
    try:
        if args.mode == 'once':
            result = pipeline.run_one_time_collection()
            print(f"Collection completed: {result}")
        else:
            pipeline.run_scheduled_collection()
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
