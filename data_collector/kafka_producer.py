from kafka import KafkaProducer
import json
import os
from dotenv import load_dotenv
import logging
from typing import Dict, Any

load_dotenv()

class TweetKafkaProducer:
    """Kafka producer for streaming tweet data"""
    
    def __init__(self):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.logger = self._setup_logger()
        self._setup_producer()
    
    def _setup_logger(self):
        logger = logging.getLogger('KafkaProducer')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger
    
    def _setup_producer(self):
        """Setup Kafka producer with error handling"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(','),
                value_serializer=lambda x: json.dumps(x, default=str).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None,
                acks='all',
                retries=3,
                retry_backoff_ms=100,
                request_timeout_ms=30000,
                max_in_flight_requests_per_connection=1  # Ensure ordering
            )
            self.logger.info(f"Kafka producer initialized with servers: {self.bootstrap_servers}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Kafka producer: {str(e)}")
            self.producer = None
    
    def send_tweet(self, tweet_data: Dict[str, Any], topic: str = 'raw_tweets') -> bool:
        """
        Send tweet data to Kafka topic
        
        Args:
            tweet_data: Tweet data dictionary
            topic: Kafka topic name
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.producer:
            self.logger.error("Kafka producer not available")
            return False
        
        try:
            key = str(tweet_data.get('id', ''))
            
            # Send to Kafka
            future = self.producer.send(topic, key=key, value=tweet_data)
            
            # Wait for the message to be sent (with timeout)
            record_metadata = future.get(timeout=10)
            
            self.logger.debug(f"Sent tweet {key} to topic {topic} (partition {record_metadata.partition}, offset {record_metadata.offset})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending tweet to Kafka: {str(e)}")
            return False
    
    def send_processed_tweet(self, tweet_data: Dict[str, Any], topic: str = 'processed_tweets') -> bool:
        """
        Send processed tweet data to Kafka topic
        
        Args:
            tweet_data: Processed tweet data dictionary
            topic: Kafka topic name
            
        Returns:
            True if sent successfully, False otherwise
        """
        return self.send_tweet(tweet_data, topic)
    
    def send_batch_tweets(self, tweets: list, topic: str = 'raw_tweets') -> int:
        """
        Send multiple tweets in batch
        
        Args:
            tweets: List of tweet dictionaries
            topic: Kafka topic name
            
        Returns:
            Number of successfully sent tweets
        """
        if not self.producer:
            self.logger.error("Kafka producer not available")
            return 0
        
        success_count = 0
        
        for tweet in tweets:
            if self.send_tweet(tweet, topic):
                success_count += 1
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        
        self.logger.info(f"Successfully sent {success_count}/{len(tweets)} tweets to {topic}")
        return success_count
    
    def close(self):
        """Close the producer"""
        if self.producer:
            try:
                self.producer.flush()  # Ensure all messages are sent
                self.producer.close()
                self.logger.info("Kafka producer closed")
            except Exception as e:
                self.logger.error(f"Error closing Kafka producer: {str(e)}")


class TweetKafkaConsumer:
    """
    Kafka consumer for receiving tweet data
    (For use by other team members)
    """
    
    def __init__(self, group_id: str = 'tweet_consumers'):
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
        self.group_id = group_id
        self.logger = self._setup_logger()
        self._setup_consumer()
    
    def _setup_logger(self):
        logger = logging.getLogger('KafkaConsumer')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        return logger
    
    def _setup_consumer(self):
        """Setup Kafka consumer"""
        try:
            from kafka import KafkaConsumer
            
            self.consumer = KafkaConsumer(
                bootstrap_servers=self.bootstrap_servers.split(','),
                group_id=self.group_id,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                key_deserializer=lambda x: x.decode('utf-8') if x else None,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                auto_commit_interval_ms=1000
            )
            self.logger.info(f"Kafka consumer initialized with group_id: {self.group_id}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Kafka consumer: {str(e)}")
            self.consumer = None
    
    def subscribe_to_topics(self, topics: list):
        """Subscribe to Kafka topics"""
        if not self.consumer:
            self.logger.error("Kafka consumer not available")
            return
        
        try:
            self.consumer.subscribe(topics)
            self.logger.info(f"Subscribed to topics: {topics}")
        except Exception as e:
            self.logger.error(f"Error subscribing to topics: {str(e)}")
    
    def consume_tweets(self, timeout_ms: int = 1000):
        """
        Consume tweets from subscribed topics
        
        Args:
            timeout_ms: Timeout for polling messages
            
        Yields:
            Tweet data dictionaries
        """
        if not self.consumer:
            self.logger.error("Kafka consumer not available")
            return
        
        try:
            for message in self.consumer:
                yield {
                    'topic': message.topic,
                    'partition': message.partition,
                    'offset': message.offset,
                    'key': message.key,
                    'value': message.value,
                    'timestamp': message.timestamp
                }
        except Exception as e:
            self.logger.error(f"Error consuming messages: {str(e)}")
    
    def close(self):
        """Close the consumer"""
        if self.consumer:
            try:
                self.consumer.close()
                self.logger.info("Kafka consumer closed")
            except Exception as e:
                self.logger.error(f"Error closing Kafka consumer: {str(e)}")


# Example usage and testing
if __name__ == "__main__":
    # Test Kafka producer
    producer = TweetKafkaProducer()
    
    # Sample tweet data
    sample_tweet = {
        'id': 123456789,
        'text': 'Test tweet about #AI',
        'created_at': '2023-10-27T10:00:00Z',
        'author_id': 987654321,
        'hashtags': ['#ai'],
        'mentions': [],
        'urls': []
    }
    
    # Send tweet
    success = producer.send_tweet(sample_tweet, 'test_tweets')
    print(f"Tweet sent: {'Success' if success else 'Failed'}")
    
    # Close producer
    producer.close()
    
    # Test consumer (commented out for now)
    # consumer = TweetKafkaConsumer('test_group')
    # consumer.subscribe_to_topics(['test_tweets'])
    # 
    # print("Consuming messages...")
    # for message in consumer.consume_tweets():
    #     print(f"Received: {message}")
    #     break  # Just test one message
    # 
    # consumer.close()
